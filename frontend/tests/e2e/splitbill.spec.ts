import { expect, test } from "@playwright/test";

const API = process.env.NEXT_PUBLIC_API_BASE_URL;
if (!API)
  throw new Error(
    "Run through backend/scripts/test_frontend.py to use an isolated database.",
  );

test.beforeEach(async ({ page, request }) => {
  for (const group of [1, 2]) {
    const response = await request.get(`${API}/groups/${group}/expenses`, {
      headers: { "X-User": "bob" },
    });
    expect(response.ok()).toBeTruthy();
    for (const expense of await response.json()) {
      const deleted = await request.delete(
        `${API}/groups/${group}/expenses/${expense.id}`,
        { headers: { "X-User": expense.paid_by } },
      );
      expect(deleted.status()).toBe(204);
    }
  }
  await page.goto("/");
  await expect(page.getByLabel("Your group")).toHaveValue("1");
  await expect(
    page.getByRole("heading", { name: "Add an expense" }),
  ).toBeVisible();
  await expect(page.getByLabel("Description", { exact: true })).toBeVisible();
});

test("equal preview, real save, balances, payer-only deletion and responsive layout", async ({
  page,
}, info) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page
    .getByLabel("Description", { exact: true })
    .fill("Night market dinner");
  await page.getByLabel("Amount THB", { exact: true }).fill("100.00");
  await expect(page.locator(".share-value")).toHaveText([
    "33.34",
    "33.33",
    "33.33",
  ]);
  await page.getByRole("button", { name: "Save expense" }).click();
  await expect(
    page.getByRole("heading", { name: "Night market dinner" }),
  ).toBeVisible();
  await expect(page.locator(".balance-amount strong")).toHaveText([
    "+66.66",
    "-33.33",
    "-33.33",
  ]);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: `test-results/screenshots/${info.project.name}.png`,
    fullPage: true,
  });
  await page.getByLabel("Viewing as").selectOption("bob");
  await expect(
    page.getByRole("heading", { name: "Night market dinner" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", {
      name: "Delete Night market dinner",
      exact: true,
    }),
  ).toHaveCount(0);
  await page.getByLabel("Viewing as").selectOption("alice");
  await page
    .getByRole("button", { name: "Delete Night market dinner", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Confirm delete", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "No expenses yet" }),
  ).toBeVisible();
  await expect(page.locator(".balance-amount strong")).toHaveText([
    "0.00",
    "0.00",
    "0.00",
  ]);
  expect(errors).toEqual([]);
});

test("exact split blocks submission until amounts match and rejects excess precision", async ({
  page,
}) => {
  await page.getByLabel("Description", { exact: true }).fill("Office supplies");
  await page.getByLabel("Amount THB", { exact: true }).fill("100.00");
  await page.getByRole("radio", { name: "Exact amounts" }).check();
  await page.getByLabel("Share for alice", { exact: true }).fill("50.00");
  await page.getByLabel("Share for bob", { exact: true }).fill("49.99");
  await expect(page.locator(".split-summary strong")).toHaveText("0.01 THB");
  await expect(
    page.getByRole("button", { name: "Save expense" }),
  ).toBeDisabled();
  await page.getByLabel("Share for bob", { exact: true }).fill("50.00");
  await page.getByLabel("Share for carol", { exact: true }).fill("0.005");
  await expect(
    page.getByRole("button", { name: "Save expense" }),
  ).toBeDisabled();
  await page.getByLabel("Share for carol", { exact: true }).fill("0.00");
  await expect(
    page.getByRole("button", { name: "Save expense" }),
  ).toBeEnabled();
  await page.getByRole("button", { name: "Save expense" }).click();
  await expect(
    page.getByRole("heading", { name: "Office supplies" }),
  ).toBeVisible();
  await expect(page.locator(".balance-amount strong")).toHaveText([
    "+50.00",
    "-50.00",
    "0.00",
  ]);
});

test("lost response retries the same key and creates only one expense", async ({
  page,
  request,
}) => {
  const keys: string[] = [];
  let first = true;
  await page.route(/\/groups\/1\/expenses$/, async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    keys.push(route.request().headers()["idempotency-key"]);
    if (first) {
      first = false;
      const result = await route.fetch();
      expect(result.status()).toBe(201);
      await route.abort("failed");
    } else await route.continue();
  });
  await page
    .getByLabel("Description", { exact: true })
    .fill("Safe retry dinner");
  await page.getByLabel("Amount THB", { exact: true }).fill("100");
  await page.getByRole("button", { name: "Save expense" }).click();
  await expect(
    page.getByRole("button", { name: "Retry expense" }),
  ).toBeVisible();
  await expect(page.getByLabel("Description", { exact: true })).toBeDisabled();
  await expect(page.getByLabel("Viewing as")).toBeDisabled();
  await page.getByRole("button", { name: "Retry expense" }).click();
  await expect(
    page.getByRole("heading", { name: "Safe retry dinner" }),
  ).toBeVisible();
  expect(keys).toHaveLength(2);
  expect(keys[0]).toBe(keys[1]);
  const expenses = await request.get(`${API}/groups/1/expenses`, {
    headers: { "X-User": "alice" },
  });
  expect(
    (await expenses.json()).filter(
      (e: { description: string }) => e.description === "Safe retry dinner",
    ),
  ).toHaveLength(1);
});

test("plain API error preserves form input and user switch clears stale groups", async ({
  page,
}) => {
  await page.route(/\/groups\/1\/expenses$/, async (route) => {
    if (route.request().method() === "POST")
      await route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({
          error: {
            code: "not_group_member",
            message: "Not a member of this group",
            details: [],
          },
        }),
      });
    else await route.continue();
  });
  await page.getByLabel("Description", { exact: true }).fill("Keep my input");
  await page.getByLabel("Amount THB", { exact: true }).fill("25");
  await page.getByRole("button", { name: "Save expense" }).click();
  await expect(page.getByRole("region", { name: "Add an expense" }).getByRole("alert")).toContainText(
    "Not a member of this group",
  );
  await expect(page.getByLabel("Description", { exact: true })).toHaveValue(
    "Keep my input",
  );
  await expect(page.getByLabel("Viewing as")).toBeEnabled();
  await page.getByLabel("Viewing as").selectOption("bob");
  await page.getByLabel("Viewing as").selectOption("dan");
  await expect(page.getByLabel("Your group")).toHaveValue("2");
  await expect(page.getByLabel("Your group").locator("option")).toHaveText([
    "Office lunch",
  ]);
  await expect(page.getByLabel("Description", { exact: true })).toHaveValue("");
  await expect(page.locator(".balance-person")).toContainText(["bob", "dan"]);
});
