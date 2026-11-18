<script lang="ts">
	import { resolve } from '$app/paths';
	import { afterNavigate, goto } from '$app/navigation';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import { api, ApiError, message, write } from '$lib/api';
	import { clock, localDate, minutes } from '$lib/format';
	import TaskEditor from '$lib/TaskEditor.svelte';
	import type { Day, Task } from '$lib/types';
	let data = $state<Day | null>(null);
	let backlog = $state<Task[]>([]);
	let backlogTotal = $state(0);
	let error = $state('');
	let pending = $state(false);
	let loading = $state(true);
	let editing = $state<Task | null | undefined>(undefined);
	let now = $state(Date.now());
	let controller: AbortController | undefined;
	let generation = 0;
	const selectedDay = $derived(page.url.searchParams.get('date') ?? '');
	const elapsed = $derived(
		data?.timer ? Math.max(0, Math.floor((now - Date.parse(data.timer.started_at)) / 1000)) : 0
	);
	async function refresh(day = selectedDay) {
		controller?.abort();
		controller = new AbortController();
		const current = ++generation;
		try {
			const [result, unplanned] = await Promise.all([
				api<Day>(`/api/v1/day/${day ? '?date=' + day : ''}`, { signal: controller.signal }),
				api<{ results: Task[]; count: number }>('/api/v1/tasks/?backlog=true&limit=100', {
					signal: controller.signal
				})
			]);
			if (current !== generation) return;
			data = result;
			backlog = unplanned.results;
			backlogTotal = unplanned.count;
			error = '';
		} catch (cause) {
			if (current !== generation || (cause instanceof Error && cause.name === 'AbortError')) return;
			if (cause instanceof ApiError && cause.status === 403 && !data) {
				await goto(resolve('/login'));
				return;
			}
			error = message(cause);
		} finally {
			if (current === generation) loading = false;
		}
	}
	afterNavigate(() => {
		editing = undefined;
		loading = true;
		data = null;
		void refresh(page.url.searchParams.get('date') ?? '');
	});
	onMount(() => {
		const tick = setInterval(() => {
			now = Date.now();
		}, 1000);
		const poll = setInterval(() => {
			if (!pending && editing === undefined) {
				if (!selectedDay && data && localDate(new Date(), data.timezone) !== data.date) data = null;
				void refresh();
			}
		}, 30000);
		const visible = () => {
			if (document.visibilityState === 'visible' && editing === undefined) void refresh();
		};
		document.addEventListener('visibilitychange', visible);
		return () => {
			clearInterval(tick);
			clearInterval(poll);
			controller?.abort();
			document.removeEventListener('visibilitychange', visible);
		};
	});
	async function command(action: () => Promise<unknown>) {
		if (pending) return;
		pending = true;
		error = '';
		try {
			await action();
			await refresh();
		} catch (cause) {
			error = message(cause);
		} finally {
			pending = false;
		}
	}
	async function moreBacklog() {
		if (pending) return;
		pending = true;
		try {
			const result = await api<{ results: Task[] }>(
				'/api/v1/tasks/?backlog=true&limit=100&offset=' + backlog.length
			);
			backlog = [...backlog, ...result.results];
		} catch (cause) {
			error = message(cause);
		} finally {
			pending = false;
		}
	}
	function move(task: Task, direction: number) {
		if (!data) return;
		const tasks = [...data.tasks];
		const index = tasks.findIndex((candidate) => candidate.id === task.id);
		const target = index + direction;
		if (target < 0 || target >= tasks.length) return;
		[tasks[index], tasks[target]] = [tasks[target], tasks[index]];
		void command(() =>
			write('/api/v1/tasks/reorder/', {
				date: data!.date,
				items: tasks.map(({ id, version }) => ({ id, version }))
			})
		);
	}
</script>

