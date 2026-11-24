import { derived, get, writable } from 'svelte/store';
import type { components } from '../schema';
import en from './en';
import es from './es';
import ptBR from './pt-BR';

export const languages = {
	en: 'English',
	'pt-BR': 'Português (Brasil)',
	es: 'Español'
} satisfies Record<components['schemas']['LanguageEnum'], string>;
export type Language = keyof typeof languages;
export const defaultLanguage: Language = 'en';

export function isLanguage(value: unknown): value is Language {
	return typeof value === 'string' && Object.hasOwn(languages, value);
}

export const catalogs = { en, 'pt-BR': ptBR, es };
type CatalogKey = keyof typeof en;
type PluralBase<Key> = Key extends `${infer Base}.other` ? Base : never;
type PluralKey = PluralBase<CatalogKey>;
type MessageKey = Exclude<CatalogKey, `${string}.${string}`> | PluralKey;

type ParameterNames<Text> = Text extends `${string}{${infer Name}}${infer Rest}`
	? Name | ParameterNames<Rest>
	: never;
type ParametersFor<Key extends MessageKey> = ParameterNames<
	(typeof en)[Key extends PluralKey ? `${Key}.other` : Extract<Key, CatalogKey>]
>;
type Substitutions<Key extends MessageKey> = [ParametersFor<Key>] extends [never]
	? []
	: [Record<ParametersFor<Key>, string | number>];
export type Translator = <Key extends MessageKey>(
	key: Key,
	...values: Substitutions<Key>
) => string;

export function translator(
	language: Language,
	catalog: Partial<Record<CatalogKey, string>> = catalogs[language]
): Translator {
	const plurals = new Intl.PluralRules(language);
	const numbers = new Intl.NumberFormat(language);
	return (key, ...[values]) => {
		const params: Record<string, string | number> | undefined = values;
		const count = params?.count;
		const variant =
			typeof count === 'number' && count !== 0 && plurals.select(count) === 'one' ? 'one' : 'other';
		const variants: Partial<Record<string, string>> = catalog;
		const fallback: Partial<Record<string, string>> = en;
		const template =
			variants[key + '.' + variant] ??
			variants[key] ??
			fallback[key + '.' + variant] ??
			fallback[key] ??
			key;
		return template.replace(/\{(\w+)\}/g, (placeholder, name: string) => {
			const value = params?.[name];
			return typeof value === 'number' ? numbers.format(value) : (value ?? placeholder);
		});
	};
}

function savedLanguage(): Language {
	try {
		const saved = localStorage.getItem('beacon-language');
		if (isLanguage(saved)) return saved;
	} catch {
		// The browser can still use the account preference without local storage.
	}
	return defaultLanguage;
}

const web = writable<Language>(defaultLanguage);
const kiosk = writable<Language>(defaultLanguage);
export const language = { subscribe: web.subscribe };
export const kioskLanguage = { subscribe: kiosk.subscribe };
export const t = derived(language, (selected): Translator => translator(selected));
export const kioskT = derived(kioskLanguage, (selected): Translator => translator(selected));

export function restoreSavedLanguage() {
	web.set(savedLanguage());
}

export function setLanguage(value: unknown) {
	const selected = isLanguage(value) ? value : defaultLanguage;
	web.set(selected);
	try {
		localStorage.setItem('beacon-language', selected);
	} catch {
		// The account preference remains available from the server.
	}
}

export function setKioskLanguage(value: unknown) {
	kiosk.set(isLanguage(value) ? value : defaultLanguage);
}

export function currentTranslator() {
	return get(t);
}
