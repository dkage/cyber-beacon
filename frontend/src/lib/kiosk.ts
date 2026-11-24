import type { components } from './schema';
import { isLanguage } from './i18n';

export function isRecord(value: unknown): value is Record<string, unknown> {
	return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function isInstant(value: unknown): value is string {
	return typeof value === 'string' && Number.isFinite(Date.parse(value));
}

function isNullableInstant(value: unknown): value is string | null {
	return value === null || isInstant(value);
}

function isCalendarDate(value: unknown): value is string {
	return typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value);
}

function isTimeZone(value: unknown): value is string {
	if (typeof value !== 'string') return false;
	try {
		new Intl.DateTimeFormat(undefined, { timeZone: value });
		return true;
	} catch {
		return false;
	}
}

function isKeyedList(value: unknown, isValid: (item: Record<string, unknown>) => boolean): boolean {
	if (!Array.isArray(value)) return false;
	const ids = new Set<unknown>();
	return value.every((item: unknown) => {
		if (!isRecord(item) || !isValid(item) || ids.has(item.id)) return false;
		ids.add(item.id);
		return true;
	});
}

export function isKioskSummary(value: unknown): value is components['schemas']['KioskSummary'] {
	return (
		isRecord(value) &&
		isCalendarDate(value.date) &&
		(value.language === undefined || isLanguage(value.language)) &&
		isTimeZone(value.timezone) &&
		(value.date_order === 'ymd' || value.date_order === 'dmy' || value.date_order === 'mdy') &&
		(value.date_separator === '-' || value.date_separator === '/') &&
		isInstant(value.fetched_at) &&
		typeof value.briefing === 'string' &&
		isKeyedList(
			value.tasks,
			(task) =>
				typeof task.id === 'string' &&
				typeof task.title === 'string' &&
				isNullableInstant(task.completed_at) &&
				(task.estimated_minutes === null ||
					(typeof task.estimated_minutes === 'number' && Number.isFinite(task.estimated_minutes)))
		) &&
		isKeyedList(
			value.events,
			(event) =>
				typeof event.id === 'number' &&
				typeof event.title === 'string' &&
				isNullableInstant(event.starts_at) &&
				isNullableInstant(event.ends_at) &&
				(event.start_date === null || isCalendarDate(event.start_date)) &&
				(event.end_date === null || isCalendarDate(event.end_date))
		) &&
		isKeyedList(
			value.calendars,
			(calendar) =>
				typeof calendar.id === 'string' &&
				typeof calendar.label === 'string' &&
				typeof calendar.enabled === 'boolean' &&
				typeof calendar.last_error === 'string' &&
				isNullableInstant(calendar.last_succeeded_at)
		)
	);
}
