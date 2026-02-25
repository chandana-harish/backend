from sqlalchemy import Column, ForeignKey, Integer, Numeric, String, DateTime, CheckConstraint, Text
from datetime import datetime ,timezone
from app.database import Base
from sqlalchemy.orm import relationship

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(20), nullable=False)
    paid_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    note = Column(Text, nullable=True)

    invoice = relationship("Invoice", back_populates="payments")

    __table_args__ = (
        CheckConstraint(amount > 0, name="check_payment_amount_positive"),
        CheckConstraint(
            payment_method.in_(["CASH", "CARD", "UPI", "BANK_TRANSFER"]),
            name="check_payment_method"
        ),
    )
