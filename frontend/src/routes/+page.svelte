<script lang="ts">
	import { t } from '$lib/i18n';
	import { resolve } from '$app/paths';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	onMount(() => {
		void goto(resolve('/today'), { replaceState: true });
	});
</script>

<p>{$t('openingDay')} <a href={resolve('/today')}>{$t('goToday')}</a></p>
