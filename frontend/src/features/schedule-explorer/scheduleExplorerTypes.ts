import type { ScheduleQueryParams } from "../../shared/api/schedule";

export type ScheduleExplorerKind = "group" | "teacher" | "room";

export type ScheduleExplorerDraft = {
  kind: ScheduleExplorerKind;
  entityId: string;
  dateFrom: string;
  dateTo: string;
  subjectId: string;
  teacherId: string;
  roomId: string;
  limit: string;
  offset: string;
};

export type ScheduleExplorerQuery = {
  kind: ScheduleExplorerKind;
  entityId: number;
  params: ScheduleQueryParams;
};
