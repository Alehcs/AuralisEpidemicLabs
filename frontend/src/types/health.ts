export interface HealthResponse {
  status: "ok" | string;
  project: string;
  version: string;
}
