"""Continuously generate lightweight traffic for the simulated services."""

import logging
import os
import random
import time
from collections.abc import Callable, Mapping

import httpx


DEFAULT_SERVICE_URLS = {
    "checkout-service": "http://localhost:8001",
    "payment-service": "http://localhost:8002",
    "inventory-service": "http://localhost:8003",
}

SERVICE_URL_ENV_VARS = {
    "checkout-service": "CHECKOUT_SERVICE_URL",
    "payment-service": "PAYMENT_SERVICE_URL",
    "inventory-service": "INVENTORY_SERVICE_URL",
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)


def service_urls_from_environment() -> dict[str, str]:
    """Return service base URLs, using localhost defaults outside Docker."""
    return {
        service_name: os.getenv(env_var, DEFAULT_SERVICE_URLS[service_name]).rstrip("/")
        for service_name, env_var in SERVICE_URL_ENV_VARS.items()
    }


def sentinel_backend_url_from_environment() -> str:
    return os.getenv("SENTINEL_BACKEND_URL", "http://localhost:8080").rstrip("/")


def send_one_round(
    client: httpx.Client,
    service_urls: Mapping[str, str],
    sentinel_backend_url: str,
    jitter_seconds: float,
    sleep: Callable[[float], None] = time.sleep,
) -> tuple[int, int]:
    """Collect and forward one telemetry event per service."""
    successes = 0
    failures = 0

    for service_name, base_url in service_urls.items():
        if jitter_seconds > 0:
            sleep(random.uniform(0, jitter_seconds))

        try:
            health_response = client.get(f"{base_url}/health")
            health_response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Health check for %s failed: %s", service_name, exc)

        try:
            metrics_response = client.get(f"{base_url}/metrics")
            metrics_response.raise_for_status()
            telemetry = metrics_response.json()

            if telemetry.get("service") != service_name:
                raise ValueError(
                    f"metrics identity mismatch: expected {service_name!r}, "
                    f"received {telemetry.get('service')!r}"
                )

            backend_response = client.post(
                f"{sentinel_backend_url}/api/v1/telemetry",
                json=telemetry,
            )
            backend_response.raise_for_status()
            successes += 1
        except (httpx.HTTPError, ValueError) as exc:
            failures += 1
            logger.warning("Telemetry delivery for %s failed: %s", service_name, exc)

    return successes, failures


def main() -> None:
    service_urls = service_urls_from_environment()
    sentinel_backend_url = sentinel_backend_url_from_environment()
    interval_seconds = max(0.0, float(os.getenv("REQUEST_INTERVAL_SECONDS", "1.0")))
    jitter_seconds = max(0.0, float(os.getenv("REQUEST_JITTER_SECONDS", "0.2")))
    timeout_seconds = max(0.1, float(os.getenv("REQUEST_TIMEOUT_SECONDS", "2.0")))

    logger.info("Generating traffic for: %s", ", ".join(service_urls))

    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            while True:
                send_one_round(
                    client,
                    service_urls,
                    sentinel_backend_url,
                    jitter_seconds,
                )
                time.sleep(interval_seconds)
    except KeyboardInterrupt:
        logger.info("Traffic generator stopped")


if __name__ == "__main__":
    main()
