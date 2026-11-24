import prettier from 'eslint-config-prettier';
import path from 'node:path';
import js from '@eslint/js';
import svelte from 'eslint-plugin-svelte';
import { defineConfig, globalIgnores, includeIgnoreFile } from 'eslint/config';
import globals from 'globals';
import ts from 'typescript-eslint';

const gitignorePath = path.resolve(import.meta.dirname, '.gitignore');

export default defineConfig(
	includeIgnoreFile(gitignorePath),
	globalIgnores(['src/lib/schema.d.ts']),
	js.configs.recommended,
	ts.configs.recommended,
	{
		languageOptions: { globals: { ...globals.browser, ...globals.node } },
		rules: {
			// typescript-eslint strongly recommend that you do not use the no-undef lint rule on TypeScript projects.
			// see: https://typescript-eslint.io/troubleshooting/faqs/eslint/#i-get-errors-from-the-no-undef-rule-about-global-variables-not-being-defined-even-though-there-are-no-typescript-errors
			'no-undef': 'off'
		}
	},
	{
		// Tooling outside the app TSConfig keeps the syntax-based preset above.
		files: ['src/**/*.{ts,svelte}', 'vite.config.ts'],
		extends: [ts.configs.recommendedTypeChecked],
		languageOptions: {
			parserOptions: {
				projectService: { allowDefaultProject: ['src/service-worker.ts'] },
				tsconfigRootDir: import.meta.dirname,
				extraFileExtensions: ['.svelte']
			}
		}
	},
	svelte.configs.recommended,
	{
		files: ['**/*.svelte'],
		languageOptions: { parserOptions: { parser: ts.parser } }
	},
	prettier,
	svelte.configs.prettier
);
