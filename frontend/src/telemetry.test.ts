import { describe, expect, it } from "vitest";
import { latestByService, mergeTelemetry, summarize } from "./telemetry";
import type { TelemetryEvent } from "./types";

const events: TelemetryEvent[] = [
  { service: "checkout-service", timestamp: "2026-08-13T20:00:02Z", request_count: 20, error_count: 2, average_latency_ms: 30, fault_mode: "HIGH_LATENCY" },
  { service: "payment-service", timestamp: "2026-08-13T20:00:01Z", request_count: 10, error_count: 1, average_latency_ms: 10, fault_mode: "NORMAL" },
  { service: "checkout-service", timestamp: "2026-08-13T19:00:00Z", request_count: 1, error_count: 0, average_latency_ms: 1, fault_mode: "NORMAL" },
];

describe("telemetry derivation", () => {
  it("uses the first newest-first event for each service", () => {
    expect(latestByService(events).get("checkout-service")?.fault_mode).toBe("HIGH_LATENCY");
  });

  it("summarizes only latest service snapshots", () => {
    expect(summarize(events)).toEqual({ totalRequests: 30, totalErrors: 3, averageLatency: 20 });
  });

  it("merges live events newest-first without duplicates", () => {
    const live = { ...events[0], request_count: 21 };

    expect(mergeTelemetry(events, [live, events[0]])).toEqual([
      live,
      events[0],
      events[1],
      events[2],
    ]);
  });
});
