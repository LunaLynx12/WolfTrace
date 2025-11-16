import type { RequestHandler } from './$types';

export const GET: RequestHandler = async () => {
	// Return empty 204 to avoid 404 logs for /favicon.png during development
	return new Response(null, {
		status: 204,
		headers: {
			'Cache-Control': 'public, max-age=86400'
		}
	});
};


