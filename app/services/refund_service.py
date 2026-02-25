from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.invoice import Invoice
from app.models.payment import Payment


def refund_payment(
    db: Session,
    invoice_id: int,
    reason: str | None = None,
):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise ValueError("Invoice not found")

    if invoice.status != "PAID":
        raise ValueError("Refund allowed only for fully paid invoices")

    # Optional: validate payments exist
    total_paid = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.invoice_id == invoice_id)
        .scalar()
    )

    if Decimal(str(total_paid)) != invoice.total:
        raise ValueError("Invoice is not fully paid")

    # ✅ Just update invoice
    invoice.status = "REFUNDED"
    invoice.refunded_at = datetime.now(timezone.utc)
    invoice.refund_reason = reason

    db.commit()
    db.refresh(invoice)

    return invoice
