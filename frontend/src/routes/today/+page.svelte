<script lang="ts">
	import { resolve } from '$app/paths';
	import { afterNavigate, goto } from '$app/navigation';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import { api, ApiError, message, providerStatusMessage, write } from '$lib/api';
	import { language, t } from '$lib/i18n';
	import { clock, formatDate, localDate, minutes } from '$lib/format';
	import TaskEditor from '$lib/TaskEditor.svelte';
	import type { Day, Task } from '$lib/types';
	let data = $state<Day | null>(null);
	let backlog = $state<Task[]>([]);
	let backlogTotal = $state(0);
	let error = $state<unknown>(null);
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
			error = null;
		} catch (cause) {
			if (current !== generation || (cause instanceof Error && cause.name === 'AbortError')) return;
			if (cause instanceof ApiError && cause.status === 403 && !data) {
				await goto(resolve('/login'));
				return;
			}
			error = cause;
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
		error = null;
		try {
			await action();
			await refresh();
		} catch (cause) {
			error = cause;
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
			error = cause;
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

<svelte:head><title>{$t('pageTitle', { page: $t('today') })}</title></svelte:head>
<div class="today-view">
	<header class="page-heading">
		<div>
			<span class="eyebrow">{$t('todayEyebrow')}</span>
			<h1>{$t('todayHeading')}</h1>
			<p class="muted">{$t('todayIntro')}</p>
		</div>
		<div class="heading-actions">
			<label
				>{$t('planDate')}<input
					type="date"
					value={data?.date ?? selectedDay}
					onchange={(event) => goto(resolve(`/today?date=${event.currentTarget.value}`))}
				/></label
			><a class="button quiet" href={resolve('/today')}>{$t('today')}</a><button
				class="primary"
				disabled={!data || pending}
				onclick={() => (editing = null)}>{$t('newTask')}</button
			>
		</div>
	</header>
	{#if error}<div role="alert" class="error">
			{message(error, $t)} <button onclick={() => refresh()}>{$t('refreshDay')}</button>
			<a href={resolve('/login')}>{$t('signIn')}</a>
		</div>{/if}
	{#if loading && !data}<p role="status">{$t('loadingDay')}</p>{/if}
	{#if data}
		<div class="metrics">
			<section class="panel">
				<span class="eyebrow">{$t('plannedWork')}</span><strong
					>{minutes(data.capacity.estimated_minutes, $t)}</strong
				><span
					>{$t('openTasks', { count: data.tasks.filter((task) => !task.completed_at).length })} · {$t(
						'withoutEstimate',
						{ count: data.capacity.unestimated_tasks }
					)}</span
				>
			</section>
			<section class="panel">
				<span class="eyebrow">{$t('availableCapacity')}</span><strong
					class:warning={data.capacity.remaining_minutes < 0}
					>{minutes(data.capacity.remaining_minutes, $t)}</strong
				><span
					>{$t('meetingCapacity', {
						meetings: minutes(data.capacity.meeting_minutes, $t),
						window: minutes(data.capacity.work_minutes, $t)
					})}</span
				>
			</section>
			<section class="panel">
				<span class="eyebrow">{$t('actualToday')}</span><strong
					>{minutes(data.day_actual_seconds / 60, $t)}</strong
				><span
					>{data.timer
						? $t('timerRunning', { time: minutes(elapsed / 60, $t) })
						: $t('ready')}</span
				>
			</section>
		</div>
		{#if data.timer}<div class="timer-bar" role="status">
				<span class="status-dot"></span><span
					>{$t('runningTask', {
						title:
							data.tasks.find((task) => task.id === data!.timer?.task)?.title ?? $t('anotherDay'),
						time: minutes(elapsed / 60, $t)
					})}</span
				><button
					disabled={pending}
					onclick={() => command(() => write(`/api/v1/timers/${data!.timer!.id}/stop/`))}
					>{$t('stopTimer')}</button
				>
			</div>{/if}
		<div class="planner-grid">
			<section class="panel task-panel">
				<div class="section-heading">
					<h2>{$t('yourDay')} <span class="count">{data.tasks.length}</span></h2>
					<span class="muted"
						>{formatDate(data.date, data.date_order, data.date_separator)} · {data.timezone}</span
					>
				</div>
				{#if !data.tasks.length}<div class="empty">
						<span class="empty-symbol">＋</span>
						<h3>{$t('emptyDay')}</h3>
						<p>{$t('emptyDayHint')}</p>
						<button onclick={() => (editing = null)}>{$t('firstTask')}</button>
					</div>{/if}
				<ol class="task-list">
					{#each data.tasks as task, index (task.id)}
						<li class:done={!!task.completed_at}>
							<button
								class="complete"
								aria-label={$t(task.completed_at ? 'reopenTask' : 'completeTask', {
									title: task.title
								})}
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
											? $t('noEstimate')
											: minutes(task.estimated_minutes, $t)}</span
									>{#if task.due_date}<span class="attention"
											>{$t('dueOn', {
												date: formatDate(task.due_date, data.date_order, data.date_separator)
											})}</span
										>{/if}{#if task.source}<span class="external"
											>↗ {task.source.provider === 'github'
												? $t('githubIssue')
												: task.source.provider === 'notion'
													? 'Notion'
													: task.source.provider}</span
										>{/if}<span
										>{$t('actualTime', {
											time: minutes((data.task_actual_seconds[task.id] ?? 0) / 60, $t)
										})}</span
									>
								</div>
							</div>
							<div class="task-actions">
								<button
									class="quiet"
									aria-label={$t('moveUp', { title: task.title })}
									disabled={pending || index === 0}
									onclick={() => move(task, -1)}>↑</button
								><button
									class="quiet"
									aria-label={$t('moveDown', { title: task.title })}
									disabled={pending || index === data!.tasks.length - 1}
									onclick={() => move(task, 1)}>↓</button
								><button
									disabled={pending || !!task.completed_at || !!data.timer}
									aria-label={$t('startTimer', { title: task.title })}
									onclick={() => command(() => write('/api/v1/timers/start/', { task: task.id }))}
									>▷</button
								><button
									class="quiet"
									aria-label={$t('trashTask', { title: task.title })}
									disabled={pending}
									onclick={() =>
										command(() =>
											write(`/api/v1/tasks/${task.id}/`, undefined, 'DELETE', task.version)
										)}>{$t('trash')}</button
								>
							</div>
						</li>
					{/each}
				</ol>
			</section>
			<aside class="panel meetings">
				<span class="eyebrow">{$t('meetingsEyebrow')}</span>
				<h2>{$t('calendarEvents')}</h2>
				{#if !data.events.length}<p class="muted">{$t('noDayMeetings')}</p>
					<a href={resolve('/connections')}>{$t('connectCalendar')}</a>{/if}
				{#each data.events as event (event.id)}<article class="meeting">
						<span class="external"
							>{event.starts_at
								? clock(event.starts_at, data.timezone, $language) +
									' – ' +
									clock(event.ends_at!, data.timezone, $language)
								: $t('allDay')}</span
						>
						<h3>{event.title}</h3>
						<small
							>{event.blocking && event.starts_at
								? $t('blocksTime')
								: $t('doesNotBlockTime')}</small
						>
					</article>{/each}
				{#each data.calendars as calendar (calendar.id)}<p
						class="freshness"
						class:error={!!calendar.last_error}
					>
						{calendar.label}: {calendar.last_error
							? providerStatusMessage(calendar.last_error, $t)
							: calendar.last_succeeded_at
								? $t('updatedAt', {
										time: clock(calendar.last_succeeded_at, data.timezone, $language)
									})
								: $t('waitingRefresh')}{!calendar.enabled ? ' · ' + $t('paused') : ''}
					</p>{/each}
				<p class="muted small">{$t('meetingsReadOnly')}</p>
			</aside>
		</div>
		<details class="panel">
			<summary>{$t('backlog', { count: backlogTotal })}</summary>
			<ul class="resource-list">
				{#each backlog as task (task.id)}<li>
						<div>
							<strong>{task.title}</strong>
							<p class="muted small">{task.completed_at ? $t('completed') : $t('notPlanned')}</p>
						</div>
						<div class="heading-actions">
							<button
								disabled={pending}
								onclick={() =>
									command(() =>
										write(
											`/api/v1/tasks/${task.id}/`,
											{ do_date: data!.date },
											'PATCH',
											task.version
										)
									)}>{$t('planThisDay')}</button
							><button disabled={pending} onclick={() => (editing = task)}>{$t('editTask')}</button>
						</div>
					</li>{/each}
			</ul>
			{#if !backlog.length}<p class="muted">{$t('backlogEmpty')}</p>{/if}
			{#if backlog.length < backlogTotal}<button disabled={pending} onclick={moreBacklog}
					>{$t('moreBacklog')}</button
				>{/if}
		</details>
		{#if editing !== undefined}{#key editing?.id ?? 'new'}<TaskEditor
					task={editing}
					day={data.date}
					onbusy={(busy: boolean) => {
						pending = busy;
					}}
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
</div>
