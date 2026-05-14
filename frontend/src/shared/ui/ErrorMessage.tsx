import { isApiError } from "../api/errors";

type ErrorMessageProps = {
  error: unknown;
  title?: string;
};

export function ErrorMessage({
  error,
  title = "Не удалось загрузить расписание",
}: ErrorMessageProps) {
  if (isApiError(error)) {
    return (
      <section className="notice error" aria-live="polite">
        <strong>Ошибка запроса ({error.status})</strong>
        {error.envelope ? (
          <>
            <span>Код: {error.envelope.error.code}</span>
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
      <strong>{title}</strong>
      <span>{error instanceof Error ? error.message : "Ошибка сети"}</span>
    </section>
  );
}
