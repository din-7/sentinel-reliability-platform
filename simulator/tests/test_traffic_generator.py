import httpx

from traffic_generator import send_one_round, service_urls_from_environment


class FakeClient:
    def __init__(self, failing_url=None):
        self.failing_url = failing_url
        self.requested_urls = []

    def get(self, url):
        self.requested_urls.append(url)
        request = httpx.Request("GET", url)
        if url == self.failing_url:
            raise httpx.ConnectError("service unavailable", request=request)
        return httpx.Response(200, request=request)


def test_service_urls_use_environment_overrides(monkeypatch):
    monkeypatch.setenv("CHECKOUT_SERVICE_URL", "http://checkout:9001/")

    urls = service_urls_from_environment()

    assert urls["checkout-service"] == "http://checkout:9001"
    assert urls["payment-service"] == "http://localhost:8002"
    assert urls["inventory-service"] == "http://localhost:8003"


def test_send_one_round_requests_every_service_with_jitter(monkeypatch):
    urls = {
        "checkout-service": "http://checkout:8001",
        "payment-service": "http://payment:8002",
        "inventory-service": "http://inventory:8003",
    }
    client = FakeClient()
    delays = []
    monkeypatch.setattr("traffic_generator.random.uniform", lambda start, end: 0.1)

    result = send_one_round(client, urls, jitter_seconds=0.2, sleep=delays.append)

    assert result == (3, 0)
    assert client.requested_urls == [f"{url}/health" for url in urls.values()]
    assert delays == [0.1, 0.1, 0.1]


def test_connection_error_does_not_stop_remaining_requests():
    urls = {
        "checkout-service": "http://checkout:8001",
        "payment-service": "http://payment:8002",
        "inventory-service": "http://inventory:8003",
    }
    failing_url = "http://payment:8002/health"
    client = FakeClient(failing_url=failing_url)

    result = send_one_round(client, urls, jitter_seconds=0)

    assert result == (2, 1)
    assert client.requested_urls[-1] == "http://inventory:8003/health"