<svelte:head><title>Today · Cyber Beacon</title></svelte:head>
<header class="page-heading">
	<div>
		<span class="eyebrow">DAILY FLIGHT PLAN</span>
		<h1>Make room for what matters.</h1>
		<p class="muted">Choose your work. Leave space to do it.</p>
	</div>
	<div class="heading-actions">
		<label
			>Plan date<input
				type="date"
				value={data?.date ?? selectedDay}
				onchange={(event) => goto(resolve(`/today?date=${event.currentTarget.value}`))}
			/></label
		><a class="button quiet" href={resolve('/today')}>Today</a><button
			class="primary"
			disabled={!data || pending}
			onclick={() => (editing = null)}>New Task</button
		>
	</div>
</header>
{#if error}<div role="alert" class="error">
		{error} <button onclick={() => refresh()}>Refresh day</button>
		<a href={resolve('/login')}>Sign in</a>
	</div>{/if}
{#if loading && !data}<p role="status">Loading your day…</p>{/if}
{#if data}
	<div class="metrics">
		<section class="panel">
			<span class="eyebrow">PLANNED WORK</span><strong
				>{minutes(data.capacity.estimated_minutes)}</strong
			><span
				>{data.tasks.filter((task) => !task.completed_at).length} open Tasks · {data.capacity
					.unestimated_tasks} without estimates</span
			>
		</section>
		<section class="panel">
			<span class="eyebrow">AVAILABLE CAPACITY</span><strong
				class:warning={data.capacity.remaining_minutes < 0}
				>{minutes(data.capacity.remaining_minutes)}</strong
			><span
				>{minutes(data.capacity.meeting_minutes)} in meetings · {minutes(
					data.capacity.work_minutes
				)} work window</span
			>
		</section>
		<section class="panel">
			<span class="eyebrow">ACTUAL TIME TODAY</span><strong
				>{minutes(data.day_actual_seconds / 60)}</strong
			><span>{data.timer ? 'Timer running · ' + minutes(elapsed / 60) : 'Ready when you are'}</span>
		</section>
	</div>
	{#if data.timer}<div class="timer-bar" role="status">
			<span class="status-dot"></span><span
				>Running: {data.tasks.find((task) => task.id === data!.timer?.task)?.title ??
					'Task on another day'} · {minutes(elapsed / 60)}</span
			><button
				disabled={pending}
				onclick={() => command(() => write(`/api/v1/timers/${data!.timer!.id}/stop/`))}
				>Stop timer</button
			>
		</div>{/if}
	<div class="planner-grid">
		<section class="panel task-panel">
			<div class="section-heading">
				<h2>Your day <span class="count">{data.tasks.length}</span></h2>
				<span class="muted">{data.date} · {data.timezone}</span>
			</div>
			{#if !data.tasks.length}<div class="empty">
					<span class="empty-symbol">＋</span>
					<h3>A little breathing room.</h3>
					<p>Add a Task or bring one in from Notion.</p>
					<button onclick={() => (editing = null)}>Create your first Task</button>
				</div>{/if}
			<ol class="task-list">
				{#each data.tasks as task, index (task.id)}
					<li class:done={!!task.completed_at}>
						<button
							class="complete"
							aria-label={`${task.completed_at ? 'Reopen' : 'Complete'} ${task.title}`}
							aria-pressed={!!task.completed_at}
							disabled={pending}
							onclick={() =>
								command(() =>
									write(
										`/api/v1/tasks/${task.id}/`,
										{ completed: !task.completed_at },
										'PATCH',
										task.version
									)
								)}>{task.completed_at ? '✓' : '○'}</button
						>
						<div class="task-content">
							<button class="task-title" disabled={pending} onclick={() => (editing = task)}
								>{task.title}</button
							>
							<div class="task-meta">
								<span
									>{task.estimated_minutes === null
										? 'No estimate'
										: minutes(task.estimated_minutes)}</span
								>{#if task.due_date}<span class="attention">Due {task.due_date}</span
									>{/if}{#if task.source}<span class="external">↗ Notion</span>{/if}<span
									>{minutes((data.task_actual_seconds[task.id] ?? 0) / 60)} actual</span
								>
							</div>
						</div>
						<div class="task-actions">
							<button
								class="quiet"
								aria-label={`Move ${task.title} up`}
								disabled={pending || index === 0}
								onclick={() => move(task, -1)}>↑</button
							><button
								class="quiet"
								aria-label={`Move ${task.title} down`}
								disabled={pending || index === data!.tasks.length - 1}
								onclick={() => move(task, 1)}>↓</button
							><button
								disabled={pending || !!task.completed_at || !!data.timer}
								aria-label={`Start timer for ${task.title}`}
								onclick={() => command(() => write('/api/v1/timers/start/', { task: task.id }))}
								>▷</button
							><button
								class="quiet"
								aria-label={`Trash ${task.title}`}
								disabled={pending}
								onclick={() =>
									command(() =>
										write(`/api/v1/tasks/${task.id}/`, undefined, 'DELETE', task.version)
									)}>Trash</button
							>
						</div>
					</li>
				{/each}
			</ol>
		</section>
		<aside class="panel meetings">
			<span class="eyebrow">AROUND YOUR WORK</span>
			<h2>Calendar events</h2>
			{#if !data.events.length}<p class="muted">No meetings in this day’s calendar data.</p>
				<a href={resolve('/connections')}>Connect a calendar →</a>{/if}
			{#each data.events as event (event.id)}<article class="meeting">
					<span class="external"
						>{event.starts_at
							? clock(event.starts_at, data.timezone) + ' – ' + clock(event.ends_at!, data.timezone)
							: 'All day'}</span
					>
					<h3>{event.title}</h3>
					<small
						>{event.blocking && event.starts_at
							? 'Counts toward capacity'
							: 'Does not reduce capacity'}</small
					>
				</article>{/each}
			{#each data.calendars as calendar (calendar.id)}<p
					class="freshness"
					class:error={!!calendar.last_error}
				>
					{calendar.label}: {calendar.last_error ||
						(calendar.last_succeeded_at
							? 'Updated ' + clock(calendar.last_succeeded_at, data.timezone)
							: 'Waiting for first refresh')}{!calendar.enabled ? ' · paused' : ''}
				</p>{/each}
			<p class="muted small">Meetings stay read-only. Your Task list stays yours.</p>
		</aside>
	</div>
	<details class="panel">
		<summary>Backlog · {backlogTotal} Tasks without a do date</summary>
		<ul class="resource-list">
			{#each backlog as task (task.id)}<li>
					<div>
						<strong>{task.title}</strong>
						<p class="muted small">{task.completed_at ? 'Completed' : 'Not assigned to a day'}</p>
					</div>
					<div class="heading-actions">
						<button
							disabled={pending}
							onclick={() =>
								command(() =>
									write(`/api/v1/tasks/${task.id}/`, { do_date: data!.date }, 'PATCH', task.version)
								)}>Plan for this day</button
						><button disabled={pending} onclick={() => (editing = task)}>Edit Task</button>
					</div>
				</li>{/each}
		</ul>
		{#if !backlog.length}<p class="muted">No Tasks waiting for a day.</p>{/if}
		{#if backlog.length < backlogTotal}<button disabled={pending} onclick={moreBacklog}
				>Load more Backlog Tasks</button
			>{/if}
	</details>
	{#if editing !== undefined}{#key editing?.id ?? 'new'}<TaskEditor
				task={editing}
				day={data.date}
				onbusy={(busy) => (pending = busy)}
				onsaved={async () => {
					pending = true;
					editing = undefined;
					try {
						await refresh();
					} finally {
						pending = false;
					}
				}}
				oncancel={() => (editing = undefined)}
			/>{/key}{/if}
{/if}
