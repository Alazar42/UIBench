<script>
	import { goto } from '$app/navigation';
	import { userContext } from '$lib/context/user';
	import { slide } from 'svelte/transition';

	let { isActive = $bindable(), ...props } = $props();

	let logoutCardOpen = $state(false);

	function logout() {
		localStorage.removeItem('accessToken');
		goto('/');
	}
</script>

<header
	class="fixed left-0 top-0 z-30 flex w-screen items-center justify-between bg-white px-6 py-3 font-sans shadow-sm"
>
	<div class="flex w-20 items-center md:w-44">
		<span class="text-xl font-black tracking-wider text-blue-950">UIB</span>
	</div>
	<div class="flex flex-1 items-center justify-center text-lg font-medium">All projects</div>
	<div class="flex items-center gap-4">
		<!-- New Project Button (Desktop) -->
		<button
			onclick={() => (isActive = true)}
			class="hidden rounded-md bg-gray-800 px-4 py-2 text-base text-white transition-colors hover:bg-gray-950 md:block"
		>
			New project
		</button>

		<!-- New Project Button (Mobile) -->
		<button
			onclick={() => (isActive = true)}
			class="flex h-10 w-10 items-center justify-center rounded-md bg-gray-800 px-4 py-2 text-2xl text-white transition-colors hover:bg-gray-950 md:hidden"
		>
			+
		</button>

		<!-- User Initial -->
		<button
			onclick={() => (logoutCardOpen = !logoutCardOpen)}
			class="flex h-9 w-9 select-none items-center justify-center rounded-full bg-gray-200 text-base font-bold uppercase text-gray-700"
		>
			{$userContext.email[0]}
		</button>

		{#if logoutCardOpen}
			<div
				onclick={() => (logoutCardOpen = !logoutCardOpen)}
				onkeydown={(e) => {
					if (e.key === 'Enter' || e.key === ' ') {
						logoutCardOpen = !logoutCardOpen;
					}
				}}
				tabindex="0"
				role="button"
				aria-label="Close logout card"
				class="fixed left-0 top-0 z-40 flex flex h-screen w-screen cursor-default items-start justify-end bg-black/0 pr-6 pt-[4.25rem]"
			>
				<button
					onclick={logout}
					transition:slide={{ axis: 'y' }}
					class="z-40 flex items-center justify-center gap-1 rounded-md bg-pink-50 px-5 py-2 text-pink-800 shadow hover:bg-pink-100"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						height="16px"
						class="fill-pink-800"
						viewBox="0 -960 960 960"
						width="16px"
						fill="currentColor"
						><path
							d="M200-120q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h280v80H200v560h280v80H200Zm440-160-55-58 102-102H360v-80h327L585-622l55-58 200 200-200 200Z"
						/></svg
					>
					Logout
				</button>
			</div>
		{/if}
	</div>
</header>
