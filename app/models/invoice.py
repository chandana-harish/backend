from sqlalchemy import Column, Integer, Numeric, ForeignKey, Date, String, DateTime, CheckConstraint
from datetime import datetime,timezone
from app.database import Base
from sqlalchemy.orm import relationship


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(
        Integer,
        ForeignKey("orders.id"),
        nullable=False,
        unique=True
    )

    subtotal = Column(Numeric(10, 2), nullable=False)
    tax = Column(Numeric(10, 2), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)

    discount_type = Column(String(10), nullable=True)
    discount_value = Column(Numeric(10, 2), default=0)

    due_date = Column(Date, nullable=False)

    status = Column(String(20), nullable=False, default="UNPAID")
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    payments = relationship("Payment", back_populates="invoice")
    order = relationship("Order", back_populates="invoice")

    # 👉 MySQL compatible
    __table_args__ = (
        CheckConstraint(
            "status IN ('UNPAID','PARTIALLY_PAID','PAID','OVERDUE', 'CANCELLED', 'REFUNDED')",
            name="check_invoice_status"
        ),
        CheckConstraint(
            "discount_type IN ('FLAT','PERCENT')",
            name="check_discount_type"
        ),
    )
