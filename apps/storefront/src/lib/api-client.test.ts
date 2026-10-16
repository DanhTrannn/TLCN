import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, apiFetch } from "./api-client";

describe("apiFetch", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("sends cookies and decodes successful JSON responses", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(apiFetch<{ ok: boolean }>("/health")).resolves.toEqual({ ok: true });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/health",
      expect.objectContaining({ credentials: "include" })
    );
  });

  it("preserves the API error contract", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({ error: { code: "FORBIDDEN", message: "Không có quyền truy cập." } }),
          { status: 403, headers: { "Content-Type": "application/json" } }
        )
      )
    );

    const error = await apiFetch("/api/v1/admin/analytics/role-metrics?target_role=executive").catch(
      (caught: unknown) => caught
    );
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      name: "ApiError",
      status: 403,
      code: "FORBIDDEN",
      message: "Không có quyền truy cập.",
    });
  });

  it("handles empty 204 responses", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 204 })));

    await expect(apiFetch<void>("/api/v1/auth/logout", { method: "POST" })).resolves.toBeUndefined();
  });
});
