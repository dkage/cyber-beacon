import { currentTranslator, setLanguage, type Translator } from './i18n';
import type { Settings } from './types';

const errorMessages = {
	invalid_timezone: 'invalidTimezone',
	invalid_work_hours: 'invalidWorkHours',
	invalid_choice: 'invalidChoice',
	required: 'requiredField',
	blank: 'requiredField',
	invalid: 'invalidInput',
	min_value: 'invalidInput',
	max_value: 'invalidInput',
	invalid_login: 'invalidLogin',
	email_password_mismatch: 'invalidLogin',
	unknown_email: 'invalidLogin',
	invalid_email: 'invalidEmail',
	pair_code_invalid: 'pairCodeInvalid',
	choose_worksheet_source: 'chooseWorksheetSource',
	choose_active_calendar: 'chooseActiveCalendar',
	source_record_mismatch: 'sourceRecordMismatch',
	invalid_github_issue: 'invalidGithubIssue',
	source_issue_mismatch: 'sourceIssueMismatch',
	connection_expired: 'connectionExpired',
	invalid_parent_task: 'invalidParentTask',
	cyclic_subtask: 'cyclicSubtask',
	timer_completed_task: 'timerCompletedTask',
	timer_already_running: 'timerAlreadyRunning',
	unknown_provider: 'unknownProvider',
	provider_error: 'providerProblem',
	reconnect_provider: 'reconnectProvider',
	not_found: 'notFound',
	throttled: 'throttled',
	conflict: 'conflict',
	secure_session: 'secureSessionFailed',
	unreadable_response: 'unreadableResponse'
} as const;

type PlainMessage =
	| (typeof errorMessages)[keyof typeof errorMessages]
	| 'accessDenied'
	| 'taskStale'
	| 'networkError'
	| 'requestFailed'
	| 'serverUnavailable'
	| 'secureTokenMissing'
	| 'untrustedPath'
	| 'invalidRedirect'
	| 'displayExpired'
	| 'pairExpired'
	| 'invalidSummary'
	| 'invalidPairCode'
	| 'invalidPairStatus'
	| 'consentDenied';

export class LocalizedError extends Error {
	constructor(readonly key: PlainMessage) {
		super(currentTranslator()(key));
	}
}

function allauthCode(body: unknown): string | undefined {
	if (!body || typeof body !== 'object' || !('errors' in body) || !Array.isArray(body.errors))
		return;
	for (const entry of body.errors as unknown[]) {
		if (entry && typeof entry === 'object' && 'code' in entry && typeof entry.code === 'string') {
			if (entry.code === 'invalid' && 'param' in entry && entry.param === 'email')
				return 'invalid_email';
			return entry.code;
		}
	}
}

function errorKey(status: number, code?: string): PlainMessage {
	if (status === 412) return 'taskStale';
	if (code && Object.hasOwn(errorMessages, code))
		return errorMessages[code as keyof typeof errorMessages];
	if (status === 401 || status === 403) return 'accessDenied';
	if (status === 404) return 'notFound';
	if (status === 409) return 'conflict';
	if (status === 429) return 'throttled';
	if (status === 400) return 'invalidInput';
	if (status >= 500) return 'serverUnavailable';
	return 'requestFailed';
}

export class ApiError extends LocalizedError {
	constructor(
		public status: number,
		public fields: unknown,
		code?: string
	) {
		super(errorKey(status, code ?? allauthCode(fields)));
	}
}
let csrfToken: string | undefined;
let languageRevision = 0;
export function clearSession() {
	csrfToken = undefined;
	languageRevision++;
}
export async function csrf(fetcher: typeof fetch = fetch): Promise<string> {
	const response = await fetcher('/api/v1/csrf/', { credentials: 'same-origin' });
	if (!response.ok) throw new ApiError(response.status, null, 'secure_session');
	const value: unknown = await response.json();
	csrfToken = undefined;
	if (
		!value ||
		typeof value !== 'object' ||
		!('csrf_token' in value) ||
		typeof value.csrf_token !== 'string' ||
		!value.csrf_token
	) {
		throw new LocalizedError('secureTokenMissing');
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
		throw new LocalizedError('untrustedPath');
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
		throw new ApiError(response.status, null, 'unreadable_response');
	}
	if (!response.ok)
		throw new ApiError(
			response.status,
			body,
			response.headers.get('X-Beacon-Error-Code') ?? undefined
		);
	return body as T;
}
export function write<T>(path: string, body?: unknown, method = 'POST', version?: number) {
	return api<T>(path, {
		method,
		body: body === undefined ? undefined : JSON.stringify(body),
		headers: version === undefined ? undefined : { 'If-Match': `"${version}"` }
	});
}
export function fieldErrorProps(error: unknown, field: string, descriptionId: string) {
	if (
		error instanceof ApiError &&
		error.fields !== null &&
		typeof error.fields === 'object' &&
		Object.hasOwn(error.fields, field)
	) {
		return { 'aria-invalid': true, 'aria-describedby': descriptionId };
	}
	return {};
}

export function message(error: unknown, translate: Translator = currentTranslator()) {
	return translate(error instanceof LocalizedError ? error.key : 'networkError');
}

const recordedProviderErrors = {
	'Reconnect this Provider account.': 'reconnectProvider',
	'Reconnect this Provider before continuing.': 'reconnectProvider',
	'Reconnect this Provider or check its resource permissions.': 'reconnectProvider',
	'Provider rate limit reached. Try again shortly.': 'throttled',
	'GitHub rate limit reached. Try again shortly.': 'throttled',
	'Calendar refresh failed. Previous data has been kept.': 'refreshKeptData',
	'Calendar refresh window expired. Previous data has been kept.': 'refreshWindowExpired',
	'Calendar is too large for one refresh. Narrow the resource or retry later.': 'refreshTooLarge'
} as const;

export function providerStatusMessage(detail: string, translate: Translator) {
	const key = Object.hasOwn(recordedProviderErrors, detail)
		? recordedProviderErrors[detail as keyof typeof recordedProviderErrors]
		: 'providerProblem';
	return translate(key);
}

export async function syncLanguage() {
	try {
		await readSettings();
	} catch {
		// Account language will be fetched at sign-in or the next authenticated reload.
	}
}

export async function readSettings() {
	const revision = languageRevision;
	const settings = await api<Settings>('/api/v1/settings/');
	if (revision === languageRevision) setLanguage(settings.language);
	return settings;
}

export function applySavedLanguage(value: Settings['language']) {
	languageRevision++;
	setLanguage(value);
}
