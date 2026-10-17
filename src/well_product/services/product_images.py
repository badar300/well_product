from __future__ import annotations

import shutil
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from well_product.models import ProductImage
from well_product.paths import (
    ALLOWED_IMAGE_SUFFIXES,
    ensure_media_dirs,
    product_media_dir,
    relative_media_path,
    resolve_media_path,
)
from well_product.units import ProductImageKind


class InvalidImageError(ValueError):
    pass


def validate_image_source(source: Path) -> Path:
    path = source.expanduser().resolve()
    if not path.is_file():
        raise InvalidImageError(f"File not found: {source}")
    suffix = path.suffix.lower()
    if suffix not in ALLOWED_IMAGE_SUFFIXES:
        raise InvalidImageError(
            f"Unsupported image type '{suffix}'. "
            f"Use: {', '.join(sorted(ALLOWED_IMAGE_SUFFIXES))}"
        )
    return path


def list_images(session: Session, product_id: int) -> list[ProductImage]:
    return list(
        session.scalars(
            select(ProductImage)
            .where(ProductImage.product_id == product_id)
            .order_by(ProductImage.kind, ProductImage.sort_order, ProductImage.id)
        ).all()
    )


def get_slot_image(
    session: Session, product_id: int, kind: ProductImageKind
) -> ProductImage | None:
    if kind == ProductImageKind.EXTRA:
        return None
    return session.scalar(
        select(ProductImage).where(
            ProductImage.product_id == product_id,
            ProductImage.kind == kind.value,
        )
    )


def resolve_absolute(relative_path: str) -> Path:
    return resolve_media_path(relative_path)


def _delete_file_if_exists(relative_path: str) -> None:
    path = resolve_media_path(relative_path)
    if path.is_file():
        path.unlink()


def _copy_to_product_dir(
    product_id: int,
    source: Path,
    dest_stem: str,
) -> str:
    dest_dir = ensure_media_dirs(product_id)
    dest_file = dest_dir / f"{dest_stem}{source.suffix.lower()}"
    shutil.copy2(source, dest_file)
    return relative_media_path(dest_file)


def set_slot_image(
    session: Session,
    product_id: int,
    kind: ProductImageKind,
    source_path: Path,
) -> ProductImage:
    if kind == ProductImageKind.EXTRA:
        raise ValueError("Use add_extra_image for extra photos")
    source = validate_image_source(source_path)
    existing = get_slot_image(session, product_id, kind)
    if existing is not None:
        _delete_file_if_exists(existing.relative_path)
        session.delete(existing)
        session.flush()
    relative = _copy_to_product_dir(product_id, source, kind.value)
    row = ProductImage(
        product_id=product_id,
        kind=kind.value,
        relative_path=relative,
        sort_order=0,
    )
    session.add(row)
    session.flush()
    return row


def add_extra_image(
    session: Session,
    product_id: int,
    source_path: Path,
) -> ProductImage:
    source = validate_image_source(source_path)
    extras = [
        img
        for img in list_images(session, product_id)
        if img.kind == ProductImageKind.EXTRA.value
    ]
    sort_order = len(extras) + 1
    relative = _copy_to_product_dir(product_id, source, f"extra_{sort_order}")
    row = ProductImage(
        product_id=product_id,
        kind=ProductImageKind.EXTRA.value,
        relative_path=relative,
        sort_order=sort_order,
    )
    session.add(row)
    session.flush()
    return row


def remove_image(session: Session, image: ProductImage) -> None:
    _delete_file_if_exists(image.relative_path)
    session.delete(image)


def clear_slot(session: Session, product_id: int, kind: ProductImageKind) -> None:
    if kind == ProductImageKind.EXTRA:
        return
    existing = get_slot_image(session, product_id, kind)
    if existing is not None:
        remove_image(session, existing)


def remove_product_media_dir(product_id: int) -> None:
    directory = product_media_dir(product_id)
    if directory.is_dir():
        shutil.rmtree(directory)


def copy_images_to_product(
    session: Session,
    source_product_id: int,
    target_product_id: int,
) -> None:
    for img in list_images(session, source_product_id):
        src = resolve_media_path(img.relative_path)
        if not src.is_file():
            continue
        if img.kind == ProductImageKind.EXTRA.value:
            add_extra_image(session, target_product_id, src)
        else:
            set_slot_image(
                session,
                target_product_id,
                ProductImageKind(img.kind),
                src,
            )


def apply_pending_images(
    session: Session,
    product_id: int,
    *,
    front: Path | None,
    back: Path | None,
    extras: list[Path],
    clear_front: bool = False,
    clear_back: bool = False,
    removed_extra_ids: list[int] | None = None,
) -> None:
    """Apply editor image state for an existing product."""
    if clear_front:
        clear_slot(session, product_id, ProductImageKind.FRONT)
    if clear_back:
        clear_slot(session, product_id, ProductImageKind.BACK)
    if front is not None:
        set_slot_image(session, product_id, ProductImageKind.FRONT, front)
    if back is not None:
        set_slot_image(session, product_id, ProductImageKind.BACK, back)
    if removed_extra_ids:
        for image_id in removed_extra_ids:
            img = session.get(ProductImage, image_id)
            if img is not None and img.product_id == product_id:
                remove_image(session, img)
    for path in extras:
        add_extra_image(session, product_id, path)
