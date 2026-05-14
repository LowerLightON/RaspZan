import type { ApiErrorEnvelope } from "../types/api";

export class ApiError extends Error {
  readonly status: number;
  readonly envelope?: ApiErrorEnvelope;

  constructor(status: number, message: string, envelope?: ApiErrorEnvelope) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.envelope = envelope;
  }
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}

export function isApiErrorEnvelope(value: unknown): value is ApiErrorEnvelope {
  if (!value || typeof value !== "object") {
    return false;
  }

  const maybeEnvelope = value as { error?: unknown };
  if (!maybeEnvelope.error || typeof maybeEnvelope.error !== "object") {
    return false;
  }

  const maybeError = maybeEnvelope.error as {
    code?: unknown;
    message?: unknown;
  };

  return (
    typeof maybeError.code === "string" &&
    typeof maybeError.message === "string"
  );
}
