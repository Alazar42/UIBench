<script lang="ts">
	import reportData from '$lib/data/report.json';

	const { project } = reportData;
	const evaluations = project.evaluation;
</script>

<main class="min-h-screen bg-gray-100 p-8">
	<h1 class="mb-8 text-center text-4xl font-extrabold text-gray-800">{project.name}</h1>

	<div class="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
		{#each Object.entries(evaluations) as [category, details]}
			<section class="rounded-2xl bg-white p-6 shadow-lg transition-shadow hover:shadow-xl">
				<header class="mb-4 flex items-center justify-between">
					<h2 class="text-2xl font-semibold capitalize text-gray-700">{category}</h2>
					<span class="text-3xl font-bold text-blue-600">{details.score}</span>
				</header>

				<div class="space-y-4">
					<div>
						<h3 class="text-lg font-medium text-gray-600">Issues</h3>
						<ul class="mt-2 space-y-2">
							{#each details.issues as issue}
								<li class="rounded border-l-4 border-red-500 bg-red-50 p-4">
									<p class="font-semibold text-red-800">{issue.id}: {issue.description}</p>
									<p class="text-sm text-red-600">Impact: {issue.impact}</p>
								</li>
							{/each}
						</ul>
					</div>

					<div>
						<h3 class="text-lg font-medium text-gray-600">Recommendations</h3>
						<ul class="mt-2 list-inside list-disc space-y-1">
							{#each details.recommendations as rec}
								<li class="text-gray-700">{rec.id}: {rec.description}</li>
							{/each}
						</ul>
					</div>
				</div>
			</section>
		{/each}
	</div>
</main>

<style>
	/* Optional: customize scrollbar for aesthetic touch */
	main::-webkit-scrollbar {
		width: 8px;
	}
	main::-webkit-scrollbar-thumb {
		background-color: rgba(100, 116, 139, 0.4);
		border-radius: 4px;
	}
</style>
