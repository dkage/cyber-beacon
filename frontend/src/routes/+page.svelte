<script lang="ts">
	import { resolve } from '$app/paths';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	onMount(() => {
		void goto(resolve('/today'), { replaceState: true });
	});
</script>

<p>Opening your day… <a href={resolve('/today')}>Go to Today</a></p>
