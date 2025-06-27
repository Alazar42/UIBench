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

interface AnalysisResult {
	status: string;
	results: {
		url: string;
		page_rating: number;
		page_class: string;
		results: {
			accessibility?: any; // Simplified for brevity, can be detailed if needed
			performance?: any;
			security?: any;
			seo?: any;
			ux?: any;
			code?: any;
			compliance?: any;
			design?: any;
			infrastructure?: any;
			nlp?: any;
			operational?: any;
			mutation?: any;
			contract?: any;
			fuzz?: any;
		};
		design_data?: any;
		performance_metrics?: any;
	};
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
