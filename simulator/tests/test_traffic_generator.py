import httpx

from traffic_generator import (
    send_one_round,
    sentinel_backend_url_from_environment,
    service_urls_from_environment,
)


class FakeClient:
    def __init__(self, failing_url=None, fault_modes=None, service_names=None):
        self.failing_url = failing_url
        self.fault_modes = fault_modes or {}
        self.service_names = service_names or {}
        self.requested_urls = []
        self.telemetry_payloads = []

    def get(self, url):
        self.requested_urls.append(url)
        request = httpx.Request("GET", url)
        if url == self.failing_url:
            raise httpx.ConnectError("service unavailable", request=request)
        if url.endswith("/metrics"):
            host = url.split("//", 1)[1].split(":", 1)[0]
            service_name = self.service_names.get(host, f"{host}-service")
            return httpx.Response(
                200,
                request=request,
                json={
                    "service": service_name,
                    "timestamp": "2026-08-13T18:42:20Z",
                    "request_count": 10,
                    "error_count": 0,
                    "average_latency_ms": 1.5,
                    "fault_mode": self.fault_modes.get(service_name, "NORMAL"),
                },
            )
        return httpx.Response(200, request=request)

    def post(self, url, json):
        self.requested_urls.append(url)
        self.telemetry_payloads.append(json)
        request = httpx.Request("POST", url)
        if url == self.failing_url:
            raise httpx.ConnectError("service unavailable", request=request)
        return httpx.Response(201, request=request, json=json)


def test_service_urls_use_environment_overrides(monkeypatch):
    monkeypatch.setenv("CHECKOUT_SERVICE_URL", "http://checkout:9001/")

    urls = service_urls_from_environment()

    assert urls["checkout-service"] == "http://checkout:9001"
    assert urls["payment-service"] == "http://localhost:8002"
    assert urls["inventory-service"] == "http://localhost:8003"


def test_backend_url_uses_environment_override(monkeypatch):
    monkeypatch.setenv("SENTINEL_BACKEND_URL", "http://sentinel:9000/")

    assert sentinel_backend_url_from_environment() == "http://sentinel:9000"


def test_send_one_round_requests_every_service_with_jitter(monkeypatch):
    urls = {
        "checkout-service": "http://checkout:8001",
        "payment-service": "http://payment:8002",
        "inventory-service": "http://inventory:8003",
    }
    client = FakeClient()
    delays = []
    monkeypatch.setattr("traffic_generator.random.uniform", lambda start, end: 0.1)

    result = send_one_round(
        client,
        urls,
        "http://backend:8080",
        jitter_seconds=0.2,
        sleep=delays.append,
    )

    assert result == (3, 0)
    for url in urls.values():
        assert f"{url}/health" in client.requested_urls
        assert f"{url}/metrics" in client.requested_urls
    assert client.requested_urls.count("http://backend:8080/api/v1/telemetry") == 3
    assert [payload["service"] for payload in client.telemetry_payloads] == [
        "checkout-service",
        "payment-service",
        "inventory-service",
    ]
    assert delays == [0.1, 0.1, 0.1]


def test_connection_error_does_not_stop_remaining_requests():
    urls = {
        "checkout-service": "http://checkout:8001",
        "payment-service": "http://payment:8002",
        "inventory-service": "http://inventory:8003",
    }
    failing_url = "http://payment:8002/metrics"
    client = FakeClient(failing_url=failing_url)

    result = send_one_round(client, urls, "http://backend:8080", jitter_seconds=0)

    assert result == (2, 1)
    assert "http://inventory:8003/metrics" in client.requested_urls
    assert client.telemetry_payloads[-1]["service"] == "inventory-service"


def test_different_service_fault_modes_remain_associated():
    urls = {
        "checkout-service": "http://checkout:8001",
        "payment-service": "http://payment:8002",
        "inventory-service": "http://inventory:8003",
    }
    client = FakeClient(
        fault_modes={
            "checkout-service": "HIGH_LATENCY",
            "payment-service": "NORMAL",
            "inventory-service": "OFFLINE",
        }
    )

    result = send_one_round(client, urls, "http://backend:8080", jitter_seconds=0)

    assert result == (3, 0)
    assert {
        payload["service"]: payload["fault_mode"]
        for payload in client.telemetry_payloads
    } == {
        "checkout-service": "HIGH_LATENCY",
        "payment-service": "NORMAL",
        "inventory-service": "OFFLINE",
    }


def test_mismatched_metrics_identity_is_not_forwarded():
    urls = {
        "checkout-service": "http://checkout:8001",
        "payment-service": "http://payment:8002",
    }
    client = FakeClient(service_names={"checkout": "payment-service"})

    result = send_one_round(client, urls, "http://backend:8080", jitter_seconds=0)

    assert result == (1, 1)
    assert [payload["service"] for payload in client.telemetry_payloads] == [
        "payment-service"
    ]
