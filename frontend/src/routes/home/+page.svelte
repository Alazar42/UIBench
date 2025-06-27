<script lang="ts">
	import { goto } from '$app/navigation';
	import { getUserProjects } from '$lib/api/server';
	import { userContext } from '$lib/context/user';
	import Header from '$lib/components/Header.svelte';
	import NewProject from '$lib/components/NewProject.svelte';
	import { onMount } from 'svelte';

	let newProjectModal = $state(false);

	let formatDate = $state((iso: string) => {});
	onMount(() => {
		formatDate = (iso: string) => new Date(iso).toLocaleString();
	});
</script>

<main
	class="flex h-screen w-screen flex-col items-center gap-6 px-12 py-16 xl:flex-row xl:justify-between"
>
	{#if newProjectModal}
		<NewProject bind:isActive={newProjectModal} />
	{/if}
	<Header bind:isActive={newProjectModal} />
	<div class="flex flex-col items-center justify-center text-center xl:items-start xl:text-start">
		{#await getUserProjects($userContext.bearer) then allProjects}
			<div class="grid gap-8 p-4 pt-8 md:grid-cols-2 xl:grid-cols-3">
				{#each allProjects as project}
					<a
						href="/projects/{project.project_id}"
						id={project.project_id}
						class="min-w-80 rounded-3xl bg-white p-6 shadow-xl transition duration-300 hover:shadow-2xl"
					>
						<header class="mb-4 flex items-center border-b pb-3">
							<div
								class="mr-2 w-fit rounded-full px-2 py-2 {project.is_public
									? 'bg-green-100 fill-green-700'
									: 'bg-yellow-100 fill-yellow-700'}"
							>
								{#if project.is_public}
									<svg
										xmlns="http://www.w3.org/2000/svg"
										height="16px"
										viewBox="0 -960 960 960"
										width="16px"
										fill="#currentColor"
										><path
											d="M480-80q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Zm-40-82v-78q-33 0-56.5-23.5T360-320v-40L168-552q-3 18-5.5 36t-2.5 36q0 121 79.5 212T440-162Zm276-102q41-45 62.5-100.5T800-480q0-98-54.5-179T600-776v16q0 33-23.5 56.5T520-680h-80v80q0 17-11.5 28.5T400-560h-80v80h240q17 0 28.5 11.5T600-440v120h40q26 0 47 15.5t29 40.5Z"
										/></svg
									>
								{:else}
									<svg
										xmlns="http://www.w3.org/2000/svg"
										height="16px"
										viewBox="0 -960 960 960"
										width="16px"
										fill="#currentColor"
										><path
											d="M819-28 701-146q-48 32-103.5 49T480-80q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-62 17-117.5T146-701L27-820l57-57L876-85l-57 57ZM440-162v-78q-33 0-56.5-23.5T360-320v-40L168-552q-3 18-5.5 36t-2.5 36q0 121 79.5 212T440-162Zm374-99-58-58q21-37 32.5-77.5T800-480q0-98-54.5-179T600-776v16q0 33-23.5 56.5T520-680h-80v45L261-814q48-31 103-48.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 61-17.5 116T814-261Z"
										/></svg
									>
								{/if}
							</div>
							<h2 class="max-w-full truncate text-2xl font-bold text-gray-800">{project.name}</h2>
							<span
								class="ml-auto rounded-full bg-purple-100 px-3 py-1 text-xs font-medium text-purple-700"
							>
								{project.status}
							</span>
						</header>

						<div class="space-y-3">
							<div class="-mb-4 flex w-3/4 truncate text-sm text-blue-600 hover:underline">
								{project.url}
							</div>

							<div class="ml-auto flex flex-col items-end text-sm">
								<p class="text-gray-500">Updated</p>
								<p class="text-gray-700">{formatDate(project.last_updated)}</p>
							</div>

							<div class="grid grid-cols-2 gap-4 text-sm">
								<div>
									<p class="text-gray-600">Results</p>
									<p class="text-gray-800">{project.analysis_result_ids.length}</p>
								</div>
								<div>
									<p class="text-gray-600">Feedback</p>
									<p class="text-gray-800">{project.feedback_ids.length}</p>
								</div>
							</div>

							<!-- {#if project.tags.length}
								<div class="pt-2">
									<p class="mb-1 text-sm text-gray-600">Tags</p>
									<div class="flex flex-wrap gap-2">
										{#each project.tags as tag}
											<span class="rounded bg-gray-200 px-2 py-1 text-xs text-gray-700">{tag}</span>
										{/each}
									</div>
								</div>
							{/if} -->
						</div>
					</a>
				{/each}
			</div>
		{:catch error}
			{console.log('Projects failed to load: ', error)}
		{/await}
	</div>
</main>
