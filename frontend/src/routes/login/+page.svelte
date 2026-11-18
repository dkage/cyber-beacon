<script lang="ts">
	import { resolve } from '$app/paths';
	import { goto } from '$app/navigation';
	import { clearSession, csrf, message, write } from '$lib/api';
	let email = $state('');
	let password = $state('');
	let pending = $state(false);
	let error = $state('');
	async function login(event: SubmitEvent) {
		event.preventDefault();
		if (pending) return;
		pending = true;
		error = '';
		try {
			await write('/_allauth/browser/v1/auth/login', { email, password });
			password = '';
			clearSession();
			await csrf();
			await goto(resolve('/today'));
		} catch (cause) {
			error = message(cause);
		} finally {
			pending = false;
		}
	}
</script>

<svelte:head><title>Sign in · Cyber Beacon</title></svelte:head>
<div class="login-shell">
	<span class="eyebrow">PERSONAL MISSION CONTROL</span>
	<h1>Welcome back.</h1>
	<p class="muted">A clear day starts with a little intention.</p>
	<form class="panel" onsubmit={login}>
		<label>Email<input type="email" autocomplete="username" bind:value={email} required /></label
		><label
			>Password<input
				type="password"
				autocomplete="current-password"
				bind:value={password}
				required
			/></label
		>
		{#if error}<p class="error" role="alert">{error}</p>{/if}<button
			class="primary"
			disabled={pending}>{pending ? 'Signing in…' : 'Sign in'}</button
		>
	</form>
	<p class="muted">Create your account with the server setup command.</p>
</div>
