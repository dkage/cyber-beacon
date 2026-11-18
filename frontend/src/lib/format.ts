export function minutes(value: number): string {
	const sign = value < 0 ? '−' : '';
	const absolute = Math.abs(Math.round(value));
	const hours = Math.floor(absolute / 60);
	return `${sign}${hours ? hours + 'h ' : ''}${absolute % 60}m`;
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
export function clock(instant: string, timezone: string) {
	return new Intl.DateTimeFormat(undefined, {
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
