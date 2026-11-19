/// <reference types="@sveltejs/kit" />
/// <reference lib="webworker" />
import { build, files, version } from '$service-worker';

const worker = self as unknown as ServiceWorkerGlobalScope;
const cacheName = `beacon-shell-${version}`;
const assets = [...build, ...files, '/kiosk'];

worker.addEventListener('install', (event) => {
	event.waitUntil(caches.open(cacheName).then((cache) => cache.addAll(assets)));
});
worker.addEventListener('activate', (event) => {
	event.waitUntil(
		(async () => {
			for (const key of await caches.keys())
				if (key.startsWith('beacon-shell-') && key !== cacheName) await caches.delete(key);
			await worker.clients.claim();
		})()
	);
});
worker.addEventListener('fetch', (event) => {
	const url = new URL(event.request.url);
	if (url.origin !== worker.location.origin || event.request.method !== 'GET') return;
	// No authenticated API response enters a service-worker cache.
	if (build.includes(url.pathname) || files.includes(url.pathname)) {
		event.respondWith(caches.match(event.request).then((cached) => cached ?? fetch(event.request)));
	} else if (event.request.mode === 'navigate' && url.pathname === '/kiosk') {
		event.respondWith(
			fetch(event.request).catch(async () => (await caches.match('/kiosk')) ?? Response.error())
		);
	}
});
