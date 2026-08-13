export type FaultMode =
  | "NORMAL"
  | "HIGH_LATENCY"
  | "HIGH_ERROR_RATE"
  | "OFFLINE";

export interface TelemetryEvent {
  service: string;
  timestamp: string;
  request_count: number;
  error_count: number;
  average_latency_ms: number;
  fault_mode: FaultMode;
}
