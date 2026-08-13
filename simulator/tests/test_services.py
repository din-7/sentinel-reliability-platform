from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from checkout_service.main import app as checkout_app
from inventory_service.main import app as inventory_app
from payment_service.main import app as payment_app


@pytest.fixture(
    params=[
        ("checkout-service", checkout_app),
        ("payment-service", payment_app),
        ("inventory-service", inventory_app),
    ]
)
def service(request):
    service_name, app = request.param
    return service_name, TestClient(app)


def test_health(service):
    service_name, client = service

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "service": service_name,
        "status": "healthy",
    }


def test_metrics(service):
    service_name, client = service
    client.get("/health")

    response = client.get("/metrics")
    body = response.json()

    assert response.status_code == 200
    assert body["service"] == service_name
    assert isinstance(body["request_count"], int)
    assert body["request_count"] >= 1
    assert isinstance(body["error_count"], int)
    assert body["error_count"] == 0
    assert isinstance(body["average_latency_ms"], float)
    assert body["average_latency_ms"] >= 0
    assert datetime.fromisoformat(body["timestamp"]).tzinfo is not None
