import { expect, test } from "@playwright/test";

test.describe("public smoke", () => {
  test("login page shows email and password fields", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByRole("heading", { name: "ThreatVision" })).toBeVisible();
    await expect(page.locator("#email")).toBeVisible();
    await expect(page.locator("#password")).toBeVisible();
    await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
  });

  test("analyze requires auth — middleware sends user to login", async ({ page }) => {
    await page.goto("/analyze");
    await page.waitForURL(/\/login/, { timeout: 15_000 });
    await expect(page.getByRole("heading", { name: "ThreatVision" })).toBeVisible();
    await expect(page.locator("#email")).toBeVisible();
  });

  test("about page loads", async ({ page }) => {
    await page.goto("/about");
    await expect(page.getByRole("heading", { name: "About ThreatVision" })).toBeVisible();
  });
});

test.describe("authenticated analyze (optional)", () => {
  test("vendor breakdown appears after successful analyze", async ({ page }) => {
    test.skip(
      !process.env.E2E_EMAIL || !process.env.E2E_PASSWORD,
      "Set E2E_EMAIL and E2E_PASSWORD (and run backend + BFF env) for this integration smoke.",
    );

    await page.goto("/login");
    await page.locator("#email").fill(process.env.E2E_EMAIL!);
    await page.locator("#password").fill(process.env.E2E_PASSWORD!);
    await page.getByRole("button", { name: "Sign in" }).click();

    await page.waitForURL(/\/(dashboard|analyze|settings)/, { timeout: 45_000 });

    await page.goto("/analyze");
    await expect(page.locator("#ioc-q")).toBeVisible({ timeout: 15_000 });
    await page.locator("#ioc-q").fill("8.8.8.8");
    await page.getByRole("button", { name: "Analyze" }).click();

    await expect(page.getByTestId("vendor-breakdown")).toBeVisible({ timeout: 90_000 });
    await expect(page.getByRole("heading", { name: "Vendor breakdown" })).toBeVisible();
  });
});
