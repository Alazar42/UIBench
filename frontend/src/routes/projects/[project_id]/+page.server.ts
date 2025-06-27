import { error } from '@sveltejs/kit';
import dummyData from '../../../../src/data/dummy.json';

export async function load({ params }) {
	const { project_id } = params;

	if (dummyData.project_id === project_id) {
		return {
			project: dummyData
		};
	}

	throw error(404, 'Project not found');
}
