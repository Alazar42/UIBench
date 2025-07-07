<script lang="ts">
	import { onMount } from 'svelte';
	import type { AnalysisResult, AResult } from '$lib/types';

	const { data } = $props<{ project: any; id: string; analysis: AnalysisResult }>();

	let cleanedData: AnalysisResult | null = $state(null);

	onMount(() => {
		if (data && data.project && data.analysis && data.analysis.result.results.results) {
			cleanedData = {
				status: data.analysis.status,
				url: data.project.url,
				name: data.project.name,
				results: {
					accessibility: {
						issues:
							data?.analysis?.result?.results?.results?.accessibility?.AccessibilityAnalyzer
								?.results?.issues ?? [],
						recommendations:
							data?.analysis?.result?.results?.results?.accessibility?.AccessibilityAnalyzer
								?.results?.recommendations ?? [],
						metrics: {
							names: Object.keys(
								data?.analysis?.result?.results?.results?.accessibility?.AccessibilityAnalyzer
									?.metrics ?? {}
							),
							scores: Object.values(
								data?.analysis?.result?.results?.results?.accessibility?.AccessibilityAnalyzer
									?.metrics ?? {}
							).map((item: any) =>
								Math.round((Number(item?.$numberDouble ?? item ?? 0) * 100) / 100)
							)
						},
						overall_score:
							data?.analysis?.result?.results?.results?.accessibility?.AccessibilityAnalyzer
								?.results?.overall_score,
						showMoreIssues: false,
						showMoreRecommendations: false
					},
					code: {
						issues: data?.analysis?.result?.results?.results?.code?.CodeAnalyzer?.results?.issues ?? [],
						recommendations:
							data?.analysis?.result?.results?.results?.code?.CodeAnalyzer?.results?.recommendations ?? [],
						metrics: {
							names: Object.keys(
								data?.analysis?.result?.results?.results?.code?.CodeAnalyzer?.results?.metrics ?? {}
							),
							scores: Object.values(
								data?.analysis?.result?.results?.results?.code?.CodeAnalyzer?.results?.metrics ?? {}
							).map((item: any) =>
								Math.round((Number(item?.$numberDouble ?? item ?? 0) * 100) / 100)
							)
						},
						overall_score:
							data?.analysis?.result?.results?.results?.code?.CodeAnalyzer?.results?.overall_score + Math.random(),
						showMoreIssues: false,
						showMoreRecommendations: false
					},
					compliance: {
						issues:
							data?.analysis?.result?.results?.results?.compliance?.ComplianceAnalyzer?.results?.issues ??
							[],
						recommendations:
							data?.analysis?.result?.results?.results?.compliance?.ComplianceAnalyzer
								?.results?.recommendations ?? [],
						metrics: {
							names: Object.keys(
								data?.analysis?.result?.results?.results?.compliance?.ComplianceAnalyzer?.results?.metrics ??
									{}
							),
							scores: Object.values(
								data?.analysis?.result?.results?.results?.compliance?.ComplianceAnalyzer?.results?.metrics ??
									{}
							).map((item: any) =>
								Math.round(
									(Number(
										item?.score?.$numberInt ??
											item?.score?.$numberDouble ??
											item?.score ??
											item ??
											0
									) *
										100) /
										100
								)
							)
						},
						overall_score:
							data?.analysis?.result?.results?.results?.compliance?.ComplianceAnalyzer
								?.results?.overall_score,
						showMoreIssues: false,
						showMoreRecommendations: false
					},
					design: {
						issues:
							data?.analysis?.result?.results?.results?.design?.DesignSystemAnalyzer?.results?.issues ?? [],
						recommendations:
							data?.analysis?.result?.results?.results?.design?.DesignSystemAnalyzer
								?.recommendations ?? [],
						metrics: {
							names: Object.keys(
								data?.analysis?.result?.results?.results?.design?.DesignSystemAnalyzer?.results?.metrics ??
									{}
							),
							scores: Object.values(
								data?.analysis?.result?.results?.results?.design?.DesignSystemAnalyzer?.results?.metrics ??
									{}
							).map((item: any) => Math.round((Number(item?.$numberInt ?? item ?? 0) * 100) / 100))
						},
						overall_score:
							data?.analysis?.result?.results?.results?.design?.DesignSystemAnalyzer?.results?.overall_score
								,
						showMoreIssues: false,
						showMoreRecommendations: false
					},
					infrastructure: {
						issues:
							data?.analysis?.result?.results?.results?.infrastructure?.InfrastructureAnalyzer
								?.results?.issues ?? [],
						recommendations:
							data?.analysis?.result?.results?.results?.infrastructure?.InfrastructureAnalyzer
								?.results?.recommendations ?? [],
						metrics: {
							names: Object.keys(
								data?.analysis?.result?.results?.results?.infrastructure?.InfrastructureAnalyzer
									?.metrics ?? {}
							),
							scores: Object.values(
								data?.analysis?.result?.results?.results?.infrastructure?.InfrastructureAnalyzer
									?.metrics ?? {}
							).map((item: any) =>
								Math.round(
									(Number(
										item?.score?.$numberInt ??
											item?.score?.$numberDouble ??
											item?.score ??
											item ??
											0
									) *
										100) /
										100
								)
							)
						},
						overall_score:
							data?.analysis?.result?.results?.results?.infrastructure?.InfrastructureAnalyzer
								?.results?.overall_score,
						showMoreIssues: false,
						showMoreRecommendations: false
					},
					performance: {
						issues:
							data?.analysis?.result?.results?.results?.performance?.PerformanceAnalyzer?.results?.issues ??
							[],
						recommendations:
							data?.analysis?.result?.results?.results?.performance?.PerformanceAnalyzer
								?.results?.recommendations ?? [],
						metrics: {
							names: Object.keys(
								data?.analysis?.result?.results?.results?.performance?.PerformanceAnalyzer
									?.metrics ?? {}
							),
							scores: Object.values(
								data?.analysis?.result?.results?.results?.performance?.PerformanceAnalyzer
									?.metrics ?? {}
							).map((item: any) =>
								Math.round(
									(Number(item?.$numberInt ?? item?.$numberDouble ?? item ?? 0) * 100) / 100
								)
							)
						},
						overall_score:
							data?.analysis?.result?.results?.results?.performance?.PerformanceAnalyzer
								?.results?.overall_score,
						showMoreIssues: false,
						showMoreRecommendations: false
					},
					seo: {
						issues: data?.analysis?.result?.results?.results?.seo?.SEOAnalyzer?.results?.issues ?? [],
						recommendations:
							data?.analysis?.result?.results?.results?.seo?.SEOAnalyzer?.results?.recommendations ?? [],
						metrics: {
							names: Object.keys(
								data?.analysis?.result?.results?.results?.seo?.SEOAnalyzer?.results?.metrics ?? {}
							),
							scores: Object.values(
								data?.analysis?.result?.results?.results?.seo?.SEOAnalyzer?.results?.metrics ?? {}
							).map((item: any) =>
								Math.round(
									(Number(
										item?.score?.$numberInt ??
											item?.score?.$numberDouble ??
											item?.score ??
											item ??
											0
									) *
										100) /
										100
								)
							)
						},
						overall_score:
							data?.analysis?.result?.results?.results?.seo?.SEOAnalyzer?.results?.overall_score
								,
						showMoreIssues: false,
						showMoreRecommendations: false
					},
					ux: {
						issues: data?.analysis?.result?.results?.results?.ux?.UXAnalyzer?.results?.issues ?? [],
						recommendations:
							data?.analysis?.result?.results?.results?.ux?.UXAnalyzer?.results?.recommendations ?? [],
						metrics: {
							names: Object.keys(
								data?.analysis?.result?.results?.results?.ux?.UXAnalyzer?.results?.metrics ?? {}
							),
							scores: Object.values(
								data?.analysis?.result?.results?.results?.ux?.UXAnalyzer?.results?.metrics ?? {}
							).map((item: any) =>
								Math.round(
									(Number(
										item?.score?.$numberInt ??
											item?.score?.$numberDouble ??
											item?.score ??
											item ??
											0
									) *
										100) /
										100
								)
							)
						},
						overall_score:
							data?.analysis?.result?.results?.results?.ux?.UXAnalyzer?.results?.overall_score,
						showMoreIssues: false,
						showMoreRecommendations: false
					}
				}
			};
		}
	});
	$inspect(cleanedData);
	$inspect(data.project);
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

	{#if cleanedData}
		<h1
			class="mb-2 line-clamp-3 max-w-prose text-ellipsis text-wrap text-4xl font-extrabold text-gray-900"
		>
			Project: {cleanedData?.name}
		</h1>
		<p class="mb-6 text-lg text-gray-600">
			URL: <a
				href={cleanedData?.url}
				target="_blank"
				rel="noopener noreferrer"
				class="text-blue-600 hover:underline">{cleanedData?.url}</a
			>
		</p>
		<div class=" w-full columns-1 gap-6 md:columns-2 md:gap-8 xl:columns-3">
			{#if cleanedData?.results.accessibility}
				{@render renderResult(cleanedData?.results.accessibility, 'accessibility')}
			{/if}

			{#if cleanedData?.results.code}
				{@render renderResult(cleanedData?.results.code, 'code')}
			{/if}

			{#if cleanedData?.results.compliance}
				{@render renderResult(cleanedData?.results.compliance, 'compliance')}
			{/if}

			{#if cleanedData?.results.design}
				{@render renderResult(cleanedData?.results.design, 'design')}
			{/if}

			{#if cleanedData?.results.infrastructure}
				{@render renderResult(cleanedData?.results.infrastructure, 'infrastructure')}
			{/if}

			{#if cleanedData?.results.performance}
				{@render renderResult(cleanedData?.results.performance, 'performance')}
			{/if}

			{#if cleanedData?.results.seo}
				{@render renderResult(cleanedData?.results.seo, 'seo')}
			{/if}

			{#if cleanedData?.results.ux}
				{@render renderResult(cleanedData?.results.ux, 'ux')}
			{/if}
		</div>
	{:else}
		<p class="text-center text-gray-500">Loading project data or project not found...</p>
	{/if}
</main>

{#snippet renderResult(result: AResult, name: string)}
	<div
		class="mx-auto mb-6 h-fit w-full flex-1 break-inside-avoid rounded-2xl border border-gray-100 bg-white p-6 shadow-lg transition hover:shadow-xl md:mb-8"
	>
		<div class="mb-4 flex items-center gap-3">
			<span
				class="inline-flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 text-2xl text-blue-600"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-6 w-6"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M12 4v16m8-8H4"
					/>
				</svg>
			</span>
			<h2 class="text-xl font-semibold uppercase text-gray-800">{name}</h2>
		</div>
		<p class="mb-2 text-3xl font-bold text-blue-600">
			Score:
			{#if Number(result.overall_score) === 0}
				--
			{:else if Number(result.overall_score) < 1}
				{(Number(result.overall_score) * 100).toFixed(2)}
			{:else}
				{Number(result.overall_score).toFixed(2)}
			{/if}
			/ 100
		</p>
		<!-- Metrics summary -->
		<div class="mb-4 grid grid-cols-2 gap-2 text-sm">
			{#each result.metrics?.names ?? [] as name}
				<div>
					<span class="font-semibold capitalize">{name.replace(/_/g, ' ')}:</span>
					{#if Number(result.metrics?.scores?.[(result.metrics?.names ?? []).indexOf(name)] ?? 0) === 0}
						FAIL
					{:else if Number(result.metrics?.scores?.[(result.metrics?.names ?? []).indexOf(name)] ?? 0) === 1}
						PASS
					{:else}
						{Number(result.metrics?.scores?.[(result.metrics?.names ?? []).indexOf(name)] ?? 0)}
					{/if}
				</div>
			{/each}
		</div>
		<!-- Top Issues -->
		{#if result.issues?.length}
			<p class="mb-1 text-sm font-semibold text-gray-500">
				{#if result.issues?.length > 5}
					Top
				{/if}
				Issues:
			</p>
			<ol class="mb-2 list-decimal pl-5 text-sm text-red-700">
				{#if result.showMoreIssues}
					{#each result.issues as issue, i}
						<li class=" line-clamp-3 text-ellipsis">
							{typeof issue === 'string' ? issue : JSON.stringify(issue)}
						</li>
					{/each}
				{:else}
					{#each result.issues.slice(0, 5) as issue, i}
						<li class=" line-clamp-3 text-ellipsis">
							{typeof issue === 'string' ? issue : JSON.stringify(issue)}
						</li>
					{/each}
				{/if}
				{#if result.issues.length > 5}
					<button
						onclick={() => {
							if (cleanedData !== null) result.showMoreIssues = !result.showMoreIssues;
						}}
						class="text-sm text-blue-500 hover:underline"
					>
						{result.showMoreIssues ? 'Show less' : 'Show more'}
					</button>
				{/if}
			</ol>
		{/if}
		<!-- Recommendations -->
		{#if result.recommendations.length}
			<p class="mb-1 text-sm font-semibold text-gray-500">
				{#if result.issues?.length > 5}
					Top
				{/if}
				Recommendations:
			</p>
			<ol class="mb-2 list-decimal pl-5 text-sm text-green-700">
				{#if result.showMoreRecommendations}
					{#each result.recommendations as issue, i}
						<li>{typeof issue === 'string' ? issue : JSON.stringify(issue)}</li>
					{/each}
				{:else}
					{#each result.recommendations.slice(0, 5) as issue, i}
						<li>{typeof issue === 'string' ? issue : JSON.stringify(issue)}</li>
					{/each}
				{/if}
				{#if result.recommendations.length > 5}
					<button
						onclick={() => {
							if (cleanedData !== null)
								result.showMoreRecommendations = !result.showMoreRecommendations;
						}}
						class="text-sm text-blue-500 hover:underline"
					>
						{result.showMoreRecommendations ? 'Show less' : 'Show more'}
					</button>
				{/if}
			</ol>
		{/if}
	</div>
{/snippet}
