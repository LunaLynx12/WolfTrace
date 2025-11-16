import type { RequestHandler } from './$types';

export const GET: RequestHandler = async () => {
	// Return empty 204 to avoid dev server 404 noise for /favicon.ico
	return new Response(null, {
		status: 204,
		headers: {
			'Cache-Control': 'public, max-age=86400'
		}
	});
};


