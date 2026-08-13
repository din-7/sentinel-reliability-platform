import type { TelemetryEvent } from "../types";

interface Props {
  serviceName: string;
  event?: TelemetryEvent;
}

function label(mode: string) {
  return mode.replaceAll("_", " ");
}

export function ServiceCard({ serviceName, event }: Props) {
  return (
    <article className="service-card">
      <div className="service-card__heading">
        <div>
          <span className="eyebrow">Service</span>
          <h3>{serviceName}</h3>
        </div>
        <span className={`status status--${event?.fault_mode ?? "unknown"}`}>
          {event ? label(event.fault_mode) : "No data"}
        </span>
      </div>
      {event ? (
        <>
          <dl className="service-metrics">
            <div><dt>Requests</dt><dd>{event.request_count.toLocaleString()}</dd></div>
            <div><dt>Errors</dt><dd>{event.error_count.toLocaleString()}</dd></div>
            <div><dt>Avg latency</dt><dd>{event.average_latency_ms.toFixed(1)} ms</dd></div>
          </dl>
          <p className="timestamp">Updated {new Date(event.timestamp).toLocaleString()}</p>
        </>
      ) : (
        <p className="empty-copy">Waiting for the first telemetry event.</p>
      )}
    </article>
  );
}
