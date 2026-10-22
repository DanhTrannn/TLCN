export const AUTO_REFRESH_INTERVAL_MS = 60_000;

const AUTO_REFRESH_ROLES = new Set(["store", "inventory", "operations", "marketing"]);

export function shouldAutoRefreshRole(role: string): boolean {
  return AUTO_REFRESH_ROLES.has(role);
}

export function formatLastUpdated(date: Date | null): string {
  if (!date) return "";
  return date.toLocaleTimeString("vi-VN", { hour12: false });
}
