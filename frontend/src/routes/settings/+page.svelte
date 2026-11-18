<script lang="ts">
	import { resolve } from '$app/paths';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api, ApiError, message, write } from '$lib/api';
	import type { Settings, Task } from '$lib/types';
	interface Device {
		id: string;
		label: string;
		expires_at: string;
		revoked_at: string | null;
	}
	interface Job {
		id: number;
		kind: string;
		outcome: string;
		message: string;
		started_at: string;
	}
	let settings = $state<Settings | null>(null);
	let devices = $state<Device[]>([]);
	let jobs = $state<Job[]>([]);
	let trash = $state<Task[]>([]);
	let error = $state('');
	let notice = $state('');
	let pending = $state(false);
	let code = $state('');
	let label = $state('Office display');
	const weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
	async function load() {
		try {
			settings = await api<Settings>('/api/v1/settings/');
			if (!settings.work_weekdays.length) settings.work_weekdays = [0, 1, 2, 3, 4];
			devices = await api<Device[]>('/api/v1/kiosk/devices/');
			jobs = (await api<{ results: Job[] }>('/api/v1/jobs/?limit=20')).results;
			trash = (await api<{ results: Task[] }>('/api/v1/tasks/?trash=true&limit=100')).results;
		} catch (cause) {
			if (cause instanceof ApiError && cause.status === 403) await goto(resolve('/login'));
			else error = message(cause);
		}
	}
	onMount(() => {
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
</script>

<svelte:head><title>Settings · Cyber Beacon</title></svelte:head>
<header class="page-heading">
	<div>
		<span class="eyebrow">YOUR OPERATING RHYTHM</span>
		<h1>A day that fits you.</h1>
		<p class="muted">Work hours, connected displays, and background health.</p>
	</div>
</header>
{#if error}<p role="alert" class="error">{error}</p>{/if}{#if notice}<p
		role="status"
		class="success"
	>
		{notice}
	</p>{/if}
<div class="connection-grid">
	{#if settings}<section class="panel">
			<h2>Work hours</h2>
			<p class="muted">{settings.email}</p>
			<form
				onsubmit={(event) => {
					event.preventDefault();
					void action(async () => {
						await write('/api/v1/settings/', settings, 'PATCH');
						notice = 'Work hours saved.';
					});
				}}
			>
				<label
					>Timezone<input
						bind:value={settings.timezone}
						required
						placeholder="America/Sao_Paulo"
					/></label
				>
				<div class="form-grid">
					<label>Work starts<input type="time" bind:value={settings.work_start} required /></label
					><label>Work ends<input type="time" bind:value={settings.work_end} required /></label>
				</div>
				<fieldset>
					<legend>Working days</legend>{#each weekdays as name, index (name)}<label
							class="check-label"
							><input
								type="checkbox"
								value={index}
								bind:group={settings.work_weekdays}
							/>{name}</label
						>{/each}
				</fieldset>
				<button class="primary" disabled={pending}>Save work hours</button>
			</form>
		</section>{/if}
	<section class="panel">
		<h2>Pair a display</h2>
		<p class="muted">
			Open <a href={resolve('/kiosk')}>Kiosk</a> on the TV, then enter its code here. Devices receive
			read-only access for 90 days.
		</p>
		<form
			onsubmit={(event) => {
				event.preventDefault();
				void action(async () => {
					await write('/api/v1/kiosk/pair/approve/', { code: code.toUpperCase(), label });
					code = '';
					await load();
					notice = 'Display approved.';
				});
			}}
		>
			<label
				>Pairing code<input
					bind:value={code}
					minlength="8"
					maxlength="8"
					required
					autocomplete="off"
				/></label
			><label>Display name<input bind:value={label} maxlength="100" required /></label><button
				disabled={pending}>Approve display</button
			>
		</form>
		{#each devices as device (device.id)}<article class="mount">
				<strong>{device.label}</strong>
				<p class="muted small">
					{device.revoked_at
						? 'Revoked'
						: 'Expires ' + new Date(device.expires_at).toLocaleDateString()}
				</p>
				<button
					disabled={pending || !!device.revoked_at}
					onclick={() =>
						action(async () => {
							await write(`/api/v1/kiosk/devices/${device.id}/revoke/`);
							await load();
						})}>Revoke display</button
				>
			</article>{/each}
	</section>
</div>
<section class="panel">
	<h2>Trash</h2>
	<p class="muted">Restoring preserves the original dates and history.</p>
	{#if !trash.length}<p>No Tasks in trash.</p>{/if}
	<ul class="resource-list">
		{#each trash as task (task.id)}<li>
				<span>{task.title}</span><button
					disabled={pending}
					onclick={() =>
						action(async () => {
							await write(`/api/v1/tasks/${task.id}/restore/`, undefined, 'POST', task.version);
							await load();
							notice = 'Task restored.';
						})}>Restore Task</button
				>
			</li>{/each}
	</ul>
</section>
<section class="panel">
	<h2>Background health</h2>
	{#if !jobs.length}<p class="muted">No Job runs recorded yet.</p>{/if}
	<ul class="job-list">
		{#each jobs as job (job.id)}<li class:error={job.outcome !== 'success'}>
				<time>{new Date(job.started_at).toLocaleString()}</time><strong
					>{job.kind} · {job.outcome}</strong
				>{#if job.message}<span>{job.message}</span>{/if}
			</li>{/each}
	</ul>
</section>
