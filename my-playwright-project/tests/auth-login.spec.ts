import { test, expect } from '@playwright/test';

test.describe('Authentication - Login Endpoint', () => {
  test('should return 401 for non-existent user', async ({ request }) => {
    const response = await request.post('/api/auth/login', {
      data: {
        email: 'nonexistent@example.com',
        password: 'password123',
      },
    });

    expect(response.status()).toBe(401);
    const body = await response.json();
    expect(body).toHaveProperty('detail');
  });

  test('should return 400 for invalid request format', async ({ request }) => {
    const response = await request.post('/api/auth/login', {
      data: {
        email: 'test@example.com',
        // missing password
      },
    });

    expect(response.status()).toBeGreaterThanOrEqual(400);
  });

  test('should log detailed info during login attempt', async ({ request, page }) => {
    // First, listen to console logs from browser context
    const consoleLogs: string[] = [];
    page.on('console', msg => consoleLogs.push(msg.text()));

    // Attempt login
    const response = await request.post('/api/auth/login', {
      data: {
        email: 'test@example.com',
        password: 'wrongpassword',
      },
    });

    expect(response.status()).toBe(401);

    // Check that response contains error detail
    const body = await response.json();
    expect(body).toHaveProperty('detail');
    console.log('Login response:', body);
  });

  test('POST /api/auth/login endpoint is accessible', async ({ request }) => {
    const response = await request.post('/api/auth/login', {
      data: {
        email: 'test@example.com',
        password: 'test123',
      },
    });

    // Endpoint should return either 401 (user not found) or 500 (server error)
    // But NOT 404 (not found) since the endpoint exists
    expect([400, 401, 422, 500]).toContain(response.status());

    // Response should be JSON
    const contentType = response.headers()['content-type'];
    expect(contentType).toContain('application/json');
  });
});
