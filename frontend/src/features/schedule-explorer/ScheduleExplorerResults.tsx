import type {
  GroupLookupItem,
  PaginatedResponse,
  RoomLookupItem,
  ScheduleEntry,
  SubjectLookupItem,
  TeacherLookupItem,
} from "../../shared/types/api";
import { Button } from "../../shared/ui/Button";
import { ErrorMessage } from "../../shared/ui/ErrorMessage";
import { WeeklyScheduleGridView } from "./WeeklyScheduleGridView";
import type { ScheduleExplorerView } from "./scheduleExplorerTypes";

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
  view: ScheduleExplorerView;
  onViewChange: (view: ScheduleExplorerView) => void;
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

type LookupProps = {
  groups: GroupLookupItem[];
  rooms: RoomLookupItem[];
  subjects: SubjectLookupItem[];
  teachers: TeacherLookupItem[];
};

function ScheduleResultsToolbar({
  data,
  onViewChange,
  view,
}: {
  data: PaginatedResponse<ScheduleEntry>;
  onViewChange: (view: ScheduleExplorerView) => void;
  view: ScheduleExplorerView;
}) {
  return (
    <div className="results-toolbar">
      <div className="summary">
        <span>Total: {data.total}</span>
        <span>Limit: {data.limit}</span>
        <span>Offset: {data.offset}</span>
        {view === "grid" ? <span>Grid range: first 100 from offset 0</span> : null}
      </div>
      <div className="view-toggle" aria-label="Results view">
        <Button
          aria-pressed={view === "table"}
          className="view-toggle-button"
          type="button"
          onClick={() => onViewChange("table")}
        >
          Table View
        </Button>
        <Button
          aria-pressed={view === "grid"}
          className="view-toggle-button"
          type="button"
          onClick={() => onViewChange("grid")}
        >
          Grid View
        </Button>
      </div>
    </div>
  );
}

function ScheduleTableView({
  data,
  groups,
  rooms,
  subjects,
  teachers,
}: {
  data: PaginatedResponse<ScheduleEntry>;
} & LookupProps) {
  return (
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
  );
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
  view,
  onViewChange,
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
      <ScheduleResultsToolbar
        data={data}
        view={view}
        onViewChange={onViewChange}
      />

      {view === "grid" ? (
        <WeeklyScheduleGridView
          entries={data.items}
          groups={groups}
          rooms={rooms}
          subjects={subjects}
          teachers={teachers}
        />
      ) : data.items.length === 0 ? (
        <div className="notice">No schedule entries found.</div>
      ) : (
        <ScheduleTableView
          data={data}
          groups={groups}
          rooms={rooms}
          subjects={subjects}
          teachers={teachers}
        />
      )}
    </section>
  );
}
