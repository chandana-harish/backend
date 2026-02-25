import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# -----------------------------
# HELPERS
# -----------------------------
def create_test_customer_helper():
    payload = {
        "name": "Order Test Customer",
        "email": f"order_{uuid.uuid4()}@example.com",
    }
    res = client.post("/customers/create-customer", json=payload)
    assert res.status_code == 201
    return res.json()


# -----------------------------
# TEST: CREATE + CONFIRM ORDER
# -----------------------------
def test_full_order_flow():
    """
    End-to-end test:
    Customer -> Order -> Confirm Order
    """

    # 1. CREATE CUSTOMER (via customers service)
    customer = create_test_customer_helper()
    customer_id = customer["id"]

    # 2. CREATE ORDER
    order_payload = {
        "customer_id": customer_id,
        "items": [
            {
                "product_name": "Laptop",
                "quantity": 2,
                "unit_price": 50000,
            },
            {
                "product_name": "Mouse",
                "quantity": 1,
                "unit_price": 1500,
            },
        ],
    }

    order_res = client.post("/orders", json=order_payload)
    assert order_res.status_code == 201

    order_data = order_res.json()
    assert order_data["status"] == "CREATED"
    assert len(order_data["items"]) == 2

    order_id = order_data["id"]

    # 3. CONFIRM ORDER
    confirm_res = client.post(f"/orders/{order_id}/confirm")
    assert confirm_res.status_code == 200
    assert confirm_res.json()["status"] == "CONFIRMED"

    # 4. INVALID CONFIRM (ALREADY CONFIRMED)
    invalid_confirm_res = client.post(f"/orders/{order_id}/confirm")
    assert invalid_confirm_res.status_code == 400


# -----------------------------
# TEST: UPDATE ORDER ITEMS
# -----------------------------
def test_update_order_items_success():
    """
    Update order items when status is CREATED
    """

    customer = create_test_customer_helper()
    customer_id = customer["id"]

    # Create order
    order_res = client.post(
        "/orders",
        json={
            "customer_id": customer_id,
            "items": [
                {
                    "product_name": "Mouse",
                    "quantity": 1,
                    "unit_price": 1000,
                }
            ],
        },
    )
    assert order_res.status_code == 201
    order_id = order_res.json()["id"]

    # Update items
    update_res = client.put(
        f"/orders/{order_id}",
        json={
            "items": [
                {
                    "product_name": "Keyboard",
                    "quantity": 2,
                    "unit_price": 2000,
                },
                {
                    "product_name": "Monitor",
                    "quantity": 1,
                    "unit_price": 12000,
                },
            ]
        },
    )

    assert update_res.status_code == 200
    data = update_res.json()

    assert data["status"] == "CREATED"
    assert len(data["items"]) == 2


# -----------------------------
# TEST: UPDATE CONFIRMED ORDER FAILS
# -----------------------------
def test_update_confirmed_order_fails():
    """
    Updating a CONFIRMED order should fail
    """

    customer = create_test_customer_helper()
    customer_id = customer["id"]

    # Create order
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
    order_id = order_res.json()["id"]

    # Confirm order
    client.post(f"/orders/{order_id}/confirm")

    # Attempt update
    update_res = client.put(
        f"/orders/{order_id}",
        json={
            "items": [
                {
                    "product_name": "Tablet",
                    "quantity": 1,
                    "unit_price": 30000,
                }
            ]
        },
    )

    assert update_res.status_code == 400


def test_cancel_order_success():
    customer = create_test_customer_helper()

    order_res = client.post(
        "/orders",
        json={
            "customer_id": customer["id"],
            "items": [
                {"product_name": "Book", "quantity": 1, "unit_price": 500}
            ],
        },
    )
    order_id = order_res.json()["id"]

    cancel_res = client.post(f"/orders/{order_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"


def test_cancel_confirmed_order_fails():
    customer = create_test_customer_helper()

    order_res = client.post(
        "/orders",
        json={
            "customer_id": customer["id"],
            "items": [
                {"product_name": "Phone", "quantity": 1, "unit_price": 30000}
            ],
        },
    )
    order_id = order_res.json()["id"]

    client.post(f"/orders/{order_id}/confirm")

    cancel_res = client.post(f"/orders/{order_id}/cancel")
    assert cancel_res.status_code == 400


def test_double_cancel_fails():
    customer = create_test_customer_helper()

    order_res = client.post(
        "/orders",
        json={
            "customer_id": customer["id"],
            "items": [
                {"product_name": "Pen", "quantity": 2, "unit_price": 50}
            ],
        },
    )
    order_id = order_res.json()["id"]

    client.post(f"/orders/{order_id}/cancel")

    second_cancel = client.post(f"/orders/{order_id}/cancel")
    assert second_cancel.status_code == 400
