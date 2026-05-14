import type { PaginatedResponse, ScheduleEntry } from "../types/api";
import { apiRequest } from "./client";

export type ScheduleQueryParams = {
  date_from: string;
  date_to: string;
  subject_id?: number;
  teacher_id?: number;
  room_id?: number;
  limit: number;
  offset: number;
};

export function getGroupSchedule(
  groupId: number,
  params: ScheduleQueryParams,
) {
  return apiRequest<PaginatedResponse<ScheduleEntry>>(
    `/schedule/groups/${groupId}`,
    {
      query: params,
    },
  );
}

export function getTeacherSchedule(
  teacherId: number,
  params: ScheduleQueryParams,
) {
  return apiRequest<PaginatedResponse<ScheduleEntry>>(
    `/schedule/teachers/${teacherId}`,
    {
      query: params,
    },
  );
}

export function getRoomSchedule(roomId: number, params: ScheduleQueryParams) {
  return apiRequest<PaginatedResponse<ScheduleEntry>>(
    `/schedule/rooms/${roomId}`,
    {
      query: params,
    },
  );
}
