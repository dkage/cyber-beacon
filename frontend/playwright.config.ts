import { defineConfig } from '@playwright/test';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const manifest = join(tmpdir(), `cyber-beacon-e2e-${process.pid}.json`);

export default defineConfig({
	globalTeardown: './e2e/teardown.ts',
	metadata: { e2eDatabaseManifest: manifest },
	webServer: [
		{
			command: 'cd ../backend && uv run --env-file ../.env python ../scripts/e2e_server.py',
			env: { BEACON_E2E_MANIFEST: manifest },
			url: 'http://127.0.0.1:8001/health/',
			timeout: 120000
		},
		{
			command: 'bun run build && bun run preview --host 127.0.0.1',
			port: 4173,
			env: { BEACON_API_ORIGIN: 'http://127.0.0.1:8001' },
			timeout: 120000
		}
	],
	use: { baseURL: 'http://127.0.0.1:4173', trace: 'retain-on-failure' },
	workers: 1,
	testDir: './e2e',
	testMatch: '**/*.e2e.ts'
});
