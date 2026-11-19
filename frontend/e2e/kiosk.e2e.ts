import { expect, test } from '@playwright/test';
import type { components } from '../src/lib/schema';

test('pair a read-only display, survive outage with stale data, and clear on revocation', async ({
	browser,
	page
}) => {
	await page.goto('/login');
	await page.getByLabel('Email', { exact: true }).fill('browser@example.test');
	await page.getByLabel('Password', { exact: true }).fill('test-browser-password-982');
	test.setTimeout(90000);
	await page.getByRole('button', { name: 'Sign in', exact: true }).click();
	await expect(page.getByRole('heading', { name: 'Your day' })).toBeVisible();
	await page.getByRole('link', { name: 'Settings', exact: false }).click();
	const deviceContext = await browser.newContext();
	const device = await deviceContext.newPage();
	await device.goto('/kiosk');
	const code = device.locator('.pairing h2');
	await expect(code).toHaveText(/^[A-Z2-9]{8}$/);
	await page.getByLabel('Pairing code', { exact: true }).fill((await code.textContent())!);
	await page.getByRole('button', { name: 'Approve display', exact: true }).click();
	await expect(device.getByRole('heading', { name: 'Design review' })).toBeVisible({
		timeout: 25000
	});
	await device.evaluate(async () => {
		await navigator.serviceWorker.ready;
	});
	await deviceContext.setOffline(true);
	await device.reload({ waitUntil: 'domcontentloaded' });
	await expect(device.getByText(/STALE · Last successful/)).toBeVisible({ timeout: 25000 });
	await expect(device.getByRole('heading', { name: 'Design review' })).toBeVisible();
	const cachedUrls = await device.evaluate(async () => {
		const urls: string[] = [];
		for (const name of await caches.keys())
			for (const request of await (await caches.open(name)).keys()) urls.push(request.url);
		return urls;
	});
	expect(cachedUrls.some((url) => url.includes('/api/'))).toBe(false);
	await deviceContext.setOffline(false);
	await page.getByRole('button', { name: 'Revoke display', exact: true }).first().click();

	await expect(device.locator('.pairing')).toBeVisible({ timeout: 45000 });
	await expect(device.getByRole('heading', { name: 'Design review' })).toHaveCount(0);
	expect(await device.evaluate(() => localStorage.getItem('beacon-summary'))).toBeNull();
	await deviceContext.close();
});

test('discard an invalid cached summary and keep the last good summary after a bad refresh', async ({
	page
}) => {
	const validSummary = {
		date: '2026-11-19',
		timezone: 'UTC',
		date_order: 'ymd',
		date_separator: '-',
		fetched_at: '2026-11-19T12:00:00Z',
		tasks: [],
		events: [],
		calendars: [],
		briefing: 'Last good briefing'
	} satisfies components['schemas']['KioskSummary'];
	let payload: unknown = {};
	await page.route('**/api/v1/kiosk/summary/', (route) => route.fulfill({ json: payload }));
	await page.addInitScript(() => {
		if (localStorage.getItem('beacon-device')) return;
		localStorage.setItem('beacon-device', 'browser-fixture');
		localStorage.setItem('beacon-summary', '{}');
	});

	await page.goto('/kiosk');
	await expect(page.getByRole('alert')).toHaveText('The server returned an invalid day summary.');
	expect(await page.evaluate(() => localStorage.getItem('beacon-summary'))).toBeNull();

	payload = validSummary;
	await page.reload();
	await expect(page.getByText('Last good briefing')).toBeVisible();
	await expect(page.getByText(/· Connected$/)).toBeVisible();

	payload = { ...validSummary, tasks: [null] };
	await page.reload();
	await expect(page.getByRole('status')).toContainText(
		'The server returned an invalid day summary.'
	);
	await expect(page.getByText('Last good briefing')).toBeVisible();
	expect(await page.evaluate(() => localStorage.getItem('beacon-summary'))).toBe(
		JSON.stringify(validSummary)
	);
});
