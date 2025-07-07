interface User {
	name?: string;
	email: string;
	password: string;
	role?: string;
}

interface UserContext {
	user_id: string;
	name: string;
	email: string;
	bearer: string;
	role: string;
	projects: [];
}

interface Project {
	id: string;
	name: string;
	description: string;
	url: string;
	tags: string[];
	status: string;
	creation_date: string;
	last_updated: string;
	is_public: boolean;
}

export interface AnalysisResult {
	name: string;
	status: string;
	url: string;
	results: {
		accessibility?: AResult;
		code?: AResult;
		compliance?: AResult;
		design?: AResult;
		infrastructure?: AResult;
		performance?: AResult;
		seo?: AResult;
		ux?: AResult;
	};
}

export interface AResult {
	issues: string[];
	recommendations: string[];
	metrics?: {
		names: string[];
		scores: number[];
	};
	overall_score: number;
	showMoreIssues: boolean;
	showMoreRecommendations: boolean;
}

interface ProjectResult {
	_id: { $oid: string };
	result_id: string;
	project_id: string;
	user_id: string;
	url: string;
	status: string;
	score: number | null;
	details: any | null;
	analysis_date: { $date: { $numberLong: string } };
	result: AnalysisResult;
}

export type { User, UserContext, Project, ProjectResult };
