import { test, expect } from '@playwright/test';

test('task automation panel executes file task and shows history', async ({ page }) => {
  await page.goto('/chat/');
  await page.evaluate(() => {
    localStorage.setItem('user_id', '00000000-0000-0000-0000-000000000001');
  });
  await page.reload();

  await expect(page.getByRole('heading', { name: 'タスク実行' })).toBeVisible();
  await page.locator('#task-input').fill('ファイル /tmp/kyosist-playwright.txt を作成して内容: Hello');
  await page.locator('#task-execute-btn').click();

  await expect(page.locator('#task-result')).toContainText('ファイルを作成しました');
  await expect(page.locator('#history-list .history-item').first()).toContainText('file');
});

test('task automation panel blocks traversal and can save a skill', async ({ page }) => {
  await page.goto('/chat/');
  await page.evaluate(() => {
    localStorage.setItem('user_id', '00000000-0000-0000-0000-000000000002');
  });
  await page.reload();

  await page.locator('#task-input').fill('ファイル ../../../etc/passwd を読んで');
  await page.locator('#task-execute-btn').click();
  await expect(page.locator('#task-result')).toContainText('パストラバーサル');

  await page.locator('#task-input').fill('コマンド実行: npm --version');
  await page.locator('#task-save-skill-btn').click();
  await expect(page.locator('#skill-list .history-item').first()).toContainText('コマンド実行');
});
