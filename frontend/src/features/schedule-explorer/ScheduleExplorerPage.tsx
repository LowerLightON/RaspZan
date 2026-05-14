import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import {
  getGroupSchedule,
  getRoomSchedule,
  getTeacherSchedule,
  type ScheduleQueryParams,
} from "../../shared/api/schedule";
import { ScheduleExplorerForm } from "./ScheduleExplorerForm";
import { ScheduleExplorerResults } from "./ScheduleExplorerResults";
import type {
  ScheduleExplorerDraft,
  ScheduleExplorerQuery,
} from "./scheduleExplorerTypes";

const initialDraft: ScheduleExplorerDraft = {
  kind: "group",
  entityId: "",
  dateFrom: "",
  dateTo: "",
  subjectId: "",
  teacherId: "",
  roomId: "",
  limit: "20",
  offset: "0",
};

function optionalNumber(value: string) {
  return value === "" ? undefined : Number(value);
}

function toQuery(draft: ScheduleExplorerDraft): ScheduleExplorerQuery {
  const params: ScheduleQueryParams = {
    date_from: draft.dateFrom,
    date_to: draft.dateTo,
    subject_id: optionalNumber(draft.subjectId),
    limit: Number(draft.limit),
    offset: Number(draft.offset),
  };

  if (draft.kind !== "teacher") {
    params.teacher_id = optionalNumber(draft.teacherId);
  }

  if (draft.kind !== "room") {
    params.room_id = optionalNumber(draft.roomId);
  }

  return {
    kind: draft.kind,
    entityId: Number(draft.entityId),
    params,
  };
}

function fetchSchedule(query: ScheduleExplorerQuery) {
  if (query.kind === "group") {
    return getGroupSchedule(query.entityId, query.params);
  }

  if (query.kind === "teacher") {
    return getTeacherSchedule(query.entityId, query.params);
  }

  return getRoomSchedule(query.entityId, query.params);
}

export function ScheduleExplorerPage() {
  const [draft, setDraft] = useState(initialDraft);
  const [submittedQuery, setSubmittedQuery] =
    useState<ScheduleExplorerQuery | null>(null);

  const scheduleQuery = useQuery({
    queryKey: ["schedule", submittedQuery],
    queryFn: () => fetchSchedule(submittedQuery!),
    enabled: submittedQuery !== null,
  });

  return (
    <main className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">RaspZan</p>
          <h1>Schedule Explorer</h1>
        </div>
      </header>

      <ScheduleExplorerForm
        draft={draft}
        isLoading={scheduleQuery.isFetching}
        onChange={setDraft}
        onSubmit={() => setSubmittedQuery(toQuery(draft))}
      />

      <ScheduleExplorerResults
        data={scheduleQuery.data}
        error={scheduleQuery.error}
        hasSubmitted={submittedQuery !== null}
        isError={scheduleQuery.isError}
        isFetching={scheduleQuery.isFetching}
      />
    </main>
  );
}
