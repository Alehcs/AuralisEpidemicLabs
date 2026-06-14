import { apiGet } from "./client";
import type { HealthResponse } from "../types/health";

export function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return apiGet<HealthResponse>("/health", signal);
}
