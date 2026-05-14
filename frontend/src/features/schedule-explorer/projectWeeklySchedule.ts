import type { ScheduleEntry } from "../../shared/types/api";

export type WeekdayKey =
  | "monday"
  | "tuesday"
  | "wednesday"
  | "thursday"
  | "friday"
  | "saturday";

export type WeekdayColumn = {
  key: WeekdayKey;
  label: string;
};

export type PeriodRow = {
  key: string;
  label: string;
  startPeriod: number;
};

export type WeeklyScheduleProjection = {
  weekdays: WeekdayColumn[];
  periods: PeriodRow[];
  cells: Map<string, Map<WeekdayKey, ScheduleEntry[]>>;
};

export const weeklyScheduleWeekdays: WeekdayColumn[] = [
  { key: "monday", label: "Monday" },
  { key: "tuesday", label: "Tuesday" },
  { key: "wednesday", label: "Wednesday" },
  { key: "thursday", label: "Thursday" },
  { key: "friday", label: "Friday" },
  { key: "saturday", label: "Saturday" },
];

const minimumPeriodPairs = [1, 3, 5, 7, 9, 11];

function normalizeWeekday(lessonDate: string): WeekdayKey | null {
  const [year, month, day] = lessonDate.split("-").map(Number);

  if (!year || !month || !day) {
    return null;
  }

  const weekdayIndex = new Date(year, month - 1, day).getDay();

  if (weekdayIndex < 1 || weekdayIndex > 6) {
    return null;
  }

  return weeklyScheduleWeekdays[weekdayIndex - 1].key;
}

function normalizePeriodStart(periodNumber: number) {
  if (!Number.isFinite(periodNumber) || periodNumber < 1) {
    return 1;
  }

  return periodNumber % 2 === 0 ? periodNumber - 1 : periodNumber;
}

function buildPeriodRow(startPeriod: number): PeriodRow {
  return {
    key: String(startPeriod),
    label: `${startPeriod}-${startPeriod + 1}`,
    startPeriod,
  };
}

function compareEntries(first: ScheduleEntry, second: ScheduleEntry) {
  return (
    first.lesson_date.localeCompare(second.lesson_date) ||
    first.period_number - second.period_number ||
    first.entry_type.localeCompare(second.entry_type) ||
    first.id - second.id
  );
}

export function projectWeeklySchedule(
  entries: ScheduleEntry[],
): WeeklyScheduleProjection {
  const periodStarts = new Set(minimumPeriodPairs);
  const cells = new Map<string, Map<WeekdayKey, ScheduleEntry[]>>();

  for (const startPeriod of minimumPeriodPairs) {
    const periodKey = String(startPeriod);
    const weekdayCells = new Map<WeekdayKey, ScheduleEntry[]>();

    for (const weekday of weeklyScheduleWeekdays) {
      weekdayCells.set(weekday.key, []);
    }

    cells.set(periodKey, weekdayCells);
  }

  for (const entry of entries) {
    const weekday = normalizeWeekday(entry.lesson_date);

    if (weekday === null) {
      continue;
    }

    const startPeriod = normalizePeriodStart(entry.period_number);
    const periodKey = String(startPeriod);
    periodStarts.add(startPeriod);

    if (!cells.has(periodKey)) {
      const weekdayCells = new Map<WeekdayKey, ScheduleEntry[]>();

      for (const weekdayColumn of weeklyScheduleWeekdays) {
        weekdayCells.set(weekdayColumn.key, []);
      }

      cells.set(periodKey, weekdayCells);
    }

    cells.get(periodKey)?.get(weekday)?.push(entry);
  }

  for (const weekdayCells of cells.values()) {
    for (const slotEntries of weekdayCells.values()) {
      slotEntries.sort(compareEntries);
    }
  }

  return {
    weekdays: weeklyScheduleWeekdays,
    periods: [...periodStarts].sort((a, b) => a - b).map(buildPeriodRow),
    cells,
  };
}
