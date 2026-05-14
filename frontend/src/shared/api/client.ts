import { ApiError, isApiErrorEnvelope } from "./errors";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

type ApiRequestOptions = RequestInit & {
  query?: Record<string, string | number | boolean | null | undefined>;
};

function buildUrl(path: string, query?: ApiRequestOptions["query"]) {
  const url = new URL(path, apiBaseUrl);

  Object.entries(query ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      url.searchParams.set(key, String(value));
    }
  });

  return url.toString();
}

async function parseJson(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    return null;
  }

  return response.json();
}

export async function apiRequest<T>(
  path: string,
  { query, headers, ...init }: ApiRequestOptions = {},
): Promise<T> {
  let response: Response;

  try {
    response = await fetch(buildUrl(path, query), {
      ...init,
      headers: {
        Accept: "application/json",
        ...headers,
      },
    });
  } catch (error) {
    throw new Error(
      error instanceof Error ? error.message : "Network request failed",
    );
  }

  const body = await parseJson(response);

  if (!response.ok) {
    if (isApiErrorEnvelope(body)) {
      throw new ApiError(response.status, body.error.message, body);
    }

    throw new ApiError(response.status, response.statusText || "API error");
  }

  return body as T;
}
