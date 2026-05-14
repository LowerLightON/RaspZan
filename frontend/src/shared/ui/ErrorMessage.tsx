import { isApiError } from "../api/errors";

type ErrorMessageProps = {
  error: unknown;
};

export function ErrorMessage({ error }: ErrorMessageProps) {
  if (isApiError(error)) {
    return (
      <section className="notice error" aria-live="polite">
        <strong>Request failed ({error.status})</strong>
        {error.envelope ? (
          <>
            <span>Code: {error.envelope.error.code}</span>
            <span>{error.envelope.error.message}</span>
          </>
        ) : (
          <span>{error.message}</span>
        )}
      </section>
    );
  }

  return (
    <section className="notice error" aria-live="polite">
      <strong>Could not load schedule</strong>
      <span>{error instanceof Error ? error.message : "Network error"}</span>
    </section>
  );
}
