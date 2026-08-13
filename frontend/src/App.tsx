import { ServiceCard } from "./components/ServiceCard";
import { SummaryMetrics } from "./components/SummaryMetrics";
import { TelemetryTable } from "./components/TelemetryTable";
import { latestByService, serviceNames, summarize } from "./telemetry";
import { useTelemetry } from "./useTelemetry";

export default function App() {
  const { events, loading, error, connectionStatus } = useTelemetry();
  const latest = latestByService(events);
  const summary = summarize(events);

  return (
    <main>
      <header className="masthead">
        <div className="brand-mark">S</div>
        <div><span className="eyebrow">Reliability control plane</span><h1>Sentinel</h1><p>Live operational health across your distributed services.</p></div>
        <div className={`live-indicator live-indicator--${connectionStatus.toLowerCase()}`}><span />{connectionStatus}</div>
      </header>

      {loading && <div className="notice">Connecting to Sentinel telemetry…</div>}
      {error && <div className="notice notice--error">Unable to load telemetry history: {error}.</div>}

      {!loading && events.length === 0 ? (
        <section className="empty-state"><h2>No telemetry received yet</h2><p>Start the traffic generator and this dashboard will populate automatically.</p></section>
      ) : (
        <>
          <SummaryMetrics {...summary} />
          <section className="services-section">
            <div className="section-heading"><div><span className="eyebrow">Fleet</span><h2>Service status</h2></div><span>{latest.size} / {serviceNames.length} reporting</span></div>
            <div className="service-grid">
              {serviceNames.map((name) => <ServiceCard key={name} serviceName={name} event={latest.get(name)} />)}
            </div>
          </section>
          <TelemetryTable events={events} />
        </>
      )}
    </main>
  );
}
