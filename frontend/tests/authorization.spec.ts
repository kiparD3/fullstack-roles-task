import { expect, type TestRole, test } from "./fixtures/rbac"
import { logInUser } from "./utils/user"

for (const role of ["admin", "manager", "member", "legacy"] as TestRole[]) {
  test.describe(`${role} authorization`, () => {
    test.use({ role })
    test.beforeEach(async ({ page, account }) => {
      await logInUser(page, account.email, account.password)
    })
    test("navigation, direct routes and user controls", async ({ page }) => {
      const privileged = role === "admin" || role === "manager"
      await expect(
        page.getByRole("link", { name: "Admin", exact: true }),
      ).toHaveCount(privileged ? 1 : 0)
      await expect(
        page.getByRole("link", { name: "Metrics", exact: true }),
      ).toHaveCount(privileged ? 1 : 0)
      await page.goto("/admin")
      if (privileged) {
        await expect(
          page.getByRole("heading", { name: "Users", exact: true }),
        ).toBeVisible()
        await expect(
          page.getByRole("button", { name: "Add User", exact: true }),
        ).toHaveCount(role === "admin" ? 1 : 0)
        if (role === "manager")
          await expect(page.getByRole("table").getByRole("button")).toHaveCount(
            0,
          )
      } else {
        await expect(
          page.getByRole("heading", { name: "Access denied" }),
        ).toBeVisible()
        await expect(page.getByRole("table")).toHaveCount(0)
      }
      await page.goto("/metrics")
      await expect(
        page.getByRole("heading", {
          name: privileged ? "Metrics" : "Access denied",
          exact: true,
        }),
      ).toBeVisible()
    })
    test("can edit own profile without privilege fields", async ({ page }) => {
      await page.goto("/settings")
      await page.getByRole("button", { name: "Edit", exact: true }).click()
      await expect(page.getByLabel("Role", { exact: true })).toHaveCount(0)
      await expect(page.getByLabel("Is superuser?")).toHaveCount(0)
      await page.getByLabel("Full name").fill(`Updated ${role}`)
      await page.getByRole("button", { name: "Save", exact: true }).click()
      await expect(page.getByText("User updated successfully")).toBeVisible()
    })
  })
}

test.describe("permission failure states", () => {
  test.use({ role: "manager" })
  test.beforeEach(async ({ page, account }) => {
    await logInUser(page, account.email, account.password)
  })
  test("403 from a protected API shows forbidden without logging out", async ({
    page,
  }) => {
    await page.route("**/api/v1/metrics/", (route) =>
      route.fulfill({ status: 403, json: { detail: "Permission revoked" } }),
    )
    await page.goto("/metrics")
    await expect(
      page.getByRole("heading", { name: "Access denied" }),
    ).toBeVisible()
    await expect(page).toHaveURL(/\/metrics$/)
    expect(
      await page.evaluate(() => localStorage.getItem("access_token")),
    ).toBeTruthy()
  })
  test("user list 403 does not reveal stale user data", async ({ page }) => {
    await page.route("**/api/v1/users/?*", (route) =>
      route.fulfill({ status: 403, json: { detail: "Permission revoked" } }),
    )
    await page.goto("/admin")
    await expect(
      page.getByRole("heading", { name: "Access denied" }),
    ).toBeVisible()
    await expect(page.getByRole("table")).toHaveCount(0)
  })
  test("current user failure hides protected content", async ({ page }) => {
    await page.route("**/api/v1/users/me", (route) =>
      route.fulfill({ status: 500, json: { detail: "Unavailable" } }),
    )
    await page.goto("/admin")
    await expect(page.getByText("Unable to verify your access.")).toBeVisible()
    await expect(page.getByRole("table")).toHaveCount(0)
    await expect(page.getByRole("button", { name: "Add User" })).toHaveCount(0)
  })
  test("loading identity does not flash protected content", async ({
    page,
  }) => {
    let release!: () => void
    const pending = new Promise<void>((resolve) => {
      release = resolve
    })
    await page.route("**/api/v1/users/me", async (route) => {
      await pending
      await route.continue()
    })
    try {
      await page.goto("/admin")
      await expect(page.getByRole("status")).toHaveText("Checking access…")
      await expect(page.getByRole("table")).toHaveCount(0)
      await expect(
        page.getByRole("link", { name: "Admin", exact: true }),
      ).toHaveCount(0)
    } finally {
      release()
    }
    await expect(page.getByRole("table")).toBeVisible()
  })
  test("expired authentication redirects to login", async ({ page }) => {
    await page.route("**/api/v1/users/me", (route) =>
      route.fulfill({ status: 401, json: { detail: "Expired" } }),
    )
    await page.goto("/admin")
    await expect(page).toHaveURL(/\/login$/)
    expect(
      await page.evaluate(() => localStorage.getItem("access_token")),
    ).toBeNull()
  })
})

test("anonymous direct navigation requires login", async ({ page }) => {
  await page.goto("/metrics")
  await expect(page).toHaveURL(/\/login$/)
})

test("logout and lower-privilege login clear admin capabilities", async ({
  page,
  account,
}) => {
  const { firstSuperuser, firstSuperuserPassword } = await import("./config")
  await logInUser(page, firstSuperuser, firstSuperuserPassword)
  await expect(
    page.getByRole("link", { name: "Admin", exact: true }),
  ).toBeVisible()
  await page.getByTestId("user-menu").click()
  await page.getByRole("menuitem", { name: "Log Out" }).click()
  await expect(page).toHaveURL(/\/login$/)
  await logInUser(page, account.email, account.password)
  await expect(
    page.getByRole("link", { name: "Admin", exact: true }),
  ).toHaveCount(0)
  await page.goto("/admin")
  await expect(
    page.getByRole("heading", { name: "Access denied" }),
  ).toBeVisible()
})

test.describe("admin role assignment", () => {
  test.use({ role: "member" })
  test("admin can promote a member through the role selector", async ({
    page,
    account,
  }) => {
    const { firstSuperuser, firstSuperuserPassword } = await import("./config")
    await logInUser(page, firstSuperuser, firstSuperuserPassword)
    await page.goto("/admin")
    const row = page.getByRole("row").filter({ hasText: account.email })
    await row.getByRole("button").click()
    await page.getByRole("menuitem", { name: "Edit User" }).click()
    await page.getByLabel("Role", { exact: true }).selectOption("manager")
    await page.getByRole("button", { name: "Save", exact: true }).click()
    await expect(page.getByText("User updated successfully")).toBeVisible()
    await expect(row.getByText("Manager", { exact: true })).toBeVisible()
    await page.getByTestId("user-menu").click()
    await page.getByRole("menuitem", { name: "Log Out" }).click()
    await expect(page).toHaveURL(/\/login$/)
    await logInUser(page, account.email, account.password)
    await page.goto("/metrics")
    await expect(
      page.getByRole("heading", { name: "Metrics", exact: true }),
    ).toBeVisible()
  })
})
