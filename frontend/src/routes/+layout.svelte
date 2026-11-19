<script lang="ts">
	import { resolve } from '$app/paths';
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { clearSession, message, write } from '$lib/api';

	let { children } = $props();
	let logoutError = $state('');
	let pending = $state(false);
	let isLoginPage = $derived(page.url.pathname.replace(/\/+$/, '') === '/login');
	async function logout() {
		pending = true;
		try {
			await write('/_allauth/browser/v1/auth/session', undefined, 'DELETE').catch(async (error) => {
				// allauth returns 401 to describe the now unauthenticated session.
				const { ApiError } = await import('$lib/api');
				if (!(error instanceof ApiError && error.status === 401)) throw error;
			});
			clearSession();
			await goto(resolve('/login'), { invalidateAll: true });
		} catch (cause) {
			logoutError = message(cause);
		} finally {
			pending = false;
		}
	}
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>
{#if page.url.pathname !== '/kiosk'}
	<a class="skip-link" href="#main">Skip to content</a>
	{#if !isLoginPage}
		<div class="app-shell">
			<aside class="sidebar">
				<a class="brand" href={resolve('/today')}
					><span class="brand-symbol">◈</span><span
						>CYBER<br />BEACON<span class="brand-subtitle">YOUR DAY, WITH INTENTION</span></span
					></a
				>
				<nav aria-label="Main navigation">
					<a class:active={page.url.pathname === '/today'} href={resolve('/today')}
						><span>◎</span> Today</a
					><a class:active={page.url.pathname === '/connections'} href={resolve('/connections')}
						><span>↗</span> Connections</a
					><a class:active={page.url.pathname === '/settings'} href={resolve('/settings')}
						><span>⚙</span> Settings</a
					><a href={resolve('/kiosk')}><span>▣</span> Kiosk display</a>
				</nav>
				<div class="sidebar-bottom">
					<span class="status-dot"></span><span>SELF-HOSTED / PERSONAL</span><button
						class="quiet"
						disabled={pending}
						onclick={logout}>Sign out</button
					>
				</div>
			</aside>
			<main id="main">
				{#if logoutError}<p class="error" role="alert">{logoutError}</p>{/if}{@render children()}
			</main>
		</div>
	{:else}
		{@render children()}
	{/if}
{:else}{@render children()}{/if}
