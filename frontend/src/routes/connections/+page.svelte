<script lang="ts">
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import { SvelteMap } from 'svelte/reactivity';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api, ApiError, message, write } from '$lib/api';
	import { formatDateTime, localDate, safeUrl } from '$lib/format';
	import type { Connection, Mount, Settings } from '$lib/types';
	interface Resource {
		id: string;
		label: string;
	}
	interface Candidate {
		id: string;
		title: string;
		url: string;
		imported_count: number;
	}
	interface Page<T> {
		results: T[];
		next_cursor: string | null;
	}
	let connections = $state<Connection[]>([]);
	let settings = $state<Settings | null>(null);
	let error = $state('');
	let notice = $state('');
	let pending = $state(false);
	let loading = $state(true);
	let selectedConnection = $state<Connection | null>(null);
	let resources = $state<Page<Resource> | null>(null);
	let selectedMount = $state<Mount | null>(null);
	let candidates = $state<Page<Candidate> | null>(null);
	let search = $state('');
	let recordSearch = $state('');
	let day = $state('');
	let resourceRequest = 0;
	let candidateRequest = 0;
	const importKeys = new SvelteMap<string, string>();
	async function load() {
		try {
			connections = await api<Connection[]>('/api/v1/integrations/connections/');
			settings = await api<Settings>('/api/v1/settings/');
			if (!day) day = localDate(new Date(), settings.timezone);
		} catch (cause) {
			if (cause instanceof ApiError && cause.status === 403) await goto(resolve('/login'));
			else error = message(cause);
		} finally {
			loading = false;
		}
	}
	onMount(() => {
		if (page.url.searchParams.get('error') === 'consent-denied') {
			error = 'Provider access was not granted. You can try connecting again when ready.';
		}
		void load();
	});
	async function action(work: () => Promise<void>) {
		if (pending) return;
		pending = true;
		error = '';
		notice = '';
		try {
			await work();
		} catch (cause) {
			error = message(cause);
		} finally {
			pending = false;
		}
	}
	function connect(provider: string) {
		void action(async () => {
			const result = await write<{ url: string }>('/api/v1/integrations/oauth/start/', {
				provider
			});
			const url = safeUrl(result.url);
			if (!url) throw new Error('Invalid provider redirect.');
			window.location.assign(url);
		});
	}
	async function browseResources(connection: Connection, cursor = '') {
		const request = ++resourceRequest;
		selectedConnection = connection;
		selectedMount = null;
		candidates = null;
		resources = null;
		const result = await api<Page<Resource>>(
			`/api/v1/integrations/connections/${connection.id}/resources/?query=${encodeURIComponent(search)}&cursor=${encodeURIComponent(cursor)}`
		);
		if (request === resourceRequest && selectedConnection?.id === connection.id) {
			resources = result;
		}
	}
	async function browse(mount: Mount, cursor = '') {
		const request = ++candidateRequest;
		selectedMount = mount;
		resources = null;
		candidates = null;
		selectedConnection =
			connections.find((connection) => connection.id === mount.connection) ?? selectedConnection;
		const result = await api<Page<Candidate>>(
			`/api/v1/integrations/mounts/${mount.id}/browse/?cursor=${encodeURIComponent(cursor)}&query=${encodeURIComponent(recordSearch)}`
		);
		if (request === candidateRequest && selectedMount?.id === mount.id) {
			candidates = result;
		}
	}
	async function importCandidate(candidate: Candidate) {
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
		notice = `Imported “${candidate.title}” as a local worksheet.`;
	}
</script>

<svelte:head><title>Connections · Cyber Beacon</title></svelte:head>
<header class="page-heading">
	<div>
		<span class="eyebrow">BRING YOUR WORK TOGETHER</span>
		<h1>Connected, on your terms.</h1>
		<p class="muted">Browse first. Import deliberately. Your worksheet stays yours.</p>
	</div>
	<div class="heading-actions">
		<button disabled={pending} onclick={() => connect('notion')}>Connect Notion</button><button
			disabled={pending}
			onclick={() => connect('google')}>Connect Google Calendar</button
		>
		<button disabled={pending} onclick={() => connect('microsoft')}>Connect Outlook Calendar</button
		>
		<button disabled={pending} onclick={() => connect('github')}>Connect GitHub</button>
	</div>
