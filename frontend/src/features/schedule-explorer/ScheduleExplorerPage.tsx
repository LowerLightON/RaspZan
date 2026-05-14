import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import {
  getGroupsLookup,
  getRoomsLookup,
  getSubjectsLookup,
  getTeachersLookup,
} from "../../shared/api/lookup";
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
  ScheduleExplorerView,
} from "./scheduleExplorerTypes";
import { initialScheduleExplorerDraft } from "./scheduleExplorerTypes";
import {
  buildScheduleExplorerSearchParams,
  parseScheduleExplorerSearchParams,
} from "./scheduleExplorerUrlState";

const lookupStaleTime = 5 * 60 * 1000;
const gridQueryLimit = 100;

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

function toEffectiveQuery(
  query: ScheduleExplorerQuery | null,
  view: ScheduleExplorerView,
) {
  if (query === null || view !== "grid") {
    return query;
  }

  return {
    ...query,
    params: {
      ...query.params,
      limit: gridQueryLimit,
      offset: 0,
    },
  };
}

function readStateFromSearch(search: string) {
  const parsed = parseScheduleExplorerSearchParams(search);

  if (!parsed.valid) {
    return {
      draft: initialScheduleExplorerDraft,
      submittedQuery: null,
      view: parsed.view,
    };
  }

  return {
    draft: parsed.draft,
    submittedQuery: toQuery(parsed.draft),
    view: parsed.view,
  };
}

export function ScheduleExplorerPage() {
  const [draft, setDraft] = useState(
    () => readStateFromSearch(window.location.search).draft,
  );
  const [submittedQuery, setSubmittedQuery] =
    useState<ScheduleExplorerQuery | null>(
      () => readStateFromSearch(window.location.search).submittedQuery,
    );
  const [view, setView] = useState<ScheduleExplorerView>(
    () => readStateFromSearch(window.location.search).view,
  );

  useEffect(() => {
    function handlePopState() {
      const nextState = readStateFromSearch(window.location.search);

      setDraft(nextState.draft);
      setSubmittedQuery(nextState.submittedQuery);
      setView(nextState.view);
    }

    window.addEventListener("popstate", handlePopState);

    return () => {
      window.removeEventListener("popstate", handlePopState);
    };
  }, []);

  function handleSubmit() {
    const nextQuery = toQuery(draft);
    const nextSearch = buildScheduleExplorerSearchParams(draft, view).toString();
    const nextUrl = `${window.location.pathname}?${nextSearch}${window.location.hash}`;

    setSubmittedQuery(nextQuery);

    if (window.location.search !== `?${nextSearch}`) {
      window.history.pushState(null, "", nextUrl);
    }
  }

  function handleViewChange(nextView: ScheduleExplorerView) {
    setView(nextView);

    if (submittedQuery === null) {
      return;
    }

    const nextSearch = buildScheduleExplorerSearchParams(draft, nextView).toString();
    const nextUrl = `${window.location.pathname}?${nextSearch}${window.location.hash}`;

    if (window.location.search !== `?${nextSearch}`) {
      window.history.pushState(null, "", nextUrl);
    }
  }

  const groupsQuery = useQuery({
    queryKey: ["lookup", "groups"],
    queryFn: getGroupsLookup,
    staleTime: lookupStaleTime,
  });
  const teachersQuery = useQuery({
    queryKey: ["lookup", "teachers"],
    queryFn: getTeachersLookup,
    staleTime: lookupStaleTime,
  });
  const roomsQuery = useQuery({
    queryKey: ["lookup", "rooms"],
    queryFn: getRoomsLookup,
    staleTime: lookupStaleTime,
  });
  const subjectsQuery = useQuery({
    queryKey: ["lookup", "subjects"],
    queryFn: getSubjectsLookup,
    staleTime: lookupStaleTime,
  });
  const effectiveScheduleQuery = toEffectiveQuery(submittedQuery, view);
  const scheduleQuery = useQuery({
    queryKey: ["schedule", effectiveScheduleQuery],
    queryFn: () => fetchSchedule(effectiveScheduleQuery!),
    enabled: effectiveScheduleQuery !== null,
  });

  const lookupQueries = [groupsQuery, teachersQuery, roomsQuery, subjectsQuery];
  const lookupError = lookupQueries.find((query) => query.error)?.error ?? null;
  const isLookupLoading = lookupQueries.some((query) => query.isLoading);
  const isLookupError = lookupQueries.some((query) => query.isError);

  return (
    <main className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">RaspZan</p>
          <h1>Просмотр расписания</h1>
        </div>
      </header>

      <ScheduleExplorerForm
        draft={draft}
        groups={groupsQuery.data ?? []}
        isLookupError={isLookupError}
        isLookupLoading={isLookupLoading}
        isLoading={scheduleQuery.isFetching}
        lookupError={lookupError}
        onChange={setDraft}
        onSubmit={handleSubmit}
        rooms={roomsQuery.data ?? []}
        subjects={subjectsQuery.data ?? []}
        teachers={teachersQuery.data ?? []}
        view={view}
      />

      <ScheduleExplorerResults
        data={scheduleQuery.data}
        error={scheduleQuery.error}
        groups={groupsQuery.data ?? []}
        hasSubmitted={submittedQuery !== null}
        isError={scheduleQuery.isError}
        isFetching={scheduleQuery.isFetching}
        rooms={roomsQuery.data ?? []}
        subjects={subjectsQuery.data ?? []}
        teachers={teachersQuery.data ?? []}
        view={view}
        onViewChange={handleViewChange}
      />
    </main>
  );
}
