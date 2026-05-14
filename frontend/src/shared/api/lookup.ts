import type {
  GroupLookupItem,
  RoomLookupItem,
  SubjectLookupItem,
  TeacherLookupItem,
} from "../types/api";
import { apiRequest } from "./client";

export function getGroupsLookup() {
  return apiRequest<GroupLookupItem[]>("/lookup/groups");
}

export function getTeachersLookup() {
  return apiRequest<TeacherLookupItem[]>("/lookup/teachers");
}

export function getRoomsLookup() {
  return apiRequest<RoomLookupItem[]>("/lookup/rooms");
}

export function getSubjectsLookup() {
  return apiRequest<SubjectLookupItem[]>("/lookup/subjects");
}
