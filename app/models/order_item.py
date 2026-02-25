from sqlalchemy import Column, ForeignKey, Integer, Numeric, String, CheckConstraint
from app.database import Base
from sqlalchemy.orm import relationship

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_name = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")

    __table_args__ = (
        CheckConstraint(quantity > 0, name="check_quantity_positive"),
        CheckConstraint(unit_price > 0, name="check_unit_price_positive"),
    )
