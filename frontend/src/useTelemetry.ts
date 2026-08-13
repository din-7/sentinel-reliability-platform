import { useEffect, useState } from "react";
import { mergeTelemetry } from "./telemetry";
import type { TelemetryEvent } from "./types";

const apiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8080";

export type ConnectionStatus = "Connected" | "Reconnecting" | "Disconnected";

function websocketUrl() {
  const url = new URL(apiUrl);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = "/ws/telemetry";
  url.search = "";
  return url.toString();
}

export function useTelemetry() {
  const [events, setEvents] = useState<TelemetryEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] =
    useState<ConnectionStatus>("Reconnecting");

  useEffect(() => {
    let active = true;

    async function loadHistory() {
      try {
        const response = await fetch(`${apiUrl}/api/v1/telemetry?limit=100`);
        if (!response.ok) throw new Error(`Backend returned ${response.status}`);
        const data: TelemetryEvent[] = await response.json();
        if (active) {
          setEvents((current) => mergeTelemetry(current, data));
          setError(null);
        }
      } catch (requestError) {
        if (active) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : "Unable to load telemetry history",
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadHistory();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    let socket: WebSocket | null = null;
    let retryTimer: number | undefined;
    let retryAttempt = 0;

    function connect() {
      if (!active) return;
      setConnectionStatus("Reconnecting");
      socket = new WebSocket(websocketUrl());

      socket.onopen = () => {
        retryAttempt = 0;
        setConnectionStatus("Connected");
      };
      socket.onmessage = (message) => {
        try {
          const event = JSON.parse(message.data) as TelemetryEvent;
          setEvents((current) => mergeTelemetry(current, [event]));
        } catch {
          // Ignore malformed messages and keep the stream alive.
        }
      };
      socket.onerror = () => socket?.close();
      socket.onclose = () => {
        if (!active) return;
        setConnectionStatus("Reconnecting");
        const delay = Math.min(1000 * 2 ** retryAttempt, 10_000);
        retryAttempt += 1;
        retryTimer = window.setTimeout(connect, delay);
      };
    }

    connect();
    return () => {
      active = false;
      if (retryTimer !== undefined) window.clearTimeout(retryTimer);
      socket?.close();
      setConnectionStatus("Disconnected");
    };
  }, []);

  return { events, loading, error, connectionStatus };
}
