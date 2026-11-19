import { currentTranslator, defaultLanguage, type Language, type Translator } from './i18n';

export type DateOrder = 'ymd' | 'dmy' | 'mdy';
export type DateSeparator = '-' | '/';

export function formatDate(value: string, order: DateOrder, separator: DateSeparator): string {
	const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
	if (!match) return value;
	const [, year, month, day] = match;
	const parts = { ymd: [year, month, day], dmy: [day, month, year], mdy: [month, day, year] };
	return parts[order].join(separator);
}

export function formatDateTime(
	value: string,
	timezone: string,
	order: DateOrder,
	separator: DateSeparator,
	language: Language = defaultLanguage
): string {
	const instant = new Date(value);
	const date = formatDateInTimezone(value, timezone, order, separator);
	const time = new Intl.DateTimeFormat(language, {
		timeZone: timezone,
		hour: '2-digit',
		minute: '2-digit'
	}).format(instant);
	return `${date} ${time}`;
}

export function formatDateInTimezone(
	value: string,
	timezone: string,
	order: DateOrder,
	separator: DateSeparator
): string {
	const instant = new Date(value);
	const parts = new Intl.DateTimeFormat('en-US', {
		timeZone: timezone,
		year: 'numeric',
		month: '2-digit',
		day: '2-digit'
	}).formatToParts(instant);
	const part = (name: string) => parts.find((value) => value.type === name)?.value ?? '';
	return formatDate(`${part('year')}-${part('month')}-${part('day')}`, order, separator);
}

export function minutes(value: number, translate: Translator = currentTranslator()): string {
	const sign = value < 0 ? '−' : '';
	const absolute = Math.abs(Math.round(value));
	const hours = Math.floor(absolute / 60);
	const minutes = absolute % 60;
	return (
		sign +
		(hours
			? translate('durationHours', { hours, minutes })
			: translate('durationMinutes', { minutes }))
	);
}
export function localDate(
	now = new Date(),
	timezone = Intl.DateTimeFormat().resolvedOptions().timeZone
) {
	const parts = new Intl.DateTimeFormat('en-US', {
		timeZone: timezone,
		year: 'numeric',
		month: '2-digit',
		day: '2-digit'
	}).formatToParts(now);
	const part = (name: string) => parts.find((value) => value.type === name)?.value;
	return `${part('year')}-${part('month')}-${part('day')}`;
}
export function clock(instant: string, timezone: string, language: Language = defaultLanguage) {
	return new Intl.DateTimeFormat(language, {
		timeZone: timezone,
		hour: '2-digit',
		minute: '2-digit'
	}).format(new Date(instant));
}
export function safeUrl(value: string) {
	try {
		const url = new URL(value);
		return ['https:', 'http:'].includes(url.protocol) ? url.href : undefined;
	} catch {
		return undefined;
	}
}
