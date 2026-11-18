<script lang="ts">
	import { untrack } from 'svelte';
	import { api, ApiError, message, write } from '$lib/api';
	import type { Task } from '$lib/types';
	import { safeUrl } from '$lib/format';
	let {
		task = null,
		day,
		onsaved,
		oncancel,
		onbusy = () => {}
	}: {
		task?: Task | null;
		day: string;
		onsaved: () => void | Promise<void>;
		oncancel: () => void;
		onbusy?: (busy: boolean) => void;
	} = $props();
	const initial = untrack(() => ({ task, day }));
	let version = $state(initial.task?.version);
	let title = $state(initial.task?.title ?? '');
	let notes = $state(initial.task?.notes ?? '');
	let doDate = $state(initial.task?.do_date ?? initial.day);
	let dueDate = $state(initial.task?.due_date ?? '');
	let startDate = $state(initial.task?.start_date ?? '');
	let estimate = $state<number | undefined>(initial.task?.estimated_minutes ?? undefined);
	let priority = $state<number | undefined>(initial.task?.priority ?? undefined);
	let error = $state('');
	let pending = $state(false);
	async function save(event: SubmitEvent) {
		event.preventDefault();
		if (pending) return;
		pending = true;
		onbusy(true);
		error = '';
		try {
			const draft = {
				title,
				notes,
				do_date: doDate || null,
				due_date: dueDate || null,
				start_date: startDate || null,
				estimated_minutes: estimate ?? null,
				priority: priority ?? null
			};
			const changes = task
				? Object.fromEntries(
						Object.entries(draft).filter(
							([key, value]) => value !== initial.task?.[key as keyof Task]
						)
					)
				: draft;
			await write(
				task ? `/api/v1/tasks/${task.id}/` : '/api/v1/tasks/',
				changes,
				task ? 'PATCH' : 'POST',
				version
			);
			await onsaved();
		} catch (cause) {
			error = message(cause);
			if (cause instanceof ApiError && cause.status === 412 && task) {
				try {
					version = (await api<Task>(`/api/v1/tasks/${task.id}/`)).version;
					error += ' Latest version loaded. Review your draft before saving again.';
				} catch {
					error += ' Could not refresh the Task.';
				}
			}
		} finally {
			pending = false;
			onbusy(false);
		}
	}
</script>

<section class="panel editor" aria-label={task ? 'Edit Task' : 'New Task'}>
	<div class="section-heading">
		<h2>{task ? 'Edit Task' : 'New Task'}</h2>
		<button type="button" class="quiet" disabled={pending} onclick={oncancel}>Close editor</button>
	</div>
	<form onsubmit={save}>
		<label>Title<input bind:value={title} required maxlength="500" /></label>
		<label>Notes<textarea bind:value={notes} rows="4" maxlength="20000"></textarea></label>
		<div class="form-grid">
			<label>Do date<input type="date" bind:value={doDate} /></label><label
				>Due date<input type="date" bind:value={dueDate} /></label
			><label>Start date<input type="date" bind:value={startDate} /></label>
			<label
				>Estimate (minutes)<input type="number" min="0" max="10080" bind:value={estimate} /></label
			><label>Priority (0–5)<input type="number" min="0" max="5" bind:value={priority} /></label>
		</div>
		{#if task?.source}<details class="source">
				<summary>Source preview · {task.source.provider}</summary>{#if safeUrl(task.source.url)}<a
						href={safeUrl(task.source.url)}
						target="_blank"
						rel="external noreferrer">Open source</a
					>{/if}
				<pre>{JSON.stringify(task.source.raw, null, 2)}</pre>
				<p>Your edits belong to this worksheet.</p>
			</details>{/if}
		{#if error}<p class="error" role="alert">{error}</p>{/if}
		<button class="primary" disabled={pending}>{pending ? 'Saving…' : 'Save Task'}</button>
	</form>
</section>
