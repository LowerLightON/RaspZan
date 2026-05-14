import { useMemo, type CSSProperties } from "react";
import type {
  GroupLookupItem,
  RoomLookupItem,
  ScheduleEntry,
  SubjectLookupItem,
  TeacherLookupItem,
} from "../../shared/types/api";
import {
  projectWeeklySchedule,
  type PeriodRow,
  type WeekdayColumn,
  type WeekdayKey,
} from "./projectWeeklySchedule";
import { formatScheduleEntryType } from "./formatScheduleEntryType";

type LookupProps = {
  groups: GroupLookupItem[];
  rooms: RoomLookupItem[];
  subjects: SubjectLookupItem[];
  teachers: TeacherLookupItem[];
};

type WeeklyScheduleGridViewProps = {
  entries: ScheduleEntry[];
} & LookupProps;

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

function ScheduleSlotEntryCard({
  entry,
  groups,
  rooms,
  subjects,
  teachers,
}: {
  entry: ScheduleEntry;
} & LookupProps) {
  const subject = labelForId(subjects, entry.subject_id);
  const teacher = labelForId(teachers, entry.teacher_id);
  const room = labelForId(rooms, entry.room_id);
  const groupLabels = labelsForIds(groups, entry.group_ids);

  return (
    <article className="slot-entry">
      <div className="slot-entry-title">{subject}</div>
      <div>{teacher}</div>
      <div>
        {room} / {formatScheduleEntryType(entry.entry_type)}
      </div>
      <div>{groupLabels}</div>
    </article>
  );
}

function WeeklyScheduleGridCell({
  entries,
  groups,
  rooms,
  subjects,
  teachers,
}: {
  entries: ScheduleEntry[];
} & LookupProps) {
  if (entries.length === 0) {
    return <div className="weekly-grid-empty">-</div>;
  }

  return (
    <div className="weekly-grid-cell-stack">
      {entries.map((entry) => (
        <ScheduleSlotEntryCard
          key={entry.id}
          entry={entry}
          groups={groups}
          rooms={rooms}
          subjects={subjects}
          teachers={teachers}
        />
      ))}
    </div>
  );
}

function getProjectedEntries(
  cells: Map<string, Map<WeekdayKey, ScheduleEntry[]>>,
  period: PeriodRow,
  weekday: WeekdayColumn,
) {
  return cells.get(period.key)?.get(weekday.key) ?? [];
}

export function WeeklyScheduleGridView({
  entries,
  groups,
  rooms,
  subjects,
  teachers,
}: WeeklyScheduleGridViewProps) {
  const projection = useMemo(() => projectWeeklySchedule(entries), [entries]);

  return (
    <div className="weekly-grid-wrap">
      <div
        className="weekly-grid"
        style={
          {
            "--weekday-count": projection.weekdays.length,
          } as CSSProperties
        }
      >
        <div className="weekly-grid-corner">Пара</div>
        {projection.weekdays.map((weekday) => (
          <div className="weekly-grid-header" key={weekday.key}>
            {weekday.label}
          </div>
        ))}

        {projection.periods.map((period) => (
          <div className="weekly-grid-row" key={period.key}>
            <div className="weekly-grid-period">{period.label}</div>
            {projection.weekdays.map((weekday) => (
              <div
                className="weekly-grid-cell"
                key={`${period.key}-${weekday.key}`}
              >
                <WeeklyScheduleGridCell
                  entries={getProjectedEntries(
                    projection.cells,
                    period,
                    weekday,
                  )}
                  groups={groups}
                  rooms={rooms}
                  subjects={subjects}
                  teachers={teachers}
                />
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
