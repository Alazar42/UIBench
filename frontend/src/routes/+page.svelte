<script>
	import Login from '$lib/components/Login.svelte';
</script>

<main class=" flex h-screen w-screen flex-col justify-between gap-6 px-12 py-16 lg:flex-row">
	<div class="flex flex-col items-center justify-center text-center lg:items-start lg:text-start">
		<h3 class="mb-6 text-2xl md:text-4xl"><strong>UIB</strong>ench</h3>
		<h1 class="mb-6 text-5xl leading-[1.125] tracking-tighter md:text-7xl">
			GET VALUEABLE INSIGHTS
		</h1>
		<p class="mb-6 max-w-3xl text-2xl md:text-3xl">
			With automated reports on the <strong>aesthetics</strong>, <strong>accessibility</strong> and
			<strong>performance</strong> of your site
		</p>
	</div>
	<Login />
</main>
