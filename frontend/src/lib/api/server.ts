import type { Project, User } from '$lib/types';
import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8000';

export async function registerUser(user: User) {
	try {
		const res = await axios.post(`${API_BASE}/users/register/`, user);
		console.log(res);
		return res.data;
	} catch (error) {
		console.error('Error occurred during register:', error);
		throw error;
	}
}

export async function loginUser(user: User) {
	try {
		const res = await axios.post(`${API_BASE}/users/login/`, user);
		console.log(res);
		return res.data;
	} catch (error) {
		console.error('Error occurred during login:', error);
		throw error;
	}
}

export async function getUserDetails(token: string) {
	try {
		// Headers.set('Authorization', `Bearer ${token}`);
		const res = await axios.get(`${API_BASE}/users/me/`, {
			headers: {
				Authorization: `Bearer ${token}`
			}
		});
		console.log(res);
		return res.data;
	} catch (error) {
		console.error('Error occurred during getUserDetails:', error);
		throw error;
	}
}

export async function getUserProjectById(token: string, projectId: string) {
	try {
		const res = await axios.get(`${API_BASE}/users/me/projects/${projectId}`, {
			headers: {
				Authorization: `Bearer ${token}`
			}
		});
		console.log('Project response:', res.data);
		return res.data;
	} catch (error) {
		console.error('Error fetching project:', error);
		throw error;
	}
}

export async function getUserProjectAnalysisById(token: string, projectId: string) {
	try {
		const res = await axios.get(`${API_BASE}/users/me/projects/${projectId}/analysis`, {
			headers: {
				Authorization: `Bearer ${token}`
			},
			method: 'GET'
		});
		console.log('Project response:', res.data);
		return res.data[0]; // Assuming the response is an array and we want the first item
	} catch (error) {
		console.error('Error fetching project:', error);
		throw error;
	}
}

export async function getUserProjects(token: string) {
	try {
		// Headers.set('Authorization', `Bearer ${token}`);
		const res = await axios.get(`${API_BASE}/users/me/projects/`, {
			headers: {
				Authorization: `Bearer ${token}`
			}
		});
		console.log(res);
		return res.data;
	} catch (error) {
		console.error('Error occurred during getUserProjects:', error);
		throw error;
	}
}

export async function createProject(project: Project, token: string) {
	try {
		// Headers.set('Authorization', `Bearer ${token}`);
		const res = await axios.post(`${API_BASE}/users/me/projects/`, project, {
			headers: {
				Authorization: `Bearer ${token}`
			}
		});
		console.log(res);
		const analysis = await startAnalysis(res.data.project_id, token);
		return res.data + analysis;
	} catch (error) {
		console.error('Error occurred during getUserProjects:', error);
		throw error;
	}
}

async function startAnalysis(id: string, token: string) {
	try {
		// Headers.set('Authorization', `Bearer ${token}`);
		const res = await axios.post(
			`${API_BASE}/users/me/projects/${id}/analysis/`,
			{},
			{
				headers: {
					Authorization: `Bearer ${token}`
				}
			}
		);
		console.log(res);
		return res.data;
	} catch (error) {
		console.error('Error occurred during startAnalysis:', error);
		throw error;
	}
}
