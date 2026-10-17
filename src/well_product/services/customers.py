from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from well_product.models import Customer


def list_customers(session: Session) -> list[Customer]:
    return list(session.scalars(select(Customer).order_by(Customer.name)).all())


def get_customer(session: Session, customer_id: int) -> Customer | None:
    return session.get(Customer, customer_id)


def create_customer(
    session: Session,
    *,
    name: str,
    email: str | None = None,
    phone: str | None = None,
    company: str | None = None,
    address: str | None = None,
    notes: str | None = None,
) -> Customer:
    customer = Customer(
        name=name.strip(),
        email=email,
        phone=phone,
        company=company,
        address=address,
        notes=notes,
    )
    session.add(customer)
    session.flush()
    return customer


def update_customer(
    session: Session,
    customer: Customer,
    *,
    name: str,
    email: str | None,
    phone: str | None,
    company: str | None,
    address: str | None,
    notes: str | None,
) -> Customer:
    customer.name = name.strip()
    customer.email = email
    customer.phone = phone
    customer.company = company
    customer.address = address
    customer.notes = notes
    session.flush()
    return customer


def delete_customer(session: Session, customer: Customer) -> None:
    session.delete(customer)
