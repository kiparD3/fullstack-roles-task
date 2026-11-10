import { test as base, expect } from "@playwright/test"
import { firstSuperuser, firstSuperuserPassword } from "../config"

export type TestRole = "admin" | "manager" | "member" | "legacy"
type Account = { id: string; email: string; password: string; token: string }
type Fixtures = { account: Account; role: TestRole }
const api = process.env.VITE_API_URL!

export const test = base.extend<Fixtures>({
  role: ["member", { option: true }],
  storageState: { cookies: [], origins: [] },
  account: async ({ request, role }, use) => {
    const auth = await request.post(`${api}/api/v1/login/access-token`, {
      form: { username: firstSuperuser, password: firstSuperuserPassword },
    })
    expect(auth.ok()).toBeTruthy()
    const headers = {
      Authorization: `Bearer ${(await auth.json()).access_token}`,
    }
    const email = `rbac-${crypto.randomUUID()}@example.com`
    const password = "Test-password-123!"
    const response = await request.post(`${api}/api/v1/users/`, {
      headers,
      data: {
        email,
        password,
        role:
          role === "legacy" ? null : role === "manager" ? "manager" : "member",
        is_superuser: role === "admin",
      },
    })
    expect(response.ok()).toBeTruthy()
    const { id } = await response.json()
    const login = await request.post(`${api}/api/v1/login/access-token`, {
      form: { username: email, password },
    })
    expect(login.ok()).toBeTruthy()
    await use({ id, email, password, token: (await login.json()).access_token })
    const deleted = await request.delete(`${api}/api/v1/users/${id}`, {
      headers,
    })
    expect(deleted.ok()).toBeTruthy()
  },
})
export { expect }
