interface Props {
  totalRequests: number;
  totalErrors: number;
  averageLatency: number;
}

export function SummaryMetrics(props: Props) {
  const metrics = [
    ["Total requests", props.totalRequests.toLocaleString()],
    ["Total errors", props.totalErrors.toLocaleString()],
    ["Average latency", `${props.averageLatency.toFixed(1)} ms`],
  ];

  return (
    <section className="summary-grid" aria-label="Summary metrics">
      {metrics.map(([label, value]) => (
        <article className="summary-card" key={label}>
          <span>{label}</span>
          <strong>{value}</strong>
        </article>
      ))}
    </section>
  );
}
