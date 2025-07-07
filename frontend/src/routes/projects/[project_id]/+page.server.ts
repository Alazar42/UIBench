import { error } from '@sveltejs/kit';
import { getUserProjectById, getUserProjectAnalysisById } from '$lib/api/server';

export async function load({ params, cookies }) {
	const { project_id } = params;

	const token = cookies.get('accessToken'); // ✅ this works server-side
	if (!token) {
		throw error(401, 'Unauthorized');
	}

	try {
		const [project, analysis] = await Promise.all([
			getUserProjectById(token, project_id),
			getUserProjectAnalysisById(token, project_id)
		]);

		return { project, analysis };
	} catch (err) {
		console.error('Error loading project or analysis:', err);
		throw error(404, 'Project or analysis not found');
	}
}
