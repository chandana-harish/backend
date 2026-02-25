import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def create_test_customer():
    """
    Helper to create a customer using existing endpoint
    """
    payload = {
        "name": "Test Customer",
        "email": f"customer_{uuid.uuid4()}@example.com",
    }
    res = client.post("/customers/create-customer", json=payload)
    assert res.status_code == 201
    return res.json()


def test_create_and_get_customer():
    """
    Customer CREATE (via orders) + GET by ID
    """
    customer = create_test_customer()
    customer_id = customer["id"]

    res = client.get(f"/customers/{customer_id}")
    assert res.status_code == 200

    data = res.json()
    assert data["id"] == customer_id
    assert data["email"] == customer["email"]
    assert data["name"] == customer["name"]


def test_get_customer_not_found():
    """
    GET non-existing customer should return 404
    """
    res = client.get("/customers/999999")
    assert res.status_code == 404


def test_list_customers():
    """
    GET list of customers
    """
    # create at least one customer
    create_test_customer()

    res = client.get("/customers")
    assert res.status_code == 200

    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "id" in data[0]
    assert "email" in data[0]


def test_update_customer():
    """
    UPDATE customer name and email
    """
    customer = create_test_customer()
    customer_id = customer["id"]

    update_payload = {
        "name": "Updated Customer Name",
        "email": f"updated_{uuid.uuid4()}@example.com",
    }

    res = client.put(f"/customers/{customer_id}", json=update_payload)
    assert res.status_code == 200

    data = res.json()
    assert data["id"] == customer_id
    assert data["name"] == "Updated Customer Name"
    assert data["email"] == update_payload["email"]


def test_update_customer_email_conflict():
    """
    Updating customer email to an existing email should fail
    """
    customer1 = create_test_customer()
    customer2 = create_test_customer()

    update_payload = {
        "name": "Conflict Name",
        "email": customer1["email"],  # duplicate email
    }

    res = client.put(f"/customers/{customer2['id']}", json=update_payload)
    assert res.status_code == 400
