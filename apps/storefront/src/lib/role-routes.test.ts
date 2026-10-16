import { describe, expect, it } from "vitest";

import { canRoleAccessRoute, getRoleHomeRoute, resolvePostLoginRedirect } from "./role-routes";

describe("role route policy", () => {
  it("routes each staff role to its own workspace", () => {
    expect(getRoleHomeRoute("store_manager")).toBe("/store");
    expect(getRoleHomeRoute("marketing_manager")).toBe("/admin/analytics?role=marketing");
    expect(getRoleHomeRoute("customer")).toBe("/products");
  });

  it("blocks cross-role operational pages", () => {
    expect(canRoleAccessRoute("marketing_manager", "/admin/coupons")).toBe(true);
    expect(canRoleAccessRoute("marketing_manager", "/admin/orders")).toBe(false);
    expect(canRoleAccessRoute("store_manager", "/store/pos")).toBe(true);
  });

  it("rejects open redirects and unauthorized return targets", () => {
    expect(resolvePostLoginRedirect("admin", "https://evil.example")).toBe("/admin");
    expect(resolvePostLoginRedirect("admin", "//evil.example")).toBe("/admin");
    expect(resolvePostLoginRedirect("marketing_manager", "/admin/orders")).toBe(
      "/admin/analytics?role=marketing"
    );
  });
});
