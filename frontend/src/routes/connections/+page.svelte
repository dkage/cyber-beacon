<script lang="ts">
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import { SvelteMap } from 'svelte/reactivity';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { language, t } from '$lib/i18n';
	import {
		api,
		ApiError,
		LocalizedError,
		message,
		providerStatusMessage,
		readSettings,
		write
	} from '$lib/api';
	import { formatDateTime, localDate, safeUrl } from '$lib/format';
	import type { Connection, Mount, Settings } from '$lib/types';
	import type { components } from '$lib/schema';

	type Schema = components['schemas'];
	type ResourcePage = Schema['ResourcePage'];
	type BrowsePage = Schema['BrowsePage'];
	let connections = $state<Connection[]>([]);
	let settings = $state<Settings | null>(null);
	let error = $state<unknown>(null);
	let notice = $state('');
	let pending = $state(false);
	let loading = $state(true);
	let selectedConnection = $state<Connection | null>(null);
	let resources = $state<{ page: ResourcePage; query: string } | null>(null);
	let selectedMount = $state<Mount | null>(null);
	let candidates = $state<{ page: BrowsePage; query: string } | null>(null);
	let search = $state('');
	let recordSearch = $state('');
	let day = $state('');
	let resourceRequest = 0;
	let candidateRequest = 0;
	const importKeys = new SvelteMap<string, string>();
	async function load() {
		try {
			[connections, settings] = await Promise.all([
				api<Connection[]>('/api/v1/integrations/connections/'),
				readSettings()
			]);
			if (!day) day = localDate(new Date(), settings.timezone);
		} catch (cause) {
			if (cause instanceof ApiError && cause.status === 403) await goto(resolve('/login'));
			else error = cause;
		} finally {
			loading = false;
		}
	}
	onMount(() => {
		if (page.url.searchParams.get('error') === 'consent-denied') {
			error = new LocalizedError('consentDenied');
		}
		void load();
	});
	async function action(work: () => Promise<void>) {
		if (pending) return;
		pending = true;
		error = null;
		notice = '';
		try {
			await work();
		} catch (cause) {
			error = cause;
		} finally {
			pending = false;
		}
	}
	function connect(provider: Schema['Provider']['provider']) {
		void action(async () => {
			const result = await write<Schema['OAuthRedirect']>('/api/v1/integrations/oauth/start/', {
				provider
			});
			const url = safeUrl(result.url);
			if (!url) throw new LocalizedError('invalidRedirect');
			window.location.assign(url);
		});
	}
	async function browseResources(connection: Connection, cursor = '', query = search) {
		const request = ++resourceRequest;
		if (selectedMount || selectedConnection?.id !== connection.id) resources = null;
		selectedConnection = connection;
		selectedMount = null;
		candidates = null;
		const result = await api<ResourcePage>(
			`/api/v1/integrations/connections/${connection.id}/resources/?query=${encodeURIComponent(query)}&cursor=${encodeURIComponent(cursor)}`
		);
		if (request === resourceRequest && selectedConnection?.id === connection.id) {
			resources = { page: result, query };
		}
	}
	async function browse(mount: Mount, cursor = '', query = recordSearch) {
		const request = ++candidateRequest;
		if (selectedMount?.id !== mount.id) candidates = null;
		selectedMount = mount;
		resources = null;
		selectedConnection =
			connections.find((connection) => connection.id === mount.connection) ?? selectedConnection;
		const result = await api<BrowsePage>(
			`/api/v1/integrations/mounts/${mount.id}/browse/?cursor=${encodeURIComponent(cursor)}&query=${encodeURIComponent(query)}`
		);
		if (request === candidateRequest && selectedMount?.id === mount.id) {
			candidates = { page: result, query };
		}
	}
	async function importCandidate(candidate: Schema['BrowseItem']) {
		if (!selectedMount) return;
		const identity = `${selectedMount.id}:${candidate.id}:${day}`;
		const key = importKeys.get(identity) ?? crypto.randomUUID();
		importKeys.set(identity, key);
		await write(`/api/v1/integrations/mounts/${selectedMount.id}/import/`, {
			external_id: candidate.id,
			do_date: day || null,
			key
		});
		importKeys.delete(identity);
		candidate.imported_count += 1;
		notice = $t('importedWorksheet', { title: candidate.title });
	}
