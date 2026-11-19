import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import type { FullConfig } from '@playwright/test';

export default function teardown(config: FullConfig) {
	execFileSync(
		'uv',
		[
			'run',
			'--env-file',
			'../.env',
			'python',
			'../scripts/e2e_database_cleanup.py',
			String(config.metadata.e2eDatabaseManifest)
		],
		{
			cwd: fileURLToPath(new URL('../../backend/', import.meta.url)),
			stdio: 'inherit'
		}
	);
}
