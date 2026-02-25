import uuid
from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# -----------------------------
# Helpers
# -----------------------------
def create_test_customer():
    res = client.post(
        "/customers/create-customer",
        json={
            "name": "Payment Test Customer",
            "email": f"payment_{uuid.uuid4()}@example.com",
        },
    )
    assert res.status_code == 201
    return res.json()


def create_and_confirm_order(customer_id: int):
    order_res = client.post(
        "/orders",
        json={
            "customer_id": customer_id,
            "items": [
                {
                    "product_name": "Laptop",
                    "quantity": 1,
                    "unit_price": 50000,
                }
            ],
        },
    )
    assert order_res.status_code == 201
    order_id = order_res.json()["id"]

    confirm_res = client.post(f"/orders/{order_id}/confirm")
    assert confirm_res.status_code == 200

    return order_id


def create_invoice(order_id: int):
    res = client.post(f"/invoices/orders/{order_id}")
    assert res.status_code == 201
    return res.json()


# -----------------------------
# Payment Flow Test
# -----------------------------
def test_payment_flow():
    """
    End-to-end payment test:
    Customer → Order → Confirm → Invoice → Partial → Full → Overpay fail
    """

    # 1️⃣ Customer
    customer = create_test_customer()

    # 2️⃣ Order + confirm
    order_id = create_and_confirm_order(customer["id"])

    # 3️⃣ Invoice
    invoice = create_invoice(order_id)
    invoice_id = invoice["id"]
    invoice_total = Decimal(str(invoice["total"]))

    assert invoice["status"] == "UNPAID"

    # 4️⃣ Partial payment
    partial_amount = invoice_total / Decimal("2")

    payment1 = client.post(
        "/payments",
        json={
            "invoice_id": invoice_id,
            "amount": float(partial_amount),
            "payment_method": "CARD",
        },
    )
    assert payment1.status_code == 201

    invoice_check = client.get(f"/invoices/{invoice_id}").json()
    assert invoice_check["status"] == "PARTIALLY_PAID"

    # 5️⃣ Final payment
    remaining = invoice_total - partial_amount

    payment2 = client.post(
        "/payments",
        json={
            "invoice_id": invoice_id,
            "amount": float(remaining),
            "payment_method": "BANK_TRANSFER",
        },
    )
    assert payment2.status_code == 201

    invoice_check = client.get(f"/invoices/{invoice_id}").json()
    assert invoice_check["status"] == "PAID"

    # 6️⃣ Overpayment should fail
    overpay = client.post(
        "/payments",
        json={
            "invoice_id": invoice_id,
            "amount": 1,
            "payment_method": "CASH",
        },
    )
    assert overpay.status_code == 400

    # 7️⃣ Fetch payments
    payments_res = client.get(f"/payments/invoice/{invoice_id}")
    assert payments_res.status_code == 200

    payments = payments_res.json()
    assert len(payments) == 2
    assert payments[0]["amount"] > 0
    assert payments[1]["amount"] > 0
