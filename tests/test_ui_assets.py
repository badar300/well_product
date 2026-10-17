from __future__ import annotations

from well_product.ui.assets import asset_path


def test_login_hero_asset_is_bundled() -> None:
    found = False
    for name in ("login_hero.jpg", "login_hero.png"):
        path = asset_path(name)
        if path.is_file() and path.stat().st_size > 0:
            found = True
            break
    assert found, "Add login_hero.png or login_hero.jpg under src/well_product/ui/assets/"
