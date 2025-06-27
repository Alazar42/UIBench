import { writable, type Writable } from 'svelte/store';
import type { UserContext } from '$lib/types';

export const userContext: Writable<UserContext> = writable({
	user_id: '',
	name: '',
	email: '',
	bearer: '',
	role: '',
	projects: []
});

userContext.subscribe((userContext) => {
	console.log('User context: ', userContext);
});
