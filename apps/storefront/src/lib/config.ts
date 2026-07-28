export const publicConfig = {
  apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
  csrfCookieName: process.env.NEXT_PUBLIC_CSRF_COOKIE_NAME ?? "tlcn_csrf",
} as const;
