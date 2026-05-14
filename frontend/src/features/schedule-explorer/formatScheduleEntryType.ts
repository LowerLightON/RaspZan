import type { ScheduleEntry } from "../../shared/types/api";

const entryTypeLabels: Record<ScheduleEntry["entry_type"], string> = {
  lesson: "Занятие",
  day_off: "Выходной",
  self_study: "Самостоятельная работа",
};

export function formatScheduleEntryType(entryType: ScheduleEntry["entry_type"]) {
  return entryTypeLabels[entryType] ?? entryType;
}
