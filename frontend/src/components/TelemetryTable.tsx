import type { TelemetryEvent } from "../types";

export function TelemetryTable({ events }: { events: TelemetryEvent[] }) {
  return (
    <section className="panel">
      <div className="panel__heading">
        <div><span className="eyebrow">Live feed</span><h2>Recent telemetry</h2></div>
        <span className="event-count">{events.length} events</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Service</th><th>Mode</th><th>Requests</th><th>Errors</th><th>Latency</th><th>Observed</th></tr></thead>
          <tbody>
            {events.map((event, index) => (
              <tr key={`${event.service}-${event.timestamp}-${index}`}>
                <td className="service-name">{event.service}</td>
                <td><span className={`status status--${event.fault_mode}`}>{event.fault_mode.replaceAll("_", " ")}</span></td>
                <td>{event.request_count.toLocaleString()}</td>
                <td>{event.error_count.toLocaleString()}</td>
                <td>{event.average_latency_ms.toFixed(1)} ms</td>
                <td>{new Date(event.timestamp).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
