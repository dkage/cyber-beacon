<script lang="ts">
	import { onMount, untrack } from 'svelte';
	import { api, ApiError, fieldErrorProps, message, write } from '$lib/api';
	import type { Task } from '$lib/types';
	import { t } from '$lib/i18n';
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
	let doDate = $state(initial.task ? (initial.task.do_date ?? '') : initial.day);
	let dueDate = $state(initial.task?.due_date ?? '');
	let startDate = $state(initial.task?.start_date ?? '');
	let estimate = $state<number | undefined>(initial.task?.estimated_minutes ?? undefined);
	let priority = $state<number | undefined>(initial.task?.priority ?? undefined);
	let error = $state<unknown>(null);
	let errorHint = $state<'taskRefreshed' | 'taskRefreshFailed' | null>(null);
	let pending = $state(false);
	let dialog: HTMLDialogElement;
	let titleInput: HTMLInputElement;
	onMount(() => {
		dialog.showModal();
		titleInput.focus();
		return () => {
			if (dialog.open) dialog.close();
		};
	});
	function dismiss(event: Event) {
		event.preventDefault();
		if (!pending) oncancel();
	}
	async function save(event: SubmitEvent) {
		event.preventDefault();
		if (pending) return;
		pending = true;
		onbusy(true);
		error = null;
		errorHint = null;
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
			error = cause;
			if (cause instanceof ApiError && cause.status === 412 && task) {
				try {
					version = (await api<Task>(`/api/v1/tasks/${task.id}/`)).version;
					errorHint = 'taskRefreshed';
				} catch {
					errorHint = 'taskRefreshFailed';
				}
			}
		} finally {
			pending = false;
			onbusy(false);
		}
	}
</script>

<dialog
	class="task-dialog"
	bind:this={dialog}
	aria-labelledby="task-editor-title"
	oncancel={dismiss}
	onclick={(event) => {
		if (event.target === dialog && !pending) oncancel();
	}}
>
	<section class="panel editor">
		<div class="section-heading">
			<h2 id="task-editor-title">{task ? $t('editTask') : $t('newTask')}</h2>
			<button type="button" class="quiet" disabled={pending} onclick={oncancel}
				>{$t('closeEditor')}</button
			>
		</div>
		<form onsubmit={save}>
			<label
				>{$t('title')}<input
					bind:this={titleInput}
					bind:value={title}
					{...fieldErrorProps(error, 'title', 'task-editor-error')}
					required
					maxlength="500"
				/></label
			>
			<label
				>{$t('notes')}<textarea
					bind:value={notes}
					{...fieldErrorProps(error, 'notes', 'task-editor-error')}
					rows="4"
					maxlength="20000"></textarea></label
			>
			<div class="form-grid">
				<label
					>{$t('doDate')}<input
						type="date"
						bind:value={doDate}
						{...fieldErrorProps(error, 'do_date', 'task-editor-error')}
					/></label
				><label
					>{$t('dueDate')}<input
						type="date"
						bind:value={dueDate}
						{...fieldErrorProps(error, 'due_date', 'task-editor-error')}
					/></label
				><label
					>{$t('startDate')}<input
						type="date"
						bind:value={startDate}
						{...fieldErrorProps(error, 'start_date', 'task-editor-error')}
					/></label
				>
				<label
					>{$t('estimate')}<input
						type="number"
						min="0"
						max="10080"
						bind:value={estimate}
						{...fieldErrorProps(error, 'estimated_minutes', 'task-editor-error')}
					/></label
				><label
					>{$t('priority')}<input
						type="number"
						min="0"
						max="5"
						bind:value={priority}
						{...fieldErrorProps(error, 'priority', 'task-editor-error')}
					/></label
				>
			</div>
			{#if task?.source}<details class="source">
					<summary>{$t('sourcePreview', { provider: task.source.provider })}</summary
					>{#if safeUrl(task.source.url)}<a
							href={safeUrl(task.source.url)}
							target="_blank"
							rel="external noreferrer">{$t('openSource')}</a
						>{/if}
					<pre>{JSON.stringify(task.source.raw, null, 2)}</pre>
					<p>{$t('worksheetEdits')}</p>
				</details>{/if}
			{#if error}<p id="task-editor-error" class="error" role="alert">
					{message(error, $t)}
					{errorHint ? $t(errorHint) : ''}
				</p>{/if}
			<button class="primary" disabled={pending}>{pending ? $t('saving') : $t('saveTask')}</button>
		</form>
	</section>
</dialog>
