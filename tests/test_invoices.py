import uuid
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


# -----------------------------
# Helpers
# -----------------------------
def create_test_customer():
    payload = {
        "name": "Invoice Test Customer",
        "email": f"invoice_{uuid.uuid4()}@example.com",
    }
    res = client.post("/customers/create-customer", json=payload)
    assert res.status_code == 201
    return res.json()


def create_and_confirm_order(customer_id: int):
    order_res = client.post(
        "/orders",
        json={
            "customer_id": customer_id,
            "items": [
                {"product_name": "Keyboard", "quantity": 2, "unit_price": 2000},
                {"product_name": "Monitor", "quantity": 1, "unit_price": 12000},
            ],
        },
    )
    assert order_res.status_code == 201
    order_id = order_res.json()["id"]

    confirm_res = client.post(f"/orders/{order_id}/confirm")
    assert confirm_res.status_code == 200

    return order_id


# -----------------------------
# 1️⃣ End-to-end invoice flow
# -----------------------------
def test_invoice_flow():
    customer = create_test_customer()
    order_id = create_and_confirm_order(customer["id"])

    invoice_res = client.post(f"/invoices/orders/{order_id}")
    assert invoice_res.status_code == 201

    invoice = invoice_res.json()
    assert invoice["order_id"] == order_id
    assert invoice["status"] == "UNPAID"
    assert invoice["subtotal"] > 0
    assert invoice["tax"] > 0
    assert invoice["total"] > invoice["subtotal"]

    invoice_id = invoice["id"]

    get_res = client.get(f"/invoices/{invoice_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == invoice_id


# -----------------------------
# 2️⃣ Duplicate invoice should fail
# -----------------------------
def test_duplicate_invoice_fails():
    customer = create_test_customer()
    order_id = create_and_confirm_order(customer["id"])

    res1 = client.post(f"/invoices/orders/{order_id}")
    assert res1.status_code == 201

    res2 = client.post(f"/invoices/orders/{order_id}")
    assert res2.status_code == 400


# -----------------------------
# 3️⃣ Invoice for unconfirmed order fails
# -----------------------------
def test_invoice_for_unconfirmed_order_fails():
    customer = create_test_customer()

    order_res = client.post(
        "/orders",
        json={
            "customer_id": customer["id"],
            "items": [{"product_name": "Mouse", "quantity": 1, "unit_price": 500}],
        },
    )
    order_id = order_res.json()["id"]

    invoice_res = client.post(f"/invoices/orders/{order_id}")
    assert invoice_res.status_code == 400


# -----------------------------
# 4️⃣ List invoices
# -----------------------------
def test_invoice_filter_by_status():
    res = client.get("/invoices?status=UNPAID")
    assert res.status_code == 200
    for invoice in res.json():
        assert invoice["status"] == "UNPAID"


def test_invoice_filter_by_customer():
    customer = create_test_customer()

    order_res = client.post(
        "/orders",
        json={
            "customer_id": customer["id"],
            "items": [{"product_name": "Book", "quantity": 1, "unit_price": 500}],
        },
    )
    order_id = order_res.json()["id"]

    client.post(f"/orders/{order_id}/confirm")
    client.post(f"/invoices/orders/{order_id}")

    res = client.get(f"/invoices?customer_id={customer['id']}")
    assert res.status_code == 200
    assert len(res.json()) >= 1


# -----------------------------
# 5️⃣ Cancel invoice
# -----------------------------
def test_cancel_invoice_success():
    customer = create_test_customer()
    order_id = create_and_confirm_order(customer["id"])

    invoice = client.post(f"/invoices/orders/{order_id}").json()
    invoice_id = invoice["id"]

    cancel_res = client.post(f"/invoices/{invoice_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"


# -----------------------------
# 6️⃣ Double cancel should fail
# -----------------------------
def test_double_cancel_invoice_fails():
    customer = create_test_customer()
    order_id = create_and_confirm_order(customer["id"])

    invoice = client.post(f"/invoices/orders/{order_id}").json()
    invoice_id = invoice["id"]

    client.post(f"/invoices/{invoice_id}/cancel")
    res = client.post(f"/invoices/{invoice_id}/cancel")

    assert res.status_code == 400
