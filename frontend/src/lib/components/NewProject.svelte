<!-- @migration-task Error while migrating Svelte code: Cannot use `export let` in runes mode — use `$props()` instead
https://svelte.dev/e/legacy_export_invalid -->
<script lang="ts">
	import { goto, invalidateAll } from '$app/navigation';
	import { createProject } from '$lib/api/server';
	import { userContext } from '$lib/context/user';
	import type { Project } from '$lib/types';
	import { blur, crossfade, draw, fade, scale, slide } from 'svelte/transition';

	let isLoading = $state(false);

	let { isActive = $bindable(), ...props } = $props();

	let project: Project = $state({
		id: '',
		name: '',
		url: '',
		creation_date: '',
		last_updated: '',
		description: '',
		is_public: false,
		tags: [],
		status: 'pending'
	});

	let newTag = $state('');
	const statuses = ['pending', 'active', 'completed'];

	function addTag() {
		if (newTag && !project.tags.includes(newTag)) {
			project.tags = [...project.tags, newTag];
			newTag = '';
		}
	}

	function removeTag(tag: string) {
		project.tags = project.tags.filter((t) => t !== tag);
	}

	async function handleSubmit(e: Event) {
		e.preventDefault();
		project.creation_date = Date.now().toString();
		project.last_updated = Date.now().toString();
		try {
			isLoading = true;
			await createProject(project, $userContext.bearer);
			// invalidateAll();
		} catch (error: any) {
			alert(`Error during createProject: ${error.message}`);
			isLoading = false;
			isActive = false;
			return;
		}
		isActive = false;
	}
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<!-- svelte-ignore a11y_click_events_have_key_events -->
<div
	transition:blur
	onclick={() => {
		isActive = false;
	}}
	class="fixed left-0 top-0 z-50 h-screen w-screen bg-gray-800/15 md:p-6"
>
	<div
		onclick={(ev) => {
			ev.stopPropagation();
		}}
		class="z-20 mx-auto h-full w-full max-w-2xl bg-white p-8 shadow-xl md:h-fit md:w-fit md:rounded-3xl"
	>
		<h1 class="mb-6 text-xl font-bold text-gray-800 md:text-3xl">Create New Project</h1>

		<form class="flex h-full flex-col md:h-fit" onsubmit={handleSubmit}>
			<div class="mb-6">
				<label for="project-url" class="mb-1 block font-medium text-gray-700">URL</label>
				<input
					id="project-url"
					type="url"
					bind:value={project.url}
					class="w-full rounded-lg border-2 px-4 py-4 focus:outline-none focus:ring-2 focus:ring-blue-400"
					required
				/>
			</div>

			<div class="mb-2">
				<label for="project-name" class="mb-1 block font-medium text-gray-700">Name</label>
				<input
					id="project-name"
					type="text"
					bind:value={project.name}
					class="w-full rounded-lg border px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
					required
				/>
			</div>

			<div class="mb-6">
				<label for="project-description" class="mb-1 block font-medium text-gray-700"
					>Description (optional)</label
				>
				<textarea
					id="project-description"
					bind:value={project.description}
					rows="3"
					class="w-full rounded-lg border px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
				></textarea>
			</div>

			<!-- <div class="mb-6">
				<div class="w-fit">
					<label for="project-tags" class="mb-1 block font-medium text-gray-700"
						>Tags (optional)</label
					>
					<div id="project-tags" class="flex items-center space-x-2">
						<input
							type="text"
							bind:value={newTag}
							class="w-1/2 flex-1 rounded-lg border px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
							placeholder="Add tag"
						/>
						<button
							type="button"
							onclick={addTag}
							class="w-1/3 rounded-lg bg-blue-500 px-4 py-2 text-white hover:bg-blue-600"
							>Add</button
						>
					</div>
				</div>
				<div class="mt-2 flex flex-wrap items-center gap-2">
					{#each project.tags as tag}
						<span
							class="flex items-center space-x-1 rounded-full bg-gray-200 px-3 py-1 text-sm text-gray-700"
						>
							<span>{tag}</span>
							<button
								type="button"
								onclick={() => removeTag(tag)}
								class="text-gray-500 hover:text-red-500">&times;</button
							>
						</span>
					{/each}
				</div>
			</div> -->

			<div class="mb-6 grow md:grow-0">
				<label for="make-public" class="flex items-center space-x-2">
					<input
						id="make-public"
						type="checkbox"
						bind:checked={project.is_public}
						class="accent-blue-500"
					/>
					<span class="text-gray-700">Make this project public</span>
				</label>
			</div>

			<div class="mb-12 flex w-full gap-2 md:mb-0">
				<button
					onclick={() => {
						isActive = false;
					}}
					type="button"
					class="w-full rounded-lg bg-gray-300 py-3 text-lg font-semibold text-gray-700 transition-colors hover:bg-gray-200"
				>
					Cancel
				</button>
				<button
					type="submit"
					class="w-full rounded-lg bg-blue-600 py-3 text-lg font-semibold text-white transition-colors hover:bg-blue-700"
				>
					{#if isLoading}
						<svg
							transition:slide
							width="36"
							height="20"
							class="mx-auto fill-blue-100"
							viewBox="0 0 24 24"
							xmlns="http://www.w3.org/2000/svg"
							><style>
								.spinner_S1WN {
									animation: spinner_MGfb 0.8s linear infinite;
									animation-delay: -0.8s;
								}
								.spinner_Km9P {
									animation-delay: -0.65s;
								}
								.spinner_JApP {
									animation-delay: -0.5s;
								}
								@keyframes spinner_MGfb {
									93.75%,
									100% {
										opacity: 0.2;
									}
								}
							</style><circle class="spinner_S1WN" cx="6" cy="12" r="4" /><circle
								class="spinner_S1WN spinner_Km9P"
								cx="18"
								cy="12"
								r="4"
							/><circle class="spinner_S1WN spinner_JApP" cx="30" cy="12" r="4" /></svg
						>
					{:else}
						Create
					{/if}
				</button>
			</div>
		</form>
	</div>
</div>
