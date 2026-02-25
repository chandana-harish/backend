
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.invoice import Invoice
from app.models.payment import Payment


# -----------------------------
# CREATE PAYMENT
# -----------------------------
def create_payment(
    db: Session,
    invoice_id: int,
    amount: Decimal,
    payment_method: str,
) -> Payment:
    amount = Decimal(str(amount))
    # 1️⃣ Validate invoice
    
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise ValueError("Invoice not found")
    
    if invoice.status == "CANCELLED":
        raise ValueError("Cannot pay a cancelled invoice")

    if invoice.status == "PAID":
        raise ValueError("Invoice is already fully paid")

    if amount <= Decimal("0.00"):
        raise ValueError("Payment amount must be greater than zero")

    # 2️⃣ Calculate total paid so far
    total_paid = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.invoice_id == invoice_id)
        .scalar()
    )

    total_paid = Decimal(str(total_paid))

    # 3️⃣ Prevent overpayment
    if total_paid + amount > invoice.total:
        raise ValueError("Payment exceeds invoice total")

    # 4️⃣ Create payment
    payment = Payment(
        invoice_id=invoice_id,
        amount=amount,
        payment_method=payment_method,
        paid_at=datetime.now(timezone.utc),
    )

    db.add(payment)
    db.flush()  # get payment.id without committing yet

    # 5️⃣ Update invoice status
    new_total_paid = total_paid + amount

    if new_total_paid == invoice.total:
        invoice.status = "PAID"
    else:
        invoice.status = "PARTIALLY_PAID"

    db.commit()
    db.refresh(payment)

    return payment


# -----------------------------
# GET PAYMENTS FOR INVOICE
# -----------------------------
def get_payments_for_invoice(
    db: Session,
    invoice_id: int,
) -> list[Payment]:
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise ValueError("Invoice not found")

    payments = (
        db.query(Payment)
        .filter(Payment.invoice_id == invoice_id)
        .order_by(Payment.paid_at.asc())
        .all()
    )

    return payments
