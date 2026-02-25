from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from app.models.customer import Customer
from app.models.order import Order
from app.models.order_item import OrderItem


# -----------------------------
# CREATE ORDER
# -----------------------------
def create_order(db: Session, customer_id: int, items: list) -> Order:
    customer = db.get(Customer, customer_id)
    if not customer:
        raise ValueError("Customer not found")

    order = Order(
        customer_id=customer_id,
        status="CREATED",
        created_at=datetime.now(timezone.utc),
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    for item in items:
        db.add(
            OrderItem(
                order_id=order.id,
                product_name=item["product_name"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
            )
        )

    db.commit()

    return get_order(db, order.id)


# -----------------------------
# CONFIRM ORDER
# -----------------------------
def confirm_order(db: Session, order_id: int) -> Order:
    order = get_order(db, order_id)

    if order.status != "CREATED":
        raise ValueError("Only CREATED orders can be confirmed")

    order.status = "CONFIRMED"
    db.commit()
    db.refresh(order)

    return order


# -----------------------------
# GET ORDER (SINGLE)
# -----------------------------
def get_order(db: Session, order_id: int) -> Order:
    order = (
        db.query(Order)
        .options(
            joinedload(Order.customer),
            joinedload(Order.items),
            joinedload(Order.invoice),
        )
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        raise ValueError("Order not found")

    order.total = sum(
        item.quantity * item.unit_price
        for item in order.items
    )

    return order


# -----------------------------
# UPDATE ORDER ITEMS
# -----------------------------
def update_order_items(db: Session, order_id: int, items: list) -> Order:
    order = get_order(db, order_id)

    if order.status != "CREATED":
        raise ValueError("Only CREATED orders can be updated")

    try:
        db.query(OrderItem).filter(OrderItem.order_id == order_id).delete()

        for item in items:
            db.add(
                OrderItem(
                    order_id=order.id,
                    product_name=item["product_name"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                )
            )

        db.commit()
        return get_order(db, order_id)

    except SQLAlchemyError:
        db.rollback()
        raise


# -----------------------------
# CANCEL ORDER
# -----------------------------
def cancel_order(db: Session, order_id: int) -> Order:
    order = get_order(db, order_id)

    if order.status == "CONFIRMED":
        raise ValueError("Confirmed orders cannot be cancelled")

    if order.status == "CANCELLED":
        raise ValueError("Order already cancelled")

    order.status = "CANCELLED"
    db.commit()
    db.refresh(order)

    return order


# -----------------------------
# LIST ORDERS (PAGINATION + FILTERS)
# -----------------------------
def list_orders(
    db: Session,
    offset: int = 0,
    limit: int = 15,
    status: str | None = None,
    customer_id: int | None = None,
) -> list[Order]:

    query = (
        db.query(Order)
        .options(
            joinedload(Order.customer),
            joinedload(Order.items),
            joinedload(Order.invoice),
        )
    )

    if status:
        query = query.filter(Order.status == status)

    if customer_id:
        query = query.filter(Order.customer_id == customer_id)

    orders = (
        query
        .order_by(Order.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    for order in orders:
        order.total = sum(
            item.quantity * item.unit_price
            for item in order.items
        )

    return orders
