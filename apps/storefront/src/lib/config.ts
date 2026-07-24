export const publicConfig = {
  apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
  eventCollectorUrl: process.env.NEXT_PUBLIC_EVENT_COLLECTOR_URL ?? "http://localhost:8001"
} as const;

