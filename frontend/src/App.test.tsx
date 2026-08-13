import { render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import App from "./App";

afterEach(() => vi.restoreAllMocks());

it("renders real fetched telemetry and service empty states", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
    ok: true,
    json: async () => [{ service: "checkout-service", timestamp: "2026-08-13T20:00:00Z", request_count: 42, error_count: 2, average_latency_ms: 12.5, fault_mode: "HIGH_LATENCY" }],
  }));

  render(<App />);

  expect((await screen.findAllByText("42")).length).toBe(3);
  expect(screen.getAllByText("HIGH LATENCY").length).toBeGreaterThan(0);
  expect(screen.getByText("payment-service")).toBeInTheDocument();
  expect(screen.getAllByText("No data").length).toBe(2);
});
