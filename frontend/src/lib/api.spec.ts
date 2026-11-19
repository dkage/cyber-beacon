import { afterEach, describe, expect, it, vi } from 'vitest';
import { api, ApiError, clearSession } from './api';

afterEach(clearSession);
describe('API transport', () => {
	it('bootstraps CSRF and sends cookies and preconditions to the same origin', async () => {
		const fetcher = vi.fn<typeof fetch>();
		fetcher.mockResolvedValueOnce(new Response(JSON.stringify({ csrf_token: 'masked' })));
		fetcher.mockResolvedValueOnce(new Response(JSON.stringify({ id: 'task' })));
		await api(
			'/api/v1/tasks/id/',
			{ method: 'PATCH', body: '{}', headers: { 'If-Match': '"2"' } },
			fetcher
		);
		const request = fetcher.mock.calls[1][1]!;
		expect(new Headers(request.headers).get('X-CSRFToken')).toBe('masked');
		expect(new Headers(request.headers).get('If-Match')).toBe('"2"');
		expect(request.credentials).toBe('same-origin');
	});
	it('does not treat non-JSON failures or stale writes as success', async () => {
		const fetcher = vi
			.fn<typeof fetch>()
			.mockResolvedValue(new Response('<h1>Down</h1>', { status: 502 }));
		await expect(api('/api/v1/day/', {}, fetcher)).rejects.toBeInstanceOf(ApiError);
		fetcher.mockResolvedValue(new Response(JSON.stringify({ detail: 'Stale' }), { status: 412 }));
		await expect(api('/api/v1/day/', {}, fetcher)).rejects.toThrow('Your draft is kept');
	});
	it('never sends CSRF to an external URL', async () => {
		const fetcher = vi.fn<typeof fetch>();
		await expect(api('https://attacker.test', { method: 'POST' }, fetcher)).rejects.toThrow(
			'trusted'
		);
		expect(fetcher).not.toHaveBeenCalled();
	});
});
