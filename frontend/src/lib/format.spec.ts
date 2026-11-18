import { describe, expect, it } from 'vitest';
import { formatDate, formatDateTime, localDate, minutes, safeUrl } from './format';

describe('calendar and display boundaries', () => {
	it('formats a local calendar date without UTC shifting', () => {
		expect(localDate(new Date('2026-11-18T02:30:00Z'), 'America/Sao_Paulo')).toBe('2026-11-17');
		expect(localDate(new Date('2026-11-18T02:30:00Z'), 'Asia/Tokyo')).toBe('2026-11-18');
	});
	it('formats dates in each user-selected order and separator', () => {
		expect(formatDate('2026-11-18', 'ymd', '-')).toBe('2026-11-18');
		expect(formatDate('2026-11-18', 'ymd', '/')).toBe('2026/11/18');
		expect(formatDate('2026-11-18', 'dmy', '-')).toBe('18-11-2026');
		expect(formatDate('2026-11-18', 'dmy', '/')).toBe('18/11/2026');
		expect(formatDate('2026-11-18', 'mdy', '-')).toBe('11-18-2026');
		expect(formatDate('2026-11-18', 'mdy', '/')).toBe('11/18/2026');
	});
	it('formats timestamps using the user date format and timezone', () => {
		expect(formatDateTime('2026-11-18T02:30:00Z', 'America/Sao_Paulo', 'dmy', '/')).toContain(
			'17/11/2026'
		);
	});
	it('keeps overcommit visible and rejects executable source URLs', () => {
		expect(minutes(-90)).toBe('−1h 30m');
		expect(safeUrl('javascript:alert(1)')).toBeUndefined();
		expect(safeUrl('https://notion.so/source')).toBe('https://notion.so/source');
	});
});
