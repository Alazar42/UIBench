<script lang="ts">
	import '../app.css';
	import { goto } from '$app/navigation';
	import { getUserDetails } from '$lib/api/server';
	import { userContext } from '$lib/context/user';
	import { onMount } from 'svelte';
	import { fade, slide } from 'svelte/transition';
	// import Header from '$lib/components/Header.svelte';
	let { children } = $props();

	let isLoading = $state(false);

	onMount(async () => {
		isLoading = true;
		const savedToken = localStorage.getItem('accessToken');

		if (savedToken) {
			try {
				const userDetails = await getUserDetails(savedToken);
				if (userDetails) {
					userContext.set({
						user_id: userDetails.user_id,
						name: userDetails.name,
						email: userDetails.email,
						bearer: localStorage.getItem('accessToken') ?? '',
						role: userDetails.role,
						projects: userDetails.projects
					});

					goto('/home');
				}
			} catch (error) {
				console.error('Possible expired token, clearing');
				localStorage.removeItem('accessToken');
				goto('/');
			}
		}
		isLoading = false;
	});
</script>

{#if isLoading}
	<div transition:fade class="absolute left-0 top-0 z-30 h-screen w-screen bg-white/70 py-96">
		<svg
			transition:slide
			width="84"
			height="20"
			class="mx-auto scale-[2.5] fill-blue-200"
			viewBox="0 0 24 24"
			xmlns="http://www.w3.org/2000/svg"
			><style>
				.spinner_S1WN {
					animation: spinner_MGfb 1.5s linear infinite;
					animation-delay: -1.5s;
				}
				.spinner_Km9P {
					animation-delay: -1s;
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
			</style><circle class="spinner_S1WN" cx="6" cy="12" r="8" /><circle
				class="spinner_S1WN spinner_Km9P"
				cx="30"
				cy="12"
				r="8"
			/><circle class="spinner_S1WN spinner_JApP" cx="54" cy="12" r="8" /></svg
		>
	</div>
{/if}
{@render children()}
