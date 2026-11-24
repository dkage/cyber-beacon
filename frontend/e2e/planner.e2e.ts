import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => {
	await page.goto('/login');
	await page.getByLabel('Email', { exact: true }).fill('browser@example.test');
	await page.getByLabel('Password', { exact: true }).fill('test-browser-password-982');
	await page.getByRole('button', { name: 'Sign in', exact: true }).click();
	await expect(page.getByRole('heading', { name: 'Your day' })).toBeVisible();
});

test('first-task creation opens a modal and the empty day fits a desktop viewport', async ({
	page
}) => {
	await page.setViewportSize({ width: 1366, height: 768 });
	const createFirstTask = page.getByRole('button', { name: 'Create your first Task' });
	await expect(createFirstTask).toBeVisible();
	expect(
		await page.evaluate(() => document.documentElement.scrollHeight <= window.innerHeight)
	).toBe(true);

	await createFirstTask.click();
	await expect(page.getByRole('dialog')).toBeVisible();
	await expect(page.getByLabel('Title', { exact: true })).toBeFocused();
	await page.getByRole('button', { name: 'Close editor' }).click();
	await expect(page.getByRole('dialog')).toHaveCount(0);
	await createFirstTask.click();
	await page.keyboard.press('Escape');
	await expect(page.getByRole('dialog')).toHaveCount(0);

	await createFirstTask.click();
	await page.getByLabel('Title', { exact: true }).fill('First task from the modal');
	await page.getByRole('button', { name: 'Save Task', exact: true }).click();
	const firstTask = page.getByRole('button', { name: 'First task from the modal', exact: true });
	await expect(firstTask).toBeVisible();
	await page.setViewportSize({ width: 390, height: 844 });
	await firstTask.click();
	const editor = page.getByRole('dialog');
	await expect(editor).toBeVisible();
	expect(await editor.evaluate((element) => element.clientHeight <= window.innerHeight)).toBe(true);
	expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
		true
	);
	await page.getByLabel('Do date', { exact: true }).fill('');
	await page.getByRole('button', { name: 'Save Task', exact: true }).click();
	await expect(firstTask).toHaveCount(0);
	const backlog = page.locator('details').filter({ hasText: 'Backlog' });
	await backlog.locator('summary').click();
	await expect(backlog.getByText('First task from the modal', { exact: true })).toBeVisible();
	await backlog.getByRole('button', { name: 'Edit Task' }).click();
	await expect(page.getByLabel('Do date', { exact: true })).toHaveValue('');
	await page.getByLabel('Title', { exact: true }).fill('Edited backlog task');
	await page.getByRole('button', { name: 'Save Task', exact: true }).click();
	await expect(backlog.getByText('Edited backlog task', { exact: true })).toBeVisible();
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
	await expect(page.getByText('Task restored.', { exact: true })).toBeVisible();
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

test('GitHub repository issues can be searched and explicitly imported', async ({ page }) => {
	const connectionId = '11111111-1111-4111-8111-111111111111';
	const mountId = '22222222-2222-4222-8222-222222222222';
	await page.route('**/api/v1/integrations/connections/', async (route) => {
		await route.fulfill({
			contentType: 'application/json',
			body: JSON.stringify([
				{
					id: connectionId,
					provider: 'github',
					label: 'danilo',
					status: 'active',
					last_error: '',
					mounts: [
						{
							id: mountId,
							connection: connectionId,
							external_id: 'acme/planner',
							label: 'acme/planner',
							enabled: true,
							last_succeeded_at: null,
							last_error: '',
							consecutive_failures: 0
						}
					]
				}
			])
		});
	});
	await page.route(`**/api/v1/integrations/mounts/${mountId}/browse/**`, async (route) => {
		const query = new URL(route.request().url()).searchParams.get('query');
		await route.fulfill({
			contentType: 'application/json',
			body: JSON.stringify({
				results: [
					{
						id: '12',
						title: query ? '#12 Fix parser regression' : '#12 Improve planner search',
						url: 'https://github.com/acme/planner/issues/12',
						imported_count: 0
					}
				],
				next_cursor: null
			})
		});
	});
	await page.route(`**/api/v1/integrations/mounts/${mountId}/import/`, async (route) => {
		expect(route.request().method()).toBe('POST');
		expect(route.request().postDataJSON()).toMatchObject({ external_id: '12' });
		await route.fulfill({ status: 201, contentType: 'application/json', body: '{}' });
	});
	await page.goto('/connections');
	await page.getByRole('button', { name: 'Browse issues', exact: true }).click();
	await expect(page.getByText('#12 Improve planner search')).toBeVisible();
	await page.getByLabel('Search issues').fill('parser');
	await page.getByRole('button', { name: 'Search issues', exact: true }).click();
	await expect(page.getByText('#12 Fix parser regression')).toBeVisible();
	await page.getByRole('button', { name: 'Import worksheet', exact: true }).click();
	await expect(page.getByRole('status')).toContainText('Imported “#12 Fix parser regression”');
	const dayResponse = await page.request.get('/api/v1/day/');
	const day = await dayResponse.json();
	day.tasks = [
		{
			source: {
				provider: 'github',
				url: 'https://github.com/acme/planner/issues/12',
				raw: {},
				imported_at: '2026-11-18T12:00:00Z'
			},
			id: '55555555-5555-4555-8555-555555555555',
			parent: null,
			title: '#12 Fix parser regression',
			notes: '',
			do_date: day.date,
			due_date: null,
			start_date: null,
			priority: null,
			estimated_minutes: null,
			position: 0,
			completed_at: null,
			version: 1,
			deleted_at: null,
			created_at: '2026-11-18T12:00:00Z',
			updated_at: '2026-11-18T12:00:00Z'
		}
	];
	await page.route('**/api/v1/day/**', async (route) => {
		await route.fulfill({ contentType: 'application/json', body: JSON.stringify(day) });
	});
	await page.goto('/today');
	await expect(page.getByText('↗ GitHub issue')).toBeVisible();
});

test('failed lookups can be retried without showing results from another selection', async ({
	page
}) => {
	const firstConnection = '11111111-1111-4111-8111-111111111111';
	const secondConnection = '33333333-3333-4333-8333-333333333333';
	const firstMount = '22222222-2222-4222-8222-222222222222';
	const secondMount = '44444444-4444-4444-8444-444444444444';
	const mount = (id: string, connection: string) => ({
		id,
		connection,
		external_id: 'acme/planner',
		label: 'acme/planner',
		enabled: true,
		last_succeeded_at: null,
		last_error: '',
		consecutive_failures: 0
	});
	await page.route('**/api/v1/integrations/connections/', async (route) => {
		await route.fulfill({
			contentType: 'application/json',
			body: JSON.stringify([
				{
					id: firstConnection,
					provider: 'github',
					label: 'Personal GitHub',
					status: 'active',
					last_error: '',
					mounts: [mount(firstMount, firstConnection)]
				},
				{
					id: secondConnection,
					provider: 'github',
					label: 'Work GitHub',
					status: 'active',
					last_error: '',
					mounts: [mount(secondMount, secondConnection)]
				}
			])
		});
	});
	let resourceSearches = 0;
	await page.route(
		`**/api/v1/integrations/connections/${firstConnection}/resources/**`,
		async (route) => {
			const query = new URL(route.request().url()).searchParams.get('query');
			if (query && ++resourceSearches === 1) {
				await route.fulfill({ status: 503, json: { detail: 'Resource search offline' } });
				return;
			}
			await route.fulfill({
				contentType: 'application/json',
				body: JSON.stringify({
					results: [{ id: 'acme/old', label: query ? 'acme/matched' : 'acme/old' }],
					next_cursor: null
				})
			});
		}
	);
	await page.route(
		`**/api/v1/integrations/connections/${secondConnection}/resources/**`,
		async (route) => {
			await route.fulfill({
				status: 503,
				contentType: 'application/json',
				body: '{"detail":"Offline"}'
			});
		}
	);
	let nextPageRequests = 0;
	await page.route(`**/api/v1/integrations/mounts/${firstMount}/browse/**`, async (route) => {
		const params = new URL(route.request().url()).searchParams;
		if (params.get('cursor')) {
			expect(params.get('query')).toBe('');
			if (++nextPageRequests === 1) {
				await route.fulfill({ status: 503, json: { detail: 'Next page offline' } });
				return;
			}
		}
		await route.fulfill({
			contentType: 'application/json',
			body: JSON.stringify({
				results: [
					{
						id: '12',
						title: params.get('cursor') ? '#12 Next issue' : '#12 Old account issue',
						url: '',
						imported_count: 0
					}
				],
				next_cursor: params.get('cursor') ? null : 'next'
			})
		});
	});
	await page.route(`**/api/v1/integrations/mounts/${secondMount}/browse/**`, async (route) => {
		await route.fulfill({
			status: 503,
			contentType: 'application/json',
			body: '{"detail":"Offline"}'
		});
	});
	await page.goto('/connections');
	const cards = page.locator('.connection-grid > section');
	await cards.nth(0).getByRole('button', { name: 'Choose resource' }).click();
	await expect(page.getByText('acme/old', { exact: true })).toBeVisible();
	await page.getByLabel('Search resources').fill('matched');
	const searchResources = page.getByRole('button', { name: 'Search', exact: true });
	await searchResources.click();
	await expect(page.getByRole('alert')).toContainText('The server is unavailable.');
	await searchResources.click();
	await expect(page.getByText('acme/matched', { exact: true })).toBeVisible();
	await cards.nth(1).getByRole('button', { name: 'Choose resource' }).click();
	await expect(page.getByText('acme/matched', { exact: true })).toHaveCount(0);
	await expect(page.getByRole('button', { name: 'Attach resource' })).toHaveCount(0);
	await expect(searchResources).toBeEnabled();
	await cards.nth(0).getByRole('button', { name: 'Browse issues' }).click();
	await expect(page.getByText('#12 Old account issue')).toBeVisible();
	await page.getByLabel('Search issues').fill('unsubmitted search');
	const nextRecords = page.getByRole('button', { name: 'Next records' });
	await nextRecords.click();
	await expect(page.getByRole('alert')).toContainText('The server is unavailable.');
	await nextRecords.click();
	await expect(page.getByText('#12 Next issue')).toBeVisible();
	await cards.nth(1).getByRole('button', { name: 'Browse issues' }).click();
	await expect(page.getByText('#12 Next issue')).toHaveCount(0);
	await expect(page.getByRole('button', { name: 'Import worksheet' })).toHaveCount(0);
	await expect(page.getByRole('button', { name: 'Search issues' })).toBeEnabled();
});

test('OAuth consent denial is shown on Connections', async ({ page }) => {
	await page.goto('/connections?error=consent-denied');
	await expect(page.getByRole('alert')).toContainText('Provider access was not granted');
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
	await expect(page.getByRole('alert')).toContainText('The server is unavailable.');
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
