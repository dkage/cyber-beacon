<script lang="ts">
	import { resolve } from '$app/paths';
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { kioskLanguage, language, t } from '$lib/i18n';
	import { clearSession, message, syncLanguage, write } from '$lib/api';

	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();
	let logoutError = $state<unknown>(null);
	let pending = $state(false);
	const activePath = $derived(page.url.pathname.replace(/\/+$/, ''));
	const isLoginPage = $derived(activePath === '/login');
	const isKioskPage = $derived(activePath === '/kiosk');
	onMount(() => {
		if (!isKioskPage && !isLoginPage && activePath !== '/settings' && activePath !== '/connections')
			void syncLanguage();
	});
	$effect(() => {
		document.documentElement.lang = isKioskPage ? $kioskLanguage : $language;
	});
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
			logoutError = cause;
		} finally {
			pending = false;
		}
	}
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>
{#if !isKioskPage}
	<a class="skip-link" href="#main">{$t('skipContent')}</a>
	{#if !isLoginPage}
		<div class="app-shell">
			<aside class="sidebar">
				<a class="brand" href={resolve('/today')}
					><span class="brand-symbol">◈</span><span
						>CYBER<br />BEACON<span class="brand-subtitle">{$t('brandTagline')}</span></span
					></a
				>
				<nav aria-label={$t('mainNavigation')}>
					<a class:active={page.url.pathname === '/today'} href={resolve('/today')}
						><span aria-hidden="true">◎</span> {$t('today')}</a
					><a class:active={page.url.pathname === '/connections'} href={resolve('/connections')}
						><span aria-hidden="true">↗</span> {$t('connections')}</a
					><a class:active={page.url.pathname === '/settings'} href={resolve('/settings')}
						><span aria-hidden="true">⚙</span> {$t('settings')}</a
					><a href={resolve('/kiosk')}><span aria-hidden="true">▣</span> {$t('kioskDisplay')}</a>
				</nav>
				<div class="sidebar-bottom">
					<span class="status-dot"></span><span>{$t('selfHosted')}</span><button
						class="quiet"
						disabled={pending}
						onclick={logout}>{$t('signOut')}</button
					>
				</div>
			</aside>
			<main id="main">
				{#if logoutError}<p class="error" role="alert">
						{message(logoutError, $t)}
					</p>{/if}{@render children()}
			</main>
		</div>
	{:else}
		{@render children()}
	{/if}
{:else}{@render children()}{/if}
