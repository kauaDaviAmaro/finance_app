import { test, expect } from '@playwright/test'

test('unauthenticated user is redirected to login when accessing /scanner', async ({ page }) => {
  await page.goto('/scanner')
  await expect(page).toHaveURL(/.*login.*/)
})

test('FREE user is redirected to subscription when accessing /scanner', async ({ page }) => {
  // Inject a fake token to pass the auth check
  await page.addInitScript(() => {
    localStorage.setItem('token', 'fake.jwt.token')
  })

  // Mock /users/me to return a FREE user
  await page.route('**/users/me', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 1,
        email: 'free@example.com',
        username: 'free',
        role: 'USER',
      }),
    })
  })

  await page.goto('/scanner')
  // Should redirect to /subscription due to requiresPro guard
  await expect(page).toHaveURL(/.*subscription.*/)
})






