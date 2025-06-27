<script>
	import { userContext } from '$lib/context/user';
	let { isActive = $bindable(), ...props } = $props();
</script>

<header
	class="fixed left-0 top-0 z-30 flex w-screen items-center justify-between bg-white px-6 py-3 font-sans shadow-sm"
>
	<div class="flex w-20 items-center md:w-44">
		<span class="text-xl font-black tracking-wider text-blue-950">UIB</span>
	</div>
	<div class="flex flex-1 items-center justify-center text-lg font-medium">All projects</div>
	<div class="flex items-center gap-4">
		<button
			onclick={() => (isActive = true)}
			class="hidden rounded-md bg-gray-800 px-4 py-2 text-base text-white transition-colors hover:bg-gray-950 md:block"
		>
			New project
		</button>
		<button
			onclick={() => (isActive = true)}
			class="flex h-10 w-10 items-center justify-center rounded-md bg-gray-800 px-4 py-2 text-2xl text-white transition-colors hover:bg-gray-950 md:hidden"
		>
			+
		</button>
		<div
			class="flex h-9 w-9 select-none items-center justify-center rounded-full bg-gray-200 text-base font-bold uppercase text-gray-700"
		>
			{$userContext.email[0]}
		</div>
	</div>
</header>