</header>
{#if error}<p class="error" role="alert">{error}</p>{/if}{#if notice}<p
		class="success"
		role="status"
	>
		{notice}
	</p>{/if}
{#if loading}<p>Loading Connections…</p>{:else if !connections.length}<section class="panel empty">
		<h2>Your work, gathered here.</h2>
		<p>Connect Notion or GitHub to choose worksheets, or a calendar to see meetings.</p>
		<p class="muted">OAuth application credentials must be configured by the server operator.</p>
	</section>{/if}
<div class="connection-grid">
	{#each connections as connection (connection.id)}<section class="panel">
			<span class="eyebrow external"
				>{connection.provider === 'notion'
					? 'NOTION'
					: connection.provider === 'google'
						? 'GOOGLE CALENDAR'
						: connection.provider === 'microsoft'
							? 'OUTLOOK CALENDAR'
							: 'GITHUB ISSUES'}</span
			>
			<h2>{connection.label}</h2>
			<p class="muted">{connection.status}</p>
			{#if connection.last_error}<p class="error">{connection.last_error}</p>{/if}
			<div class="heading-actions">
				<button
					disabled={pending || connection.status !== 'active'}
					onclick={() => action(() => browseResources(connection))}>Choose resource</button
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
						})}>Disconnect</button
				>
			</div>
			{#each connection.mounts as mount (mount.id)}<article class="mount">
					<h3>{mount.label}</h3>
					<p class="muted small">
						{mount.enabled ? 'Enabled' : 'Paused'} · {mount.last_error ||
							(mount.last_succeeded_at && settings
								? 'Updated ' +
									formatDateTime(
										mount.last_succeeded_at,
										settings.timezone,
										settings.date_order,
										settings.date_separator
									)
								: 'No refresh yet')}
					</p>
					{#if connection.provider === 'notion'}<button
							disabled={pending || connection.status !== 'active'}
							onclick={() => action(() => browse(mount))}>Browse records</button
						>{:else if connection.provider === 'github'}<button
							disabled={pending || connection.status !== 'active'}
							onclick={() => action(() => browse(mount))}>Browse issues</button
						>{:else}<button
							disabled={pending || connection.status !== 'active'}
							onclick={() =>
								action(async () => {
									await write(`/api/v1/integrations/mounts/${mount.id}/refresh/`);
									notice = 'Calendar refresh queued. Meetings will update shortly.';
									await load();
								})}>Refresh meetings</button
						>{/if}
				</article>{/each}
		</section>{/each}
</div>
{#if selectedConnection && resources}<section class="panel source">
		<h2>
			Choose a {selectedConnection.provider === 'notion'
				? 'Notion data source'
				: selectedConnection.provider === 'github'
					? 'GitHub repository'
					: 'calendar'}
		</h2>
		{#if selectedConnection.provider === 'notion' || selectedConnection.provider === 'github'}<form
				class="inline-form"
				onsubmit={(event) => {
					event.preventDefault();
					void action(() => browseResources(selectedConnection!));
				}}
			>
				<label>Search resources<input bind:value={search} maxlength="200" /></label><button
					disabled={pending}>Search</button
				>
			</form>{/if}
		{#if !resources.results.length}<p>
				No accessible resources. Check the provider’s sharing permissions.
			</p>{/if}
		<ul class="resource-list">
			{#each resources.results as resource (resource.id)}<li>
					<span>{resource.label}</span><button
						disabled={pending}
						onclick={() =>
							action(async () => {
								await write(`/api/v1/integrations/connections/${selectedConnection!.id}/mounts/`, {
									external_id: resource.id,
									label: resource.label
								});
								await load();
								notice = 'Resource attached.';
							})}>Attach resource</button
					>
				</li>{/each}
		</ul>
		{#if resources.next_cursor}<button
				disabled={pending}
				onclick={() => action(() => browseResources(selectedConnection!, resources!.next_cursor!))}
				>Next resources</button
			>{/if}
	</section>{/if}
{#if selectedMount && candidates}<section class="panel source">
		<div class="section-heading">
			<div>
				<span class="eyebrow">SOURCE BROWSER</span>
				<h2>{selectedMount.label}</h2>
			</div>
			<label>Import to day<input type="date" bind:value={day} /></label>
		</div>
		<form
			class="inline-form"
			onsubmit={(event) => {
				event.preventDefault();
				void action(() => browse(selectedMount!));
			}}
		>
			<label
				>{selectedConnection?.provider === 'github' ? 'Search issues' : 'Search records'}<input
					bind:value={recordSearch}
					maxlength="200"
				/></label
			><button disabled={pending}
				>{selectedConnection?.provider === 'github' ? 'Search issues' : 'Search records'}</button
			>
		</form>
		{#if !candidates.results.length}<p>No records in this source.</p>{/if}
		<ul class="resource-list">
			{#each candidates.results as candidate (candidate.id)}<li>
					<div>
						<strong>{candidate.title}</strong>
						<p class="muted small">
							{candidate.imported_count
								? `${candidate.imported_count} existing worksheets · import again intentionally`
								: 'Not imported'}
						</p>
						{#if safeUrl(candidate.url)}<a
								href={safeUrl(candidate.url)}
								target="_blank"
								rel="external noreferrer">Preview at source ↗</a
							>{/if}
					</div>
					<button disabled={pending} onclick={() => action(() => importCandidate(candidate))}
						>Import worksheet</button
					>
				</li>{/each}
		</ul>
		{#if candidates.next_cursor}<button
				disabled={pending}
				onclick={() => action(() => browse(selectedMount!, candidates!.next_cursor!))}
				>Next records</button
			>{/if}
	</section>{/if}
