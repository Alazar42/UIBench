<script>
	import { goto } from '$app/navigation';
	import { userContext } from '$lib/context/user';

	let { isActive = $bindable(), ...props } = $props();

	function logout() {
		localStorage.removeItem("accessToken");
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
		<div
			class="flex h-9 w-9 select-none items-center justify-center rounded-full bg-gray-200 text-base font-bold uppercase text-gray-700"
		>
			{$userContext.email[0]}
		</div>

		<!-- Logout Button with SVG Icon -->
		<button
			onclick={logout}
			class="flex h-9 w-9 items-center justify-center rounded-full bg-red-100 text-red-600 hover:bg-red-200"
			title="Logout"
			aria-label="Logout"
		>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
				stroke-width="2"
				class="h-5 w-5"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a2 2 0 002 2h3a2 2 0 002-2V7a2 2 0 00-2-2h-3a2 2 0 00-2 2v1"
				/>
			</svg>
		</button>
	</div>
</header>
