from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.invoice import Invoice


TAX_RATE = Decimal("0.18")  # 18% tax


def create_invoice(
    db: Session,
    order_id: int,
    discount_type: str | None = None,
    discount_value: Decimal = Decimal("0.00"),
) -> Invoice:

    order = db.get(Order, order_id)
    if not order:
        raise ValueError("Order not found")

    if order.status != "CONFIRMED":
        raise ValueError("Invoice can be created only for CONFIRMED orders")

    if order.invoice:
        raise ValueError("Invoice already exists for this order")

    if not order.items:
        raise ValueError("Order has no items")

    # Subtotal
    subtotal = sum(
        Decimal(item.quantity) * Decimal(item.unit_price)
        for item in order.items
    ).quantize(Decimal("0.01"))

    # Tax
    tax = (subtotal * TAX_RATE).quantize(Decimal("0.01"))

    # Discount
    discount_amount = Decimal("0.00")

    if discount_type == "FLAT":
        discount_amount = discount_value

    elif discount_type == "PERCENT":
        discount_amount = (subtotal * discount_value / Decimal("100")).quantize(
            Decimal("0.01")
        )

    if discount_amount > subtotal:
        raise ValueError("Discount cannot exceed subtotal")

    total = (subtotal + tax - discount_amount).quantize(Decimal("0.01"))

    invoice = Invoice(
        order_id=order.id,
        subtotal=subtotal,
        tax=tax,
        total=total,
        discount_type=discount_type,
        discount_value=discount_value,
        status="UNPAID",
        due_date=(datetime.now(timezone.utc) + timedelta(days=30)).date(),
        created_at=datetime.now(timezone.utc),
    )

    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    return invoice


def get_invoice(db: Session, invoice_id: int) -> Invoice:
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise ValueError("Invoice not found")
    return invoice


def list_invoices(
    db: Session,
    status: Optional[str] = None,
    customer_id: Optional[int] = None,
    order_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> list[Invoice]:

    query = db.query(Invoice).join(Order)

    if status:
        query = query.filter(Invoice.status == status)

    if order_id:
        query = query.filter(Invoice.order_id == order_id)

    if customer_id:
        query = query.filter(Order.customer_id == customer_id)

    if from_date:
        query = query.filter(Invoice.created_at >= from_date)

    if to_date:
        query = query.filter(Invoice.created_at <= to_date)

    return query.order_by(Invoice.id.desc()).all()


def cancel_invoice(db: Session, invoice_id: int) -> Invoice:
    invoice = get_invoice(db, invoice_id)

    if invoice.status == "PAID":
        raise ValueError("Paid invoice cannot be cancelled")

    if invoice.status == "CANCELLED":
        raise ValueError("Invoice already cancelled")

    invoice.status = "CANCELLED"
    db.commit()
    db.refresh(invoice)

    return invoice
