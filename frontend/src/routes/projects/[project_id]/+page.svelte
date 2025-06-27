<script lang="ts">
	import { onMount } from 'svelte';
	import type { ProjectResult } from '$lib/types';

	const { data } = $props<{ project: ProjectResult }>();

	let projectData: ProjectResult | null = $state(null);

	onMount(() => {
		if (data && data.project) {
			projectData = data.project;
		}
	});
</script>

<main class="container mx-auto p-8">
	<a href="/home" class="mb-4 inline-flex items-center text-blue-600 hover:underline">
		<svg
			xmlns="http://www.w3.org/2000/svg"
			class="mr-2 h-4 w-4"
			fill="none"
			viewBox="0 0 24 24"
			stroke="currentColor"
		>
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="2"
				d="M10 19l-7-7m0 0l7-7m-7 7h18"
			/>
		</svg>
		Back to All Projects
	</a>

	{#if projectData && projectData.result}
		<h1 class="mb-2 text-4xl font-extrabold text-gray-900">Project: {projectData.project_id}</h1>
		<p class="mb-6 text-lg text-gray-600">
			URL: <a
				href={projectData.url}
				target="_blank"
				rel="noopener noreferrer"
				class="text-blue-600 hover:underline">{projectData.url}</a
			>
		</p>

		<div class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
			{#each Object.entries(projectData.result.results) as [analyzerName, analyzerData]}
				{#if analyzerData && typeof analyzerData === 'object' && 'overall_score' in analyzerData}
					<div class="rounded-lg bg-white p-6 shadow-md">
						<h2 class="mb-3 text-2xl font-semibold text-gray-800">
							{analyzerName.replace(/([A-Z])/g, ' $1').trim()}
						</h2>
						<p class="mb-4 text-xl font-bold text-purple-700">
							Score: {Math.round(analyzerData.overall_score * 100) / 100}
						</p>

						{#if analyzerData.metrics && Object.keys(analyzerData.metrics).length > 0}
							<h3 class="mb-2 text-lg font-medium text-gray-700">Metrics:</h3>
							<ul class="mb-4 list-disc pl-5 text-gray-700">
								{#each Object.entries(analyzerData.metrics) as [metricName, metricValue]}
									<li>{metricName}: {JSON.stringify(metricValue)}</li>
								{/each}
							</ul>
						{/if}

						{#if analyzerData.issues && analyzerData.issues.length > 0}
							<h3 class="mb-2 text-lg font-medium text-red-600">Issues:</h3>
							<ul class="mb-4 list-disc pl-5 text-gray-700">
								{#each analyzerData.issues.slice(0, 5) as issue}
									<li>{typeof issue === 'string' ? issue : JSON.stringify(issue)}</li>
								{/each}
								{#if analyzerData.issues.length > 5}
									<li>...and {analyzerData.issues.length - 5} more issues</li>
								{/if}
							</ul>
						{/if}

						{#if analyzerData.recommendations && analyzerData.recommendations.length > 0}
							<h3 class="mb-2 text-lg font-medium text-green-600">Recommendations:</h3>
							<ul class="mb-4 list-disc pl-5 text-gray-700">
								{#each analyzerData.recommendations.slice(0, 5) as recommendation}
									<li>{recommendation}</li>
								{/each}
								{#if analyzerData.recommendations.length > 5}
									<li>...and {analyzerData.recommendations.length - 5} more recommendations</li>
								{/if}
							</ul>
						{/if}

						{#if analyzerData.details && Object.keys(analyzerData.details).length > 0}
							<details class="mt-4">
								<summary class="cursor-pointer text-blue-600 hover:underline"
									>View Full Details</summary
								>
								<pre class="mt-2 overflow-auto rounded-md bg-gray-50 p-3 text-xs">
									{JSON.stringify(analyzerData.details, null, 2)}
								</pre>
							</details>
						{/if}
					</div>
				{/if}
			{/each}
		</div>
	{:else}
		<p class="text-center text-gray-500">Loading project data or project not found...</p>
	{/if}
</main>
