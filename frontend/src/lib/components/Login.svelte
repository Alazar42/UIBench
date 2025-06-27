<script lang="ts">
	import { slide } from 'svelte/transition';
	import { userContext } from '$lib/context/user';
	import { getUserDetails, loginUser, registerUser } from '$lib/api/server';

	import { passwordStrength } from 'check-password-strength';
	import { goto } from '$app/navigation';

	let isLoading = $state(false);

	let isNewUser = $state(false);
	let agreedToTerms = $state(false);

	let errorInEmail = $state(false);
	let emailInput = $state('');

	let mismatchPassword = $state(false);
	let weakPassword = $state(false);
	let passwordInput = $state('');
	let confirmPasswordInput = $state('');

	let onSubmit = async () => {
		/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailInput) ? (errorInEmail = false) : (errorInEmail = true);

		let userResponse;
		if (isNewUser) {
			userResponse = await onSignup();
		} else userResponse = await onLogin();

		const userDetails = await getUserDetails(userResponse.access_token);

		userContext.set({
			user_id: userDetails.user_id,
			name: userDetails.name,
			email: userDetails.email,
			bearer: userResponse.access_token,
			role: userDetails.role,
			projects: userDetails.projects
		});

		localStorage.setItem('accessToken', userResponse.access_token);

		if (userDetails.user_id !== '') {
			goto('/home');
		}

		isLoading = false;
	};

	let onLogin = async () => {
		passwordInput === '' ? (weakPassword = true) : (weakPassword = false);
		if (!errorInEmail && !weakPassword) {
			// hash.update(passwordInput);
			try {
				isLoading = true;
				return await loginUser({
					email: emailInput,
					password: passwordInput
				});

				// write the updated users to the file
				// alert('Signup successful');
			} catch (error: any) {
				alert(`Error during signup: ${error.message}`);
				isLoading = false;
				return;
			}
		}
	};

	let onSignup = async () => {
		if (!agreedToTerms) {
			alert('You must agree to the terms and conditions');
			return;
		}
		passwordStrength(passwordInput).value === 'Too weak'
			? (weakPassword = true)
			: (weakPassword = false);
		passwordInput !== confirmPasswordInput ? (mismatchPassword = true) : (mismatchPassword = false);

		if (!errorInEmail && !weakPassword && !mismatchPassword) {
			try {
				isLoading = true;

				await registerUser({
					name: '',
					email: emailInput,
					password: passwordInput,
					role: 'user'
				});

				return await loginUser({
					email: emailInput,
					password: passwordInput
				});
			} catch (error: any) {
				alert(`Error during signup: ${error.message}`);
				isLoading = false;
				return;
			}
		}
	};
</script>

<div class="flex w-80 flex-col items-center justify-center xl:scale-125 xl:pr-8">
	<ul id="login or signup tabs" class="mb-6 flex text-center text-sm font-medium text-gray-500">
		<li class=" me-2">
			<button
				onclick={() => {
					isNewUser = false;
				}}
				aria-current="page"
				class={isNewUser
					? 'inline-block p-4 pb-2 text-gray-500 transition-all'
					: 'active inline-block border-b-2 border-gray-500 p-4 pb-2 text-gray-900 transition-all'}
				>Log in</button
			>
		</li>
		<li class="me-2">
			<button
				onclick={() => {
					isNewUser = true;
				}}
				class={isNewUser
					? 'active inline-block border-b-2 border-gray-500 p-4 pb-2 text-gray-900 transition-all'
					: 'inline-block p-4 pb-2 text-gray-500 transition-all'}>Signup</button
			>
		</li>
	</ul>
	<form action="" class="flex w-full flex-col items-center">
		<div class="mb-4 w-full">
			<input
				bind:value={emailInput}
				type="email"
				id="email"
				class={errorInEmail
					? 'block w-full rounded-lg border border-red-500 bg-red-50 p-2.5 text-sm text-red-900 placeholder-red-700 shadow-inner focus:border-red-500 focus:ring-red-500'
					: 'block w-full rounded-lg border border-gray-300 bg-gray-50 p-2.5 text-sm text-gray-900 shadow-inner focus:border-blue-500 focus:ring-blue-500'}
				placeholder={errorInEmail ? 'Invalid email' : 'john.doe@company.com'}
				required
			/>
			{#if errorInEmail}
				<p class="mt-1 text-sm text-red-600">
					Fix your <span class="font-medium">email </span> and we shall continue
				</p>
			{/if}
		</div>

		<div class="mb-4 w-full">
			<input
				bind:value={passwordInput}
				type="password"
				id="password"
				class={weakPassword
					? 'block w-full rounded-lg border border-red-500 bg-red-50 p-2.5 text-sm text-red-900 placeholder-red-700 shadow-inner focus:border-red-500 focus:ring-red-500'
					: 'block w-full rounded-lg border border-gray-300 bg-gray-50 p-2.5 text-sm text-gray-900 shadow-inner focus:border-blue-500 focus:ring-blue-500'}
				placeholder="Password"
				required
			/>
			{#if passwordInput !== '' && isNewUser && !weakPassword}
				<p class="mt-1 text-end text-sm text-gray-500">
					{passwordStrength(passwordInput).value}
				</p>
			{/if}
			{#if weakPassword && isNewUser}
				<p class="mt-1 w-fit text-sm text-red-500">A-Z, a-z, 0-9 and "!-@$ required</p>
			{/if}
		</div>

		{#if isNewUser}
			<div class="mb-4 w-full">
				<input
					bind:value={confirmPasswordInput}
					type="password"
					id="confirm_password"
					transition:slide
					class={errorInEmail
						? 'block w-full rounded-lg border border-red-500 bg-red-50 p-2.5 text-sm text-red-900 placeholder-red-700 shadow-inner focus:border-red-500 focus:ring-red-500'
						: 'block w-full rounded-lg border border-gray-300 bg-gray-50 p-2.5 text-sm text-gray-900 shadow-inner focus:border-blue-500 focus:ring-blue-500'}
					placeholder="Confirm Password"
					required
				/>

				{#if mismatchPassword}
					<p class="mt-1 text-sm text-red-600">Your passwords do not match</p>
				{/if}
			</div>
		{/if}
		{#if isNewUser}
			<div class="mb-4 flex items-start">
				<div class="flex h-5 items-center">
					<input
						id="remember"
						type="checkbox"
						value=""
						bind:checked={agreedToTerms}
						class="focus:ring-3 -800 -600 h-4 w-4 rounded border border-gray-300 bg-gray-50 focus:ring-blue-300"
						required
					/>
				</div>
				<label for="remember" class="ms-2 text-sm font-medium text-gray-900"
					>I agree with the <a href="/" class="text-blue-600 hover:underline"
						>terms and conditions</a
					>.</label
				>
			</div>
		{/if}
		<button
			type="submit"
			onclick={onSubmit}
			class="w-full rounded-lg bg-blue-700 px-5 py-2.5 text-center text-sm font-medium text-white hover:bg-blue-800 focus:outline-none focus:ring-4 focus:ring-blue-300"
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
				<p transition:slide>{isNewUser ? 'Signup' : 'Log in'}</p>
			{/if}
		</button>
	</form>
</div>
