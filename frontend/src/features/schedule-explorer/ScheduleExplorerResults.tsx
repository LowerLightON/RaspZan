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
import { formatScheduleEntryType } from "./formatScheduleEntryType";
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
        <span>Всего: {data.total}</span>
        <span>Лимит: {data.limit}</span>
        <span>Смещение: {data.offset}</span>
        {view === "grid" ? <span>Диапазон сетки: первые 100 со смещения 0</span> : null}
      </div>
      <div className="view-toggle" aria-label="Вид результатов">
        <Button
          aria-pressed={view === "table"}
          className="view-toggle-button"
          type="button"
          onClick={() => onViewChange("table")}
        >
          Таблица
        </Button>
        <Button
          aria-pressed={view === "grid"}
          className="view-toggle-button"
          type="button"
          onClick={() => onViewChange("grid")}
        >
          Сетка
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
            <th>Дата</th>
            <th>Пара</th>
            <th>Предмет</th>
            <th>Преподаватель</th>
            <th>Аудитория</th>
            <th>Группы</th>
            <th>Тип занятия</th>
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
              <td>{formatScheduleEntryType(entry.entry_type)}</td>
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
        Выберите параметры расписания и загрузите первую страницу.
      </section>
    );
  }

  if (isFetching) {
    return (
      <section className="notice" aria-live="polite">
        Загрузка расписания...
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
        <div className="notice">Занятия не найдены.</div>
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
