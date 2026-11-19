<script lang="ts">
	import { t } from '$lib/i18n';
	import { resolve } from '$app/paths';
	import { goto } from '$app/navigation';
	import { clearSession, csrf, message, syncLanguage, write } from '$lib/api';
	let email = $state('');
	let password = $state('');
	let pending = $state(false);
	let error = $state<unknown>(null);
	async function login(event: SubmitEvent) {
		event.preventDefault();
		if (pending) return;
		pending = true;
		error = null;
		try {
			await write('/_allauth/browser/v1/auth/login', { email, password });
			password = '';
			clearSession();
			await Promise.all([csrf(), syncLanguage()]);
			await goto(resolve('/today'));
		} catch (cause) {
			error = cause;
		} finally {
			pending = false;
		}
	}
</script>

<svelte:head><title>{$t('pageTitle', { page: $t('signIn') })}</title></svelte:head>
<div class="login-shell">
	<span class="eyebrow">{$t('loginEyebrow')}</span>
	<h1>{$t('welcome')}</h1>
	<p class="muted">{$t('loginIntro')}</p>
	<form class="panel" onsubmit={login}>
		<label
			>{$t('email')}<input
				type="email"
				autocomplete="username"
				bind:value={email}
				required
			/></label
		><label
			>{$t('password')}<input
				type="password"
				autocomplete="current-password"
				bind:value={password}
				required
			/></label
		>
		{#if error}<p class="error" role="alert">{message(error, $t)}</p>{/if}<button
			class="primary"
			disabled={pending}>{pending ? $t('signingIn') : $t('signIn')}</button
		>
	</form>
	<p class="muted">{$t('accountSetup')}</p>
</div>
