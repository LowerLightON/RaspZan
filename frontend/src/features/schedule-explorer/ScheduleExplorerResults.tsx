import type { PaginatedResponse, ScheduleEntry } from "../../shared/types/api";
import { ErrorMessage } from "../../shared/ui/ErrorMessage";

type ScheduleExplorerResultsProps = {
  data?: PaginatedResponse<ScheduleEntry>;
  error: unknown;
  isError: boolean;
  isFetching: boolean;
  hasSubmitted: boolean;
};

function formatNullable(value: string | number | null) {
  return value ?? "-";
}

export function ScheduleExplorerResults({
  data,
  error,
  isError,
  isFetching,
  hasSubmitted,
}: ScheduleExplorerResultsProps) {
  if (!hasSubmitted) {
    return (
      <section className="notice">
        Choose schedule parameters and load the first page.
      </section>
    );
  }

  if (isFetching) {
    return (
      <section className="notice" aria-live="polite">
        Loading schedule...
      </section>
    );
  }

  if (isError) {
    return <ErrorMessage error={error} />;
  }

  if (!data) {
    return null;
  }

  return (
    <section className="panel results">
      <div className="summary">
        <span>Total: {data.total}</span>
        <span>Limit: {data.limit}</span>
        <span>Offset: {data.offset}</span>
      </div>

      {data.items.length === 0 ? (
        <div className="notice">No schedule entries found.</div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Date</th>
                <th>Period</th>
                <th>Time</th>
                <th>Type</th>
                <th>Week</th>
                <th>Title</th>
                <th>Subject</th>
                <th>Teacher</th>
                <th>Room</th>
                <th>Groups</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((entry) => (
                <tr key={entry.id}>
                  <td>{entry.id}</td>
                  <td>{entry.lesson_date}</td>
                  <td>{entry.period_number}</td>
                  <td>
                    {formatNullable(entry.starts_at)} -{" "}
                    {formatNullable(entry.ends_at)}
                  </td>
                  <td>{entry.entry_type}</td>
                  <td>{entry.week_type}</td>
                  <td>{formatNullable(entry.title)}</td>
                  <td>{formatNullable(entry.subject_id)}</td>
                  <td>{formatNullable(entry.teacher_id)}</td>
                  <td>{formatNullable(entry.room_id)}</td>
                  <td>{entry.group_ids.join(", ") || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
