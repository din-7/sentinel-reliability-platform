import type { TelemetryEvent } from "./types";

export const serviceNames = [
  "checkout-service",
  "payment-service",
  "inventory-service",
] as const;

export function eventKey(event: TelemetryEvent) {
  return [
    event.service,
    event.timestamp,
    event.request_count,
    event.error_count,
    event.average_latency_ms,
    event.fault_mode,
  ].join("|");
}

export function mergeTelemetry(
  current: TelemetryEvent[],
  incoming: TelemetryEvent[],
  limit = 100,
) {
  const events = new Map<string, TelemetryEvent>();
  for (const event of [...incoming, ...current]) {
    if (!events.has(eventKey(event))) events.set(eventKey(event), event);
  }
  return [...events.values()]
    .sort((left, right) => Date.parse(right.timestamp) - Date.parse(left.timestamp))
    .slice(0, limit);
}

export function latestByService(events: TelemetryEvent[]) {
  const latest = new Map<string, TelemetryEvent>();
  for (const event of events) {
    if (!latest.has(event.service)) latest.set(event.service, event);
  }
  return latest;
}

export function summarize(events: TelemetryEvent[]) {
  const snapshots = [...latestByService(events).values()];
  return {
    totalRequests: snapshots.reduce((sum, event) => sum + event.request_count, 0),
    totalErrors: snapshots.reduce((sum, event) => sum + event.error_count, 0),
    averageLatency:
      snapshots.length === 0
        ? 0
        : snapshots.reduce(
            (sum, event) => sum + event.average_latency_ms,
            0,
          ) / snapshots.length,
  };
}
