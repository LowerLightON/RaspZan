import {
  initialScheduleExplorerDraft,
  type ScheduleExplorerDraft,
  type ScheduleExplorerKind,
  type ScheduleExplorerView,
} from "./scheduleExplorerTypes";

export type ParsedScheduleExplorerUrl =
  | { valid: true; draft: ScheduleExplorerDraft; view: ScheduleExplorerView }
  | { valid: false; draft: ScheduleExplorerDraft; view: ScheduleExplorerView };

const validKinds = new Set<ScheduleExplorerKind>(["group", "teacher", "room"]);
const validViews = new Set<ScheduleExplorerView>(["table", "grid"]);
const datePattern = /^\d{4}-\d{2}-\d{2}$/;
const positiveIntegerPattern = /^[1-9]\d*$/;
const nonNegativeIntegerPattern = /^(0|[1-9]\d*)$/;
const initialView: ScheduleExplorerView = "table";

function isScheduleExplorerKind(value: string | null): value is ScheduleExplorerKind {
  return value !== null && validKinds.has(value as ScheduleExplorerKind);
}

function isScheduleExplorerView(value: string | null): value is ScheduleExplorerView {
  return value !== null && validViews.has(value as ScheduleExplorerView);
}

function isPositiveInteger(value: string | null): value is string {
  return value !== null && positiveIntegerPattern.test(value);
}

function isNonNegativeInteger(value: string | null): value is string {
  return value !== null && nonNegativeIntegerPattern.test(value);
}

function parseOptionalPositiveInteger(value: string | null) {
  if (value === null) {
    return "";
  }

  return isPositiveInteger(value) ? value : null;
}

function parseLimit(value: string | null) {
  if (value === null) {
    return initialScheduleExplorerDraft.limit;
  }

  if (!isPositiveInteger(value)) {
    return null;
  }

  const parsed = Number(value);
  return parsed >= 1 && parsed <= 100 ? value : null;
}

function parseOffset(value: string | null) {
  if (value === null) {
    return initialScheduleExplorerDraft.offset;
  }

  return isNonNegativeInteger(value) ? value : null;
}

export function parseScheduleExplorerSearchParams(
  search: string,
): ParsedScheduleExplorerUrl {
  const params = new URLSearchParams(search);

  if ([...params.keys()].length === 0) {
    return {
      valid: false,
      draft: initialScheduleExplorerDraft,
      view: initialView,
    };
  }

  const viewParam = params.get("view");
  const view = viewParam === null ? initialView : viewParam;
  const kind = params.get("kind");
  const entityId = params.get("entityId");
  const dateFrom = params.get("dateFrom");
  const dateTo = params.get("dateTo");
  const subjectId = parseOptionalPositiveInteger(params.get("subjectId"));
  const teacherId = parseOptionalPositiveInteger(params.get("teacherId"));
  const roomId = parseOptionalPositiveInteger(params.get("roomId"));
  const limit = parseLimit(params.get("limit"));
  const offset = parseOffset(params.get("offset"));

  if (
    !isScheduleExplorerKind(kind) ||
    !isPositiveInteger(entityId) ||
    dateFrom === null ||
    !datePattern.test(dateFrom) ||
    dateTo === null ||
    !datePattern.test(dateTo) ||
    subjectId === null ||
    teacherId === null ||
    roomId === null ||
    limit === null ||
    offset === null ||
    !isScheduleExplorerView(view)
  ) {
    return {
      valid: false,
      draft: initialScheduleExplorerDraft,
      view: initialView,
    };
  }

  return {
    valid: true,
    view,
    draft: {
      kind,
      entityId,
      dateFrom,
      dateTo,
      subjectId,
      teacherId,
      roomId,
      limit,
      offset,
    },
  };
}

export function buildScheduleExplorerSearchParams(
  draft: ScheduleExplorerDraft,
  view: ScheduleExplorerView = initialView,
) {
  const params = new URLSearchParams();

  if (view !== initialView) {
    params.set("view", view);
  }

  params.set("kind", draft.kind);
  params.set("entityId", draft.entityId);
  params.set("dateFrom", draft.dateFrom);
  params.set("dateTo", draft.dateTo);

  if (draft.subjectId !== "") {
    params.set("subjectId", draft.subjectId);
  }

  if (draft.teacherId !== "") {
    params.set("teacherId", draft.teacherId);
  }

  if (draft.roomId !== "") {
    params.set("roomId", draft.roomId);
  }

  params.set("limit", draft.limit);
  params.set("offset", draft.offset);

  return params;
}