</script>

<svelte:head><title>{$t('pageTitle', { page: $t('connections') })}</title></svelte:head>
<header class="page-heading">
	<div>
		<span class="eyebrow">{$t('connectionsEyebrow')}</span>
		<h1>{$t('connectionsHeading')}</h1>
		<p class="muted">{$t('connectionsIntro')}</p>
	</div>
	<div class="heading-actions">
		<button disabled={pending} onclick={() => connect('notion')}>{$t('connectNotion')}</button
		><button disabled={pending} onclick={() => connect('google')}>{$t('connectGoogle')}</button>
		<button disabled={pending} onclick={() => connect('microsoft')}>{$t('connectOutlook')}</button>
		<button disabled={pending} onclick={() => connect('github')}>{$t('connectGithub')}</button>
	</div>
</header>
{#if error}<p class="error" role="alert">{message(error, $t)}</p>{/if}{#if notice}<p
		class="success"
		role="status"
	>
		{notice}
	</p>{/if}
{#if loading}<p>{$t('loadingConnections')}</p>{:else if !connections.length}<section
		class="panel empty"
	>
		<h2>{$t('connectionsEmpty')}</h2>
		<p>{$t('connectionsEmptyHint')}</p>
		<p class="muted">{$t('oauthSetup')}</p>
	</section>{/if}
<div class="connection-grid">
	{#each connections as connection (connection.id)}<section class="panel">
			<span class="eyebrow external"
				>{connection.provider === 'notion'
					? $t('notionLabel')
					: connection.provider === 'google'
						? $t('googleLabel')
						: connection.provider === 'microsoft'
							? $t('outlookLabel')
							: $t('githubLabel')}</span
			>
			<h2>{connection.label}</h2>
			<p class="muted">
				{$t(
					connection.status === 'active'
						? 'connectionActive'
						: connection.status === 'disconnected'
							? 'connectionDisconnected'
							: connection.status === 'needs_reauth'
								? 'connectionNeedsReauth'
								: 'connectionUnknown'
				)}
			</p>
			{#if connection.last_error}<p class="error">
					{providerStatusMessage(connection.last_error, $t)}
				</p>{/if}
			<div class="heading-actions">
				<button
					disabled={pending || connection.status !== 'active'}
					onclick={() => action(() => browseResources(connection))}>{$t('chooseResource')}</button
				><button
					class="quiet"
					disabled={pending}
					onclick={() =>
						action(async () => {
							await write(`/api/v1/integrations/connections/${connection.id}/disconnect/`);
							selectedMount = null;
							selectedConnection = null;
							resources = null;
							candidates = null;
							await load();
						})}>{$t('disconnect')}</button
				>
			</div>
			{#each connection.mounts as mount (mount.id)}<article class="mount">
					<h3>{mount.label}</h3>
					<p class="muted small">
						{mount.enabled ? $t('enabled') : $t('paused')} · {mount.last_error
							? providerStatusMessage(mount.last_error, $t)
							: mount.last_succeeded_at && settings
								? $t('updatedAt', {
										time: formatDateTime(
											mount.last_succeeded_at,
											settings.timezone,
											settings.date_order,
											settings.date_separator,
											$language
										)
									})
								: $t('notRefreshed')}
					</p>
					{#if connection.provider === 'notion'}<button
							disabled={pending || connection.status !== 'active'}
							onclick={() => action(() => browse(mount))}>{$t('browseRecords')}</button
						>{:else if connection.provider === 'github'}<button
							disabled={pending || connection.status !== 'active'}
							onclick={() => action(() => browse(mount))}>{$t('browseIssues')}</button
						>{:else}<button
							disabled={pending || connection.status !== 'active'}
							onclick={() =>
								action(async () => {
									await write(`/api/v1/integrations/mounts/${mount.id}/refresh/`);
									notice = $t('refreshQueued');
									await load();
								})}>{$t('refreshMeetings')}</button
						>{/if}
				</article>{/each}
		</section>{/each}
</div>
{#if selectedConnection && !selectedMount}<section class="panel source">
		<h2>
			{$t(
				selectedConnection.provider === 'notion'
					? 'chooseNotion'
					: selectedConnection.provider === 'github'
						? 'chooseRepository'
						: 'chooseCalendar'
			)}
		</h2>
		{#if selectedConnection.provider === 'notion' || selectedConnection.provider === 'github'}<form
				class="inline-form"
				onsubmit={(event) => {
					event.preventDefault();
					void action(() => browseResources(selectedConnection!));
				}}
			>
				<label>{$t('searchResources')}<input bind:value={search} maxlength="200" /></label><button
					disabled={pending}>{$t('search')}</button
				>
			</form>
		{:else if !resources && !pending}<button
				onclick={() => action(() => browseResources(selectedConnection!))}
				>{$t('retryResources')}</button
			>{/if}
		{#if resources && !resources.page.results.length}<p>
				{$t('resourcesEmpty')}
			</p>{/if}
		<ul class="resource-list">
			{#each resources?.page.results ?? [] as resource (resource.id)}<li>
					<span>{resource.label}</span><button
						disabled={pending}
						onclick={() =>
							action(async () => {
								await write(`/api/v1/integrations/connections/${selectedConnection!.id}/mounts/`, {
									external_id: resource.id,
									label: resource.label
								});
								await load();
								notice = $t('resourceAttached');
							})}>{$t('attachResource')}</button
					>
				</li>{/each}
		</ul>
		{#if resources?.page.next_cursor}<button
				disabled={pending}
				onclick={() =>
					action(() =>
						browseResources(selectedConnection!, resources!.page.next_cursor!, resources!.query)
					)}>{$t('nextResources')}</button
			>{/if}
	</section>{/if}
{#if selectedMount}<section class="panel source">
		<div class="section-heading">
			<div>
				<span class="eyebrow">{$t('sourceBrowser')}</span>
				<h2>{selectedMount.label}</h2>
			</div>
			<label>{$t('importToDay')}<input type="date" bind:value={day} /></label>
		</div>
		<form
			class="inline-form"
			onsubmit={(event) => {
				event.preventDefault();
				void action(() => browse(selectedMount!));
			}}
		>
			<label
				>{selectedConnection?.provider === 'github'
					? $t('searchIssues')
					: $t('searchRecords')}<input bind:value={recordSearch} maxlength="200" /></label
			><button disabled={pending}
				>{selectedConnection?.provider === 'github'
					? $t('searchIssues')
					: $t('searchRecords')}</button
			>
		</form>
		{#if candidates && !candidates.page.results.length}<p>{$t('recordsEmpty')}</p>{/if}
		<ul class="resource-list">
			{#each candidates?.page.results ?? [] as candidate (candidate.id)}<li>
					<div>
						<strong>{candidate.title}</strong>
						<p class="muted small">
							{candidate.imported_count
								? $t('importAgain', { count: candidate.imported_count })
								: $t('notImported')}
						</p>
						{#if safeUrl(candidate.url)}<a
								href={safeUrl(candidate.url)}
								target="_blank"
								rel="external noreferrer">{$t('previewSource')}</a
							>{/if}
					</div>
					<button disabled={pending} onclick={() => action(() => importCandidate(candidate))}
						>{$t('importWorksheet')}</button
					>
				</li>{/each}
		</ul>
		{#if candidates?.page.next_cursor}<button
				disabled={pending}
				onclick={() =>
					action(() => browse(selectedMount!, candidates!.page.next_cursor!, candidates!.query))}
				>{$t('nextRecords')}</button
			>{/if}
	</section>{/if}
