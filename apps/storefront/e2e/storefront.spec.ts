import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.route("**/api/v1/products**", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ items: [], next_cursor: null }),
    });
  });
  await page.route("**/api/v1/auth/me", async (route) => {
    await route.fulfill({
      status: 401,
      contentType: "application/json",
      body: JSON.stringify({ error: { code: "AUTH_REQUIRED", message: "Yêu cầu đăng nhập." } }),
    });
  });
});

test("renders the public storefront and navigates to the catalog", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: /Mỗi ngày/ })).toBeVisible();
  await page.getByRole("link", { name: /Khám phá bộ sưu tập/ }).click();
  await expect(page).toHaveURL(/\/products/);
});

test("protects login return targets from open redirects", async ({ page }) => {
  await page.goto("/login?returnTo=https://evil.example");

  await expect(page.getByRole("heading", { name: "Đăng nhập" })).toBeVisible();
  await expect(page.getByLabel("Email")).toBeVisible();
  await expect(page.getByLabel("Mật khẩu")).toBeVisible();
});
