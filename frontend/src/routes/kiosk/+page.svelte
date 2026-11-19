<script lang="ts">
	import { onMount } from 'svelte';
	import { clock, formatDate, minutes } from '$lib/format';
	import { kioskLanguage, kioskT as t, setKioskLanguage } from '$lib/i18n';
	import { LocalizedError, message, providerStatusMessage } from '$lib/api';
	import { isKioskSummary, isRecord } from '$lib/kiosk';
	import type { components } from '$lib/schema';

	type Schema = components['schemas'];
	type Summary = Schema['KioskSummary'];
	let summary = $state<Summary | null>(null);
	let code = $state('');
	let secret = '';
	let error = $state<unknown>(null);
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
	async function request(path: string, body?: unknown): Promise<unknown> {
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
			throw new LocalizedError('displayExpired');
		}
		if (!response.ok)
			throw new LocalizedError(response.status === 400 ? 'pairExpired' : 'serverUnavailable');
		const result: unknown = await response.json();
		return result;
	}
	async function refreshSummary() {
		const result = await request('summary/');
		if (!isKioskSummary(result)) throw new LocalizedError('invalidSummary');
		summary = result;
		setKioskLanguage(result.language);
		remember('beacon-summary', JSON.stringify(result));
		stale = false;
	}
	async function refresh() {
		if (stopped) return;
		try {
			if (token) {
				await refreshSummary();
			} else if (!secret) {
				const pairing = await request('pair/', {});
				if (
					!isRecord(pairing) ||
					typeof pairing.code !== 'string' ||
					typeof pairing.secret !== 'string'
				) {
					throw new LocalizedError('invalidPairCode');
				}
				code = pairing.code;
				secret = pairing.secret;
			} else {
				try {
					const result = await request('pair/poll/', { secret } satisfies Schema['Poll']);
					if (isRecord(result) && typeof result.token === 'string' && result.token) {
						token = result.token;
						secret = '';
						code = '';
						remember('beacon-device', token);
						await refreshSummary();
					} else if (!isRecord(result) || result.status !== 'pending') {
						throw new LocalizedError('invalidPairStatus');
					}
				} catch (cause) {
					secret = '';
					code = '';
					throw cause;
				}
			}
			failures = 0;
			error = null;
		} catch (cause) {
			failures += 1;
			error = cause;
			stale = !!summary;
		}
		if (!stopped)
			timeout = setTimeout(
				() => {
					void refresh();
				},
				Math.min(120000, (token ? 15000 : 5000) * 2 ** Math.min(failures, 3))
			);
	}
	onMount(() => {
		stopped = false;
		setKioskLanguage(undefined);
		try {
			token = localStorage.getItem('beacon-device') ?? '';
			scale = Number(localStorage.getItem('beacon-scale') ?? 1) || 1;
			const cached = localStorage.getItem('beacon-summary');
			if (token && cached) {
				const result: unknown = JSON.parse(cached);
				if (isKioskSummary(result)) {
					summary = result;
					setKioskLanguage(result.language);
					stale = true;
				} else {
					remember('beacon-summary', null);
				}
			}
		} catch {
			summary = null;
			remember('beacon-summary', null);
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

<svelte:head><title>{$t('pageTitle', { page: $t('kiosk') })}</title></svelte:head>
<div class="kiosk" style={`--display-scale:${scale}`}>
	<header class="kiosk-heading">
		<div>
			<span class="eyebrow">{$t('kioskEyebrow')}</span>
			<h1>
				{summary
					? formatDate(summary.date, summary.date_order, summary.date_separator)
					: $t('kioskHeading')}
			</h1>
		</div>
		<div class="kiosk-clock">
			{summary ? clock(new Date(now).toISOString(), summary.timezone, $kioskLanguage) : ''}
		</div>
	</header>
	{#if stale && summary}<p class="error stale" role="status">
			{$t('kioskStale', { time: clock(summary.fetched_at, summary.timezone, $kioskLanguage) })}
			{error ? message(error, $t) : ''}
		</p>{:else if error}<p class="error" role="alert">{message(error, $t)}</p>{/if}
	{#if !token}<section class="panel pairing">
			<span class="eyebrow">{$t('kioskPair')}</span>
			<h2>{code || $t('kioskRequestCode')}</h2>
			<p>{$t('kioskPairPath')}</p>
			<p class="muted">
				{$t('kioskLimited')}
			</p>
		</section>{/if}
	{#if summary}<div class="kiosk-grid">
			<section class="panel">
				<span class="eyebrow">{$t('kioskToday')}</span>
				<h2>
					{$t('kioskRemaining', {
						count: summary.tasks.filter((task) => !task.completed_at).length
					})}
				</h2>
				{#if !summary.tasks.length}<p class="muted">{$t('kioskEmpty')}</p>{/if}
				<ul class="kiosk-tasks">
					{#each summary.tasks as task (task.id)}<li class:done={!!task.completed_at}>
							<span class="attention">{task.completed_at ? '✓' : '○'}</span><strong
								>{task.title}</strong
							><span class="muted"
								>{task.estimated_minutes === null ? '—' : minutes(task.estimated_minutes, $t)}</span
							>
						</li>{/each}
				</ul>
			</section>
			<aside class="panel">
				<span class="eyebrow external">{$t('kioskEvents')}</span>{#if !summary.events.length}<h2>
						{$t('kioskFocus')}
					</h2>
					<p class="muted">
						{$t('kioskNoMeetings')}
					</p>{/if}{#each summary.events as event (event.id)}<article class="meeting">
						<span class="external"
							>{event.starts_at
								? clock(event.starts_at, summary.timezone, $kioskLanguage)
								: $t('allDay')}</span
						>
						<h2>{event.title}</h2>
					</article>{/each}
				{#each summary.calendars as calendar (calendar.id)}<p
						class="small"
						class:error={!!calendar.last_error}
					>
						{calendar.label}: {calendar.last_error
							? providerStatusMessage(calendar.last_error, $t)
							: calendar.last_succeeded_at
								? $t('updatedAt', {
										time: clock(calendar.last_succeeded_at, summary.timezone, $kioskLanguage)
									})
								: $t('waitingRefresh')}
					</p>{/each}
				<div class="briefing">
					<span class="eyebrow">{$t('briefing')}</span>
					<p class="muted">
						{summary.briefing === $t('briefingLater') ? $t('briefingLater') : summary.briefing}
					</p>
				</div>
			</aside>
		</div>
		<footer class="muted">
			{summary.timezone} · {$t('updatedAt', {
				time: clock(summary.fetched_at, summary.timezone, $kioskLanguage)
			})} · {stale ? $t('lastKnownDay') : $t('connected')}
		</footer>{/if}
	<label class="display-scale"
		>{$t('tvTextSize')}<input
			type="range"
			min="0.8"
			max="1.8"
			step="0.1"
			bind:value={scale}
			oninput={() => remember('beacon-scale', String(scale))}
		/></label
	>
</div>
