<script lang="ts">
	import { onMount } from 'svelte';
	import { clock, formatDate, minutes } from '$lib/format';
	import { message } from '$lib/api';
	import type { components } from '$lib/schema';

	type Schema = components['schemas'];
	type Summary = Schema['KioskSummary'];
	let summary = $state<Summary | null>(null);
	let code = $state('');
	let secret = '';
	let error = $state('');
	let stale = $state(false);
	let scale = $state(1);
	let now = $state(Date.now());
	let token = $state('');
	let stopped = false;
	let timeout: ReturnType<typeof setTimeout> | undefined;
	let failures = 0;
	function remember(key: string, value: string | null) {
		try {
			if (value === null) localStorage.removeItem(key);
			else localStorage.setItem(key, value);
		} catch {
			/* Display can continue without persistence. */
		}
	}
	async function request<T>(path: string, body?: unknown): Promise<T> {
		const response = await fetch('/api/v1/kiosk/' + path, {
			method: body === undefined ? 'GET' : 'POST',
			headers: {
				'Content-Type': 'application/json',
				...(token ? { Authorization: 'Device ' + token } : {})
			},
			body: body === undefined ? undefined : JSON.stringify(body),
			cache: 'no-store',
			credentials: 'omit'
		});
		if (response.status === 401) {
			token = '';
			summary = null;
			remember('beacon-device', null);
			remember('beacon-summary', null);
			throw new Error('Display access expired or was revoked. Pair again.');
		}
		if (!response.ok)
			throw new Error(
				response.status === 400
					? 'Pairing expired. A new code will be generated.'
					: 'The server is unavailable.'
			);
		return response.json();
	}
	async function refresh() {
		if (stopped) return;
		try {
			if (token) {
				summary = await request<Summary>('summary/');
				remember('beacon-summary', JSON.stringify(summary));
				stale = false;
			} else if (!secret) {
				const pairing = await request<Schema['PairingStarted']>('pair/', {});
				code = pairing.code;
				secret = pairing.secret;
			} else {
				try {
					const result = await request<Schema['PairingClaimed'] | Schema['PairingPending']>(
						'pair/poll/',
						{ secret } satisfies Schema['Poll']
					);
					if ('token' in result) {
						token = result.token;
						secret = '';
						code = '';
						remember('beacon-device', token);
						summary = await request<Summary>('summary/');
						remember('beacon-summary', JSON.stringify(summary));
					}
				} catch (cause) {
					secret = '';
					code = '';
					throw cause;
				}
			}
			failures = 0;
			error = '';
		} catch (cause) {
			failures += 1;
			error = message(cause);
			stale = !!summary;
		}
		if (!stopped)
			timeout = setTimeout(
				refresh,
				Math.min(120000, (token ? 15000 : 5000) * 2 ** Math.min(failures, 3))
			);
	}
	onMount(() => {
		stopped = false;
		try {
			token = localStorage.getItem('beacon-device') ?? '';
			scale = Number(localStorage.getItem('beacon-scale') ?? 1) || 1;
			const cached = localStorage.getItem('beacon-summary');
			if (token && cached) {
				summary = JSON.parse(cached);
				stale = true;
			}
		} catch {
			summary = null;
		}
		const tick = setInterval(() => {
			now = Date.now();
		}, 1000);
		void refresh();
		return () => {
			stopped = true;
			clearInterval(tick);
			clearTimeout(timeout);
		};
	});
</script>

<svelte:head><title>Kiosk · Cyber Beacon</title></svelte:head>
<div class="kiosk" style={`--display-scale:${scale}`}>
	<header class="kiosk-heading">
		<div>
			<span class="eyebrow">CYBER BEACON / LIVE DISPLAY</span>
			<h1>
				{summary
					? formatDate(summary.date, summary.date_order, summary.date_separator)
					: 'Your day, at a glance.'}
			</h1>
		</div>
		<div class="kiosk-clock">
			{summary ? clock(new Date(now).toISOString(), summary.timezone) : ''}
		</div>
	</header>
	{#if stale && summary}<p class="error stale" role="status">
			STALE · Last successful update {clock(summary.fetched_at, summary.timezone)}. {error}
		</p>{:else if error}<p class="error" role="alert">{error}</p>{/if}
	{#if !token}<section class="panel pairing">
			<span class="eyebrow">PAIR THIS DISPLAY</span>
			<h2>{code || 'Requesting a pairing code…'}</h2>
			<p>On your signed-in planner, open Settings → Pair a display.</p>
			<p class="muted">
				Codes expire after ten minutes. This display can only read a limited day summary.
			</p>
		</section>{/if}
	{#if summary}<div class="kiosk-grid">
			<section class="panel">
				<span class="eyebrow">TODAY'S WORK</span>
				<h2>{summary.tasks.filter((task) => !task.completed_at).length} Tasks to go</h2>
				{#if !summary.tasks.length}<p class="muted">No work planned for this day.</p>{/if}
				<ul class="kiosk-tasks">
					{#each summary.tasks as task (task.id)}<li class:done={!!task.completed_at}>
							<span class="attention">{task.completed_at ? '✓' : '○'}</span><strong
								>{task.title}</strong
							><span class="muted"
								>{task.estimated_minutes === null ? '—' : minutes(task.estimated_minutes)}</span
							>
						</li>{/each}
				</ul>
			</section>
			<aside class="panel">
				<span class="eyebrow external">CALENDAR EVENTS</span>{#if !summary.events.length}<h2>
						Room to focus.
					</h2>
					<p class="muted">
						No meetings in the current calendar data.
					</p>{/if}{#each summary.events as event (event.id)}<article class="meeting">
						<span class="external"
							>{event.starts_at ? clock(event.starts_at, summary.timezone) : 'All day'}</span
						>
						<h2>{event.title}</h2>
					</article>{/each}
				{#each summary.calendars as calendar (calendar.id)}<p
						class="small"
						class:error={!!calendar.last_error}
					>
						{calendar.label}: {calendar.last_error ||
							(calendar.last_succeeded_at
								? 'Updated ' + clock(calendar.last_succeeded_at, summary.timezone)
								: 'Waiting for first refresh')}
					</p>{/each}
				<div class="briefing">
					<span class="eyebrow">BRIEFING</span>
					<p class="muted">{summary.briefing}</p>
				</div>
			</aside>
		</div>
		<footer class="muted">
			{summary.timezone} · Updated {clock(summary.fetched_at, summary.timezone)} · {stale
				? 'Last known day'
				: 'Connected'}
		</footer>{/if}
	<label class="display-scale"
		>TV text size<input
			type="range"
			min="0.8"
			max="1.8"
			step="0.1"
			bind:value={scale}
			oninput={() => remember('beacon-scale', String(scale))}
		/></label
	>
</div>
