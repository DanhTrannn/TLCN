import { describe, expect, it } from "vitest";

import { AUTO_REFRESH_INTERVAL_MS, shouldAutoRefreshRole } from "./dashboard-refresh";

describe("dashboard refresh policy", () => {
  it("auto-refreshes tactical roles only", () => {
    expect(shouldAutoRefreshRole("store")).toBe(true);
    expect(shouldAutoRefreshRole("inventory")).toBe(true);
    expect(shouldAutoRefreshRole("operations")).toBe(true);
    expect(shouldAutoRefreshRole("marketing")).toBe(true);
    expect(shouldAutoRefreshRole("executive")).toBe(false);
    expect(shouldAutoRefreshRole("sales")).toBe(false);
    expect(shouldAutoRefreshRole("system")).toBe(false);
  });

  it("uses a 60 second interval", () => {
    expect(AUTO_REFRESH_INTERVAL_MS).toBe(60_000);
  });
});
