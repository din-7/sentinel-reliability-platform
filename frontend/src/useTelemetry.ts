import { useEffect, useState } from "react";
import type { TelemetryEvent } from "./types";

const apiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8080";

export function useTelemetry(pollIntervalMs = 5000) {
  const [events, setEvents] = useState<TelemetryEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const response = await fetch(`${apiUrl}/api/v1/telemetry?limit=100`);
        if (!response.ok) throw new Error(`Backend returned ${response.status}`);
        const data: TelemetryEvent[] = await response.json();
        if (active) {
          setEvents(data);
          setError(null);
        }
      } catch (requestError) {
        if (active) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : "Unable to load telemetry",
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    const poll = window.setInterval(load, pollIntervalMs);
    return () => {
      active = false;
      window.clearInterval(poll);
    };
  }, [pollIntervalMs]);

  return { events, loading, error };
}
