import { describe, expect, it } from 'vitest';
import { ApiError, message } from '../api';
import { catalogs, translator } from './index';

function placeholders(text: string) {
	return [...new Set(Array.from(text.matchAll(/\{(\w+)\}/g), (match) => match[1]))].sort();
}

describe('translation catalogs', () => {
	it('requires identical keys, nonempty messages, and the same parameters in every language', () => {
		const keys = Object.keys(catalogs.en).sort();
		for (const [language, catalog] of Object.entries(catalogs)) {
			expect(Object.keys(catalog).sort(), language).toEqual(keys);
			for (const key of Object.keys(catalogs.en) as (keyof typeof catalogs.en)[]) {
				const text = catalog[key];
				expect(text.trim(), `${language} ${key}`).not.toBe('');
				expect(placeholders(text), `${language} ${key}`).toEqual(placeholders(catalogs.en[key]));
			}
		}
		for (const [key, text] of Object.entries(catalogs.en)) {
			if (key.endsWith('.other')) {
				const singular = key.replace(/\.other$/, '.one') as keyof typeof catalogs.en;
				expect(placeholders(catalogs.en[singular]), singular).toEqual(placeholders(text));
			}
		}
	});

	it('uses plural forms, formats counts, and falls back to English before inserting values', () => {
		expect(translator('en')('openTasks', { count: 1 })).toBe('1 open Task');
		expect(translator('pt-BR')('openTasks', { count: 0 })).toBe('0 tarefas abertas');
		expect(translator('pt-BR')('openTasks', { count: 1200 })).toBe('1.200 tarefas abertas');
		expect(translator('es')('openTasks', { count: 2 })).toBe('2 tareas pendientes');
		expect(translator('es', {})('reopenTask', { title: 'Reunião' })).toBe('Reopen Reunião');
		expect(translator('es', {})('openTasks', { count: 1 })).toBe('1 open Task');
	});

	it('uses stable API and allauth codes without showing raw unknown error details', () => {
		const pt = translator('pt-BR');
		const es = translator('es');
		const auth = new ApiError(400, { errors: [{ code: 'email_password_mismatch' }] });
		expect(message(auth, pt)).toBe(pt('invalidLogin'));
		const django = new ApiError(400, { timezone: ['English text'] }, 'invalid_timezone');
		expect(message(django, es)).toBe(es('invalidTimezone'));
		expect(message(new ApiError(503, { detail: 'Raw response' }), es)).toBe(
			es('serverUnavailable')
		);
		expect(message(new TypeError('Network error'), pt)).toBe(pt('networkError'));
	});
});
