import { useEffect, useState } from "react";

import { getHealth } from "../../api/health.api";
import type { HealthResponse } from "../../types/health";

type ConnectionState = "checking" | "connected" | "disconnected";

export function BackendStatusCard() {
  const [state, setState] = useState<ConnectionState>("checking");
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    getHealth(controller.signal)
      .then((response) => {
        setHealth(response);
        setState("connected");
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState("disconnected");
      });
    return () => controller.abort();
  }, []);

  const labels: Record<ConnectionState, string> = {
    checking: "Checking backend",
    connected: "Connected",
    disconnected: "Not connected",
  };

  return (
    <aside className="status-card" aria-live="polite">
      <div className="status-card__topline">
        <span className={`status-dot status-dot--${state}`} />
        <span>{labels[state]}</span>
      </div>
      <strong>{health?.project ?? "FastAPI service"}</strong>
      <span className="status-card__meta">
        {health ? `Version ${health.version}` : "Expected on port 8000"}
      </span>
    </aside>
  );
}
