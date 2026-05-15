import { expect, test } from "@playwright/test";

test("imports CSV and opens ticker report", async ({ page }) => {
  await page.goto("http://127.0.0.1:5173");
  await page.getByRole("link", { name: "Import" }).click();
  await page.getByLabel("Watchlist CSV").setInputFiles("../examples/sample_watchlist.csv");
  await page.getByRole("button", { name: "Preview" }).click();
  await expect(page.getByText("Valid rows: 2")).toBeVisible();
  await page.getByRole("button", { name: "Import valid rows" }).click();
  await page.getByRole("link", { name: "Dashboard" }).click();
  await expect(page.getByText("MSFT")).toBeVisible();
  await page.getByText("MSFT").click();
  await expect(page.getByText("Final Directional Recommendation")).toBeVisible();
});
