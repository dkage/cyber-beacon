import { describe, expect, it } from 'vitest';
import { localDate, minutes, safeUrl } from './format';

describe('calendar and display boundaries', () => {
	it('formats a local calendar date without UTC shifting', () => {
		expect(localDate(new Date('2026-11-18T02:30:00Z'), 'America/Sao_Paulo')).toBe('2026-11-17');
		expect(localDate(new Date('2026-11-18T02:30:00Z'), 'Asia/Tokyo')).toBe('2026-11-18');
	});
	it('keeps overcommit visible and rejects executable source URLs', () => {
		expect(minutes(-90)).toBe('−1h 30m');
		expect(safeUrl('javascript:alert(1)')).toBeUndefined();
		expect(safeUrl('https://notion.so/source')).toBe('https://notion.so/source');
	});
});
