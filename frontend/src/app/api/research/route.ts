import { ApiError, askResearch } from "@/lib/api";
import type { ResearchAsk } from "@/lib/types";

/**
 * Server-side proxy for the regulatory research endpoint. The client chat posts
 * here so the Argus bearer token stays on the server and is never exposed to
 * the browser. This is a request/response proxy — the backend returns a
 * complete answer; there is no token streaming.
 */
export async function POST(request: Request): Promise<Response> {
  let payload: ResearchAsk;
  try {
    const body = (await request.json()) as Partial<ResearchAsk>;
    if (!body.question || typeof body.question !== "string") {
      return Response.json(
        { error: "A 'question' string is required." },
        { status: 400 },
      );
    }
    payload = {
      question: body.question,
      jurisdiction: body.jurisdiction ?? null,
    };
  } catch {
    return Response.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  try {
    const answer = await askResearch(payload);
    return Response.json(answer);
  } catch (err) {
    const status = err instanceof ApiError && err.status ? err.status : 502;
    return Response.json(
      { error: "The research service is unavailable." },
      { status: status === 401 ? 502 : status },
    );
  }
}
