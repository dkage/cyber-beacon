<script lang="ts">
	import { resolve } from '$app/paths';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import {
		api,
		ApiError,
		applySavedLanguage,
		message,
		providerStatusMessage,
		readSettings,
		write
	} from '$lib/api';
	import { language, languages, t } from '$lib/i18n';
	import { formatDate, formatDateInTimezone, formatDateTime } from '$lib/format';
	import type { components } from '$lib/schema';
	import type { Settings, Task } from '$lib/types';
	type Schema = components['schemas'];
	interface Job {
		id: number;
		kind: string;
		outcome: string;
		message: string;
		started_at: string;
	}
	let settings = $state<Settings | null>(null);
	let devices = $state<Schema['Device'][]>([]);
	let jobs = $state<Job[]>([]);
	let trash = $state<Task[]>([]);
	let error = $state<unknown>(null);
	let notice = $state('');
	let pending = $state(false);
	let code = $state('');
	let label = $state('');
	const weekdays = $derived.by(() => {
		const format = new Intl.DateTimeFormat($language, { weekday: 'long', timeZone: 'UTC' });
		return Array.from({ length: 7 }, (_, index) => format.format(Date.UTC(2024, 0, index + 1)));
	});
	const jobKinds: Partial<Record<string, 'jobCarry' | 'jobCalendar'>> = {
		carry_forward: 'jobCarry',
		calendar_sync: 'jobCalendar'
	};
	const jobOutcomes: Partial<
		Record<string, 'jobRunning' | 'jobSuccess' | 'jobFailed' | 'jobSkipped' | 'jobCancelled'>
	> = {
		started: 'jobRunning',
		success: 'jobSuccess',
		failed: 'jobFailed',
		skipped: 'jobSkipped',
		lost: 'jobFailed',
		cancelled: 'jobCancelled',
		retryable: 'jobFailed',
		fatal: 'jobFailed',
		auth_dead: 'jobFailed',
		rate_limited: 'jobFailed'
	};
	async function load() {
		try {
			settings = await readSettings();
			if (!settings.work_weekdays.length) settings.work_weekdays = [0, 1, 2, 3, 4];
			devices = await api<Schema['Device'][]>('/api/v1/kiosk/devices/');
			jobs = (await api<{ results: Job[] }>('/api/v1/jobs/?limit=20')).results;
			trash = (await api<{ results: Task[] }>('/api/v1/tasks/?trash=true&limit=100')).results;
		} catch (cause) {
			if (cause instanceof ApiError && cause.status === 403) await goto(resolve('/login'));
			else error = cause;
		}
	}
	onMount(() => {
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
</script>

<svelte:head><title>{$t('pageTitle', { page: $t('settings') })}</title></svelte:head>
<header class="page-heading">
	<div>
		<span class="eyebrow">{$t('settingsEyebrow')}</span>
		<h1>{$t('settingsHeading')}</h1>
		<p class="muted">{$t('settingsIntro')}</p>
	</div>
</header>
{#if error}<p role="alert" class="error">{message(error, $t)}</p>{/if}{#if notice}<p
		role="status"
		class="success"
	>
		{notice}
	</p>{/if}
<div class="connection-grid">
	{#if settings}<section class="panel">
			<h2>{$t('preferences')}</h2>
			<p class="muted">{settings.email}</p>
			<form
				onsubmit={(event) => {
					event.preventDefault();
					void action(async () => {
						settings = await write<Settings>('/api/v1/settings/', settings, 'PATCH');
						applySavedLanguage(settings.language);
						notice = $t('preferencesSaved');
					});
				}}
			>
				<label
					>{$t('timezone')}<input
						bind:value={settings.timezone}
						required
						placeholder="America/Sao_Paulo"
					/></label
				>
				<div class="form-grid">
					<label
						>{$t('workStarts')}<input
							type="time"
							bind:value={settings.work_start}
							required
						/></label
					><label
						>{$t('workEnds')}<input type="time" bind:value={settings.work_end} required /></label
					>
				</div>
				<label>
					{$t('language')}
					<select bind:value={settings.language}>
						{#each Object.entries(languages) as [value, name] (value)}
							<option {value} lang={value}>{name}</option>
						{/each}
					</select>
				</label>
				<fieldset>
					<legend>{$t('workingDays')}</legend>{#each weekdays as name, index (name)}<label
							class="check-label"
							><input
								type="checkbox"
								value={index}
								bind:group={settings.work_weekdays}
							/>{name}</label
						>{/each}
				</fieldset>
				<div class="form-grid">
					<label
						>{$t('dateOrder')}<select bind:value={settings.date_order}>
							<option value="ymd">{$t('yearMonthDay')}</option>
							<option value="dmy">{$t('dayMonthYear')}</option>
							<option value="mdy">{$t('monthDayYear')}</option>
						</select></label
					><label
						>{$t('dateSeparator')}<select bind:value={settings.date_separator}>
							<option value="-">{$t('hyphen')}</option>
							<option value="/">{$t('slash')}</option>
						</select></label
					>
				</div>
				<p class="muted">
					{$t('datePreview', {
						date: formatDate('2026-11-18', settings.date_order, settings.date_separator)
					})}
				</p>
				<button class="primary" disabled={pending}>{$t('savePreferences')}</button>
			</form>
		</section>{/if}
	<section class="panel">
		<h2>{$t('pairDisplay')}</h2>
		<p class="muted">
			{$t('pairInstructions')} <a href={resolve('/kiosk')}>{$t('kiosk')}</a>
		</p>
		<form
			onsubmit={(event) => {
				event.preventDefault();
				void action(async () => {
					await write('/api/v1/kiosk/pair/approve/', {
						code: code.toUpperCase(),
						label: label || $t('officeDisplay')
					} satisfies Schema['Approve']);
					code = '';
					await load();
					notice = $t('displayApproved');
				});
			}}
		>
			<label
				>{$t('pairCode')}<input
					bind:value={code}
					minlength="8"
					maxlength="8"
					required
					autocomplete="off"
				/></label
			><label
				>{$t('displayName')}<input
					bind:value={label}
					maxlength="100"
					placeholder={$t('officeDisplay')}
				/></label
			><button disabled={pending}>{$t('approveDisplay')}</button>
		</form>
		{#each devices as device (device.id)}<article class="mount">
				<strong>{device.label}</strong>
				<p class="muted small">
					{device.revoked_at
						? $t('revoked')
						: settings
							? $t('expires', {
									date: formatDateInTimezone(
										device.expires_at,
										settings.timezone,
										settings.date_order,
										settings.date_separator
									)
								})
							: $t('expiresSoon')}
				</p>
				<button
					disabled={pending || !!device.revoked_at}
					onclick={() =>
						action(async () => {
							await write(`/api/v1/kiosk/devices/${device.id}/revoke/`);
							await load();
						})}>{$t('revokeDisplay')}</button
				>
			</article>{/each}
	</section>
</div>
<section class="panel">
	<h2>{$t('trash')}</h2>
	<p class="muted">{$t('trashHint')}</p>
	{#if !trash.length}<p>{$t('trashEmpty')}</p>{/if}
	<ul class="resource-list">
		{#each trash as task (task.id)}<li>
				<span>{task.title}</span><button
					disabled={pending}
					onclick={() =>
						action(async () => {
							await write(`/api/v1/tasks/${task.id}/restore/`, undefined, 'POST', task.version);
							await load();
							notice = $t('taskRestored');
						})}>{$t('restoreTask')}</button
				>
			</li>{/each}
	</ul>
</section>
<section class="panel">
	<h2>{$t('backgroundHealth')}</h2>
	{#if !jobs.length}<p class="muted">{$t('noJobs')}</p>{/if}
	<ul class="job-list">
		{#each jobs as job (job.id)}<li class:error={job.outcome !== 'success'}>
				<time
					>{settings
						? formatDateTime(
								job.started_at,
								settings.timezone,
								settings.date_order,
								settings.date_separator,
								$language
							)
						: job.started_at}</time
				><strong
					>{$t(jobKinds[job.kind] ?? 'jobOther')} · {$t(
						jobOutcomes[job.outcome] ?? 'jobUnknown'
					)}</strong
				>{#if job.message}<span
						>{job.outcome === 'lost'
							? $t('jobWorkerStopped')
							: job.kind === 'carry_forward'
								? $t('carryFailed')
								: job.kind === 'calendar_sync' && job.outcome !== 'cancelled'
									? providerStatusMessage(job.message, $t)
									: $t('jobDetails')}</span
					>{/if}
			</li>{/each}
	</ul>
</section>
