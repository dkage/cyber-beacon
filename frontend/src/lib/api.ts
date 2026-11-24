export class ApiError extends Error {
	constructor(
		public status: number,
		public fields: unknown
	) {
		super(
			status === 412
				? 'This Task changed elsewhere. Your draft is kept; refresh and retry.'
				: status === 403
					? 'Access denied or your session changed. Sign in again, then retry.'
					: describe(fields)
		);
	}
}
function describe(value: unknown): string {
	if (typeof value === 'string') return value;
	if (Array.isArray(value)) return value.map(describe).join(' ');
	if (value && typeof value === 'object')
		return Object.entries(value)
			.map(([key, item]) => `${key === 'detail' ? '' : key + ': '}${describe(item)}`)
			.join(' ');
	return 'The request failed. Please try again.';
}
let csrfToken: string | undefined;
export function clearSession() {
	csrfToken = undefined;
}
export async function csrf(fetcher: typeof fetch = fetch): Promise<string> {
	const response = await fetcher('/api/v1/csrf/', { credentials: 'same-origin' });
	if (!response.ok) throw new ApiError(response.status, 'Could not initialize a secure session.');
	const value: unknown = await response.json();
	csrfToken = undefined;
	if (
		!value ||
		typeof value !== 'object' ||
		!('csrf_token' in value) ||
		typeof value.csrf_token !== 'string' ||
		!value.csrf_token
	) {
		throw new Error('The server did not return a CSRF token.');
	}
	csrfToken = value.csrf_token;
	return csrfToken;
}
export async function api<T>(
	path: string,
	options: RequestInit = {},
	fetcher: typeof fetch = fetch
): Promise<T> {
	if (!path.startsWith('/api/v1/') && !path.startsWith('/_allauth/'))
		throw new Error('API requests must use a trusted same-origin path.');
	const headers = new Headers(options.headers);
	if (!['GET', 'HEAD', 'OPTIONS'].includes((options.method ?? 'GET').toUpperCase())) {
		headers.set('X-CSRFToken', csrfToken ?? (await csrf(fetcher)));
		if (options.body) headers.set('Content-Type', 'application/json');
	}
	headers.set('Accept', 'application/json');
	const response = await fetcher(path, { ...options, headers, credentials: 'same-origin' });
	if (response.status === 204) return undefined as T;
	let body: unknown;
	try {
		body = await response.json();
	} catch {
		throw new ApiError(response.status, 'The server returned an unreadable response.');
	}
	if (!response.ok) throw new ApiError(response.status, body);
	return body as T;
}
export function write<T>(path: string, body?: unknown, method = 'POST', version?: number) {
	return api<T>(path, {
		method,
		body: body === undefined ? undefined : JSON.stringify(body),
		headers: version === undefined ? undefined : { 'If-Match': `"${version}"` }
	});
}
export function message(error: unknown) {
	return error instanceof Error ? error.message : 'Connection failed. Please try again.';
}
