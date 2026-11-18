import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => {
	await page.goto('/login');
	await page.getByLabel('Email', { exact: true }).fill('browser@example.test');
	await page.getByLabel('Password', { exact: true }).fill('test-browser-password-982');
	await page.getByRole('button', { name: 'Sign in', exact: true }).click();
	await expect(page.getByRole('heading', { name: 'Your day' })).toBeVisible();
});

test('a real authenticated day: create, edit, order, time, complete, trash and restore', async ({
	page
}) => {
	await expect(page.getByRole('heading', { name: 'Design review' })).toBeVisible();
	await page.getByRole('button', { name: 'New Task', exact: true }).click();
	await page.getByLabel('Title', { exact: true }).fill('Prepare launch');
	await page.getByLabel('Estimate (minutes)', { exact: true }).fill('30');
	await page.getByRole('button', { name: 'Save Task', exact: true }).click();
	await expect(page.getByRole('button', { name: 'Prepare launch', exact: true })).toBeVisible();
	await page.getByRole('button', { name: 'New Task', exact: true }).click();
	await page.getByLabel('Title', { exact: true }).fill('Write release notes');
	await page.getByRole('button', { name: 'Save Task', exact: true }).click();
	await page.getByRole('button', { name: 'Move Write release notes up', exact: true }).click();
	await expect(page.locator('.task-list li').first()).toContainText('Write release notes');
	await page.screenshot({ path: 'test-results/today-desktop.png', fullPage: true });
	await page.getByRole('button', { name: 'Start timer for Prepare launch', exact: true }).click();
	await expect(page.getByRole('button', { name: 'Stop timer', exact: true })).toBeVisible();
	await page.reload();
	await expect(page.getByRole('button', { name: 'Stop timer', exact: true })).toBeVisible();
	await page.getByRole('button', { name: 'Stop timer', exact: true }).click();
	await page.getByRole('button', { name: 'Prepare launch', exact: true }).click();
	await page.getByLabel('Notes', { exact: true }).fill('Keep the release small.');
	await page.getByRole('button', { name: 'Save Task', exact: true }).click();
	await page.getByRole('button', { name: 'Complete Prepare launch', exact: true }).click();
	await expect(
		page.getByRole('button', { name: 'Reopen Prepare launch', exact: true })
	).toHaveAttribute('aria-pressed', 'true');
	await page.getByRole('button', { name: 'Trash Prepare launch', exact: true }).click();
	await page.getByRole('link', { name: 'Settings', exact: false }).click();
	await page.getByRole('button', { name: 'Restore Task', exact: true }).click();
	await page.getByRole('link', { name: 'Today', exact: false }).first().click();
	await expect(page.getByRole('button', { name: 'Prepare launch', exact: true })).toBeVisible();
	const rejected = await page.request.post('/api/v1/tasks/', { data: { title: 'No CSRF' } });
	expect(rejected.status()).toBe(403);
	await page.getByRole('button', { name: 'Sign out', exact: true }).click();
	await expect(page).toHaveURL(/\/login$/);
});

test('the login screen hides app navigation, including with a trailing slash', async ({ page }) => {
	await page.goto('/login/');
	await expect(page.getByRole('heading', { name: 'Welcome back.' })).toBeVisible();
	await expect(page.getByRole('navigation', { name: 'Main navigation' })).toHaveCount(0);
});

test('date preferences persist and format the planner day', async ({ page }) => {
	await page.locator('nav').getByRole('link', { name: 'Settings' }).click();
	await page.getByLabel('Date order').selectOption('dmy');
	await page.getByLabel('Date separator').selectOption('/');
	await page.getByRole('button', { name: 'Save preferences' }).click();
	await expect(page.getByRole('status')).toContainText('Preferences saved.');
	await page.locator('nav').getByRole('link', { name: 'Today' }).click();
	const day = await (await page.request.get('/api/v1/day/')).json();
	const [year, month, date] = day.date.split('-');
	await expect(page.locator('.section-heading .muted').first()).toContainText(
		`${date}/${month}/${year}`
	);
	await page.reload();
	await page.locator('nav').getByRole('link', { name: 'Settings' }).click();
	await expect(page.getByLabel('Date order')).toHaveValue('dmy');
	await expect(page.getByLabel('Date separator')).toHaveValue('/');
});

test('static deep links, mobile layout and retained rejected drafts', async ({ page }) => {
	await page.setViewportSize({ width: 390, height: 844 });
	await page.goto('/today?date=2026-11-18');
	await page.reload();
	await page.getByRole('button', { name: 'New Task', exact: true }).click();
	await page.getByLabel('Title', { exact: true }).fill('Retain this draft');
	await page.route('**/api/v1/tasks/', async (route) => {
		if (route.request().method() === 'POST')
			await route.fulfill({
				status: 503,
				contentType: 'application/json',
				body: JSON.stringify({ detail: 'Temporarily unavailable' })
			});
		else await route.continue();
	});
	await page.getByRole('button', { name: 'Save Task', exact: true }).click();
	await expect(page.getByRole('alert')).toContainText('Temporarily unavailable');
	await expect(page.getByLabel('Title', { exact: true })).toHaveValue('Retain this draft');
	expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
		true
	);
});

test('a second client edit rejects stale saves and preserves the local draft', async ({ page }) => {
	await page.getByRole('button', { name: 'New Task', exact: true }).click();
	await page.getByLabel('Title', { exact: true }).fill('Concurrent work');
	await page.getByRole('button', { name: 'Save Task', exact: true }).click();
	await page.getByRole('button', { name: 'Concurrent work', exact: true }).click();
	await page.getByLabel('Title', { exact: true }).fill('My retained draft');
	const day = await (await page.request.get('/api/v1/day/')).json();
	const task = day.tasks.find((value: { title: string }) => value.title === 'Concurrent work');
	const csrf = await (await page.request.get('/api/v1/csrf/')).json();
	const changed = await page.request.patch(`/api/v1/tasks/${task.id}/`, {
		data: { notes: 'Changed in another client' },
		headers: { 'X-CSRFToken': csrf.csrf_token, 'If-Match': `"${task.version}"` }
	});
	expect(changed.status()).toBe(200);
	await page.getByRole('button', { name: 'Save Task', exact: true }).click();
	await expect(page.getByRole('alert')).toContainText('Latest version loaded');
	await expect(page.getByLabel('Title', { exact: true })).toHaveValue('My retained draft');
	await page.getByRole('button', { name: 'Save Task', exact: true }).click();
	await expect(page.getByRole('button', { name: 'My retained draft', exact: true })).toBeVisible();
	const saved = await (await page.request.get(`/api/v1/tasks/${task.id}/`)).json();
	expect(saved.notes).toBe('Changed in another client');
});
