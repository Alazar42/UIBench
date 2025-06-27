<script lang="ts">
	import Login from '$lib/components/Login.svelte';
</script>

<main
	class=" flex h-screen w-screen flex-col items-center gap-6 px-12 py-16 xl:flex-row xl:justify-between"
>
	<div class="flex flex-col items-center justify-center text-center xl:items-start xl:text-start">
		<h3 class="mb-6 text-xl md:text-2xl xl:text-4xl"><strong>UIB</strong>ench</h3>
		<h1 class="mb-6 text-2xl leading-[1.125] tracking-tighter md:text-5xl xl:text-7xl">
			GET VALUEABLE INSIGHTS
		</h1>
		<p class="mb-6 max-w-3xl text-xl md:text-2xl xl:text-3xl">
			With automated reports on the <strong>aesthetics</strong>, <strong>accessibility</strong> and
			<strong>performance</strong> of your site
		</p>
	</div>
	<Login />
</main>
