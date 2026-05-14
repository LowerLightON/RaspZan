import type {
  GroupLookupItem,
  PaginatedResponse,
  RoomLookupItem,
  ScheduleEntry,
  SubjectLookupItem,
  TeacherLookupItem,
} from "../../shared/types/api";
import { ErrorMessage } from "../../shared/ui/ErrorMessage";

type ScheduleExplorerResultsProps = {
  data?: PaginatedResponse<ScheduleEntry>;
  error: unknown;
  groups: GroupLookupItem[];
  isError: boolean;
  isFetching: boolean;
  hasSubmitted: boolean;
  rooms: RoomLookupItem[];
  subjects: SubjectLookupItem[];
  teachers: TeacherLookupItem[];
};

function labelForId(
  items: Array<{ id: number; label: string }>,
  id: number | null,
) {
  if (id === null) {
    return "-";
  }

  return items.find((item) => item.id === id)?.label ?? String(id);
}

function labelsForIds(items: Array<{ id: number; label: string }>, ids: number[]) {
  if (ids.length === 0) {
    return "-";
  }

  return ids
    .map((id) => items.find((item) => item.id === id)?.label ?? String(id))
    .join(", ");
}

export function ScheduleExplorerResults({
  data,
  error,
  groups,
  isError,
  isFetching,
  hasSubmitted,
  rooms,
  subjects,
  teachers,
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
                <th>Date</th>
                <th>Period</th>
                <th>Subject</th>
                <th>Teacher</th>
                <th>Room</th>
                <th>Groups</th>
                <th>Entry type</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((entry) => (
                <tr key={entry.id}>
                  <td>{entry.lesson_date}</td>
                  <td>{entry.period_number}</td>
                  <td>{labelForId(subjects, entry.subject_id)}</td>
                  <td>{labelForId(teachers, entry.teacher_id)}</td>
                  <td>{labelForId(rooms, entry.room_id)}</td>
                  <td>{labelsForIds(groups, entry.group_ids)}</td>
                  <td>{entry.entry_type}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
