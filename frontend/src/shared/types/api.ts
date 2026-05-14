export type PaginatedResponse<T> = {
  items: T[];
  total: number;
  limit: number;
  offset: number;
};

export type ApiErrorEnvelope = {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
};

export type ScheduleEntry = {
  id: number;
  entry_type: string;
  lesson_date: string;
  period_number: number;
  starts_at: string | null;
  ends_at: string | null;
  week_type: string;
  title: string | null;
  notes: string | null;
  lesson_plan_item_id: number | null;
  subject_id: number | null;
  teacher_id: number | null;
  room_id: number | null;
  group_ids: number[];
};

export type LookupItem = {
  id: number;
  label: string;
};

export type GroupLookupItem = LookupItem & {
  code: string;
};

export type TeacherLookupItem = LookupItem & {
  full_name: string;
};

export type RoomLookupItem = LookupItem & {
  number: string;
};

export type SubjectLookupItem = LookupItem & {
  name: string;
};
