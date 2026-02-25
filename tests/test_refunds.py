import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_refund_flow():
    """
    Customer -> Order -> Confirm -> Invoice -> Pay -> Refund
    """

    # Create customer
    customer_res = client.post(
        "/customers/create-customer",
        json={
            "name": "Refund Test Customer",
            "email": f"refund_{uuid.uuid4()}@example.com",
        },
    )
    customer_id = customer_res.json()["id"]

    # Create order
    order_res = client.post(
        "/orders",
        json={
            "customer_id": customer_id,
            "items": [
                {"product_name": "Phone", "quantity": 1, "unit_price": 20000}
            ],
        },
    )
    order_id = order_res.json()["id"]

    # Confirm order
    client.post(f"/orders/{order_id}/confirm")

    # Create invoice
    invoice_res = client.post(f"/invoices/orders/{order_id}")
    invoice = invoice_res.json()
    invoice_id = invoice["id"]
    total = invoice["total"]

    # Pay invoice fully
    client.post(
        "/payments",
        json={
            "invoice_id": invoice_id,
            "amount": total,
            "payment_method": "CARD",
        },
    )

    # Refund half
    refund_res = client.post(
        f"/refunds/invoice/{invoice_id}",
        params={"amount": total / 2},
    )
    assert refund_res.status_code == 201
    refund = refund_res.json()
    assert refund["payment_method"] == "REFUND"
    assert refund["amount"] < 0

    # Invoice should be PARTIALLY_PAID
    invoice_check = client.get(f"/invoices/{invoice_id}")
    assert invoice_check.json()["status"] == "PARTIALLY_PAID"

def test_over_refund_fails():
    customer_res = client.post(
        "/customers",
        json={
            "name": "Over Refund",
            "email": f"over_refund_{uuid.uuid4()}@example.com",
        },
    )
    customer_id = customer_res.json()["id"]

    order_res = client.post(
        "/orders",
        json={
            "customer_id": customer_id,
            "items": [
                {"product_name": "Tablet", "quantity": 1, "unit_price": 10000}
            ],
        },
    )
    order_id = order_res.json()["id"]
    client.post(f"/orders/{order_id}/confirm")

    invoice = client.post(f"/invoices/orders/{order_id}").json()
    invoice_id = invoice["id"]
    total = invoice["total"]

    client.post(
        "/payments",
        json={
            "invoice_id": invoice_id,
            "amount": total,
            "payment_method": "CARD",
        },
    )

    # Over-refund
    res = client.post(
        f"/refunds/invoice/{invoice_id}",
        params={"amount": total + 1},
    )
    assert res.status_code == 400
