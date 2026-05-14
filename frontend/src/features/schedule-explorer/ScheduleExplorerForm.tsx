import type { FormEvent } from "react";
import type {
  GroupLookupItem,
  LookupItem,
  RoomLookupItem,
  SubjectLookupItem,
  TeacherLookupItem,
} from "../../shared/types/api";
import { Button } from "../../shared/ui/Button";
import { ErrorMessage } from "../../shared/ui/ErrorMessage";
import { Field } from "../../shared/ui/Field";
import { Input } from "../../shared/ui/Input";
import { Select } from "../../shared/ui/Select";
import type {
  ScheduleExplorerDraft,
  ScheduleExplorerKind,
  ScheduleExplorerView,
} from "./scheduleExplorerTypes";

type ScheduleExplorerFormProps = {
  draft: ScheduleExplorerDraft;
  groups: GroupLookupItem[];
  teachers: TeacherLookupItem[];
  rooms: RoomLookupItem[];
  subjects: SubjectLookupItem[];
  isLookupError: boolean;
  isLookupLoading: boolean;
  isLoading: boolean;
  lookupError: unknown;
  onChange: (draft: ScheduleExplorerDraft) => void;
  onSubmit: () => void;
  view: ScheduleExplorerView;
};

const scheduleTypeLabels: Record<ScheduleExplorerKind, string> = {
  group: "Group",
  teacher: "Teacher",
  room: "Room",
};

const mainSelectPlaceholder: Record<ScheduleExplorerKind, string> = {
  group: "Select group",
  teacher: "Select teacher",
  room: "Select room",
};

function renderLookupOptions(items: LookupItem[]) {
  return items.map((item) => (
    <option key={item.id} value={String(item.id)}>
      {item.label}
    </option>
  ));
}

export function ScheduleExplorerForm({
  draft,
  groups,
  teachers,
  rooms,
  subjects,
  isLookupError,
  isLookupLoading,
  isLoading,
  lookupError,
  onChange,
  onSubmit,
  view,
}: ScheduleExplorerFormProps) {
  function updateField<K extends keyof ScheduleExplorerDraft>(
    field: K,
    value: ScheduleExplorerDraft[K],
  ) {
    onChange({ ...draft, [field]: value });
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit();
  }

  function handleKindChange(kind: ScheduleExplorerKind) {
    onChange({ ...draft, kind, entityId: "" });
  }

  const mainItems =
    draft.kind === "group" ? groups : draft.kind === "teacher" ? teachers : rooms;
  const formDisabled = isLookupLoading || isLookupError;
  const paginationDisabled = view === "grid";

  return (
    <>
      {isLookupError ? (
        <ErrorMessage error={lookupError} title="Could not load lookup data" />
      ) : null}
      <form className="panel form-grid" onSubmit={handleSubmit}>
        <Field label="Schedule type">
          <Select
            disabled={formDisabled}
            value={draft.kind}
            onChange={(event) =>
              handleKindChange(event.target.value as ScheduleExplorerKind)
            }
          >
            {Object.entries(scheduleTypeLabels).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
        </Field>

        <Field label={scheduleTypeLabels[draft.kind]}>
          <Select
            disabled={formDisabled}
            required
            value={draft.entityId}
            onChange={(event) => updateField("entityId", event.target.value)}
          >
            <option value="">{mainSelectPlaceholder[draft.kind]}</option>
            {renderLookupOptions(mainItems)}
          </Select>
        </Field>

        <Field label="Date from">
          <Input
            required
            type="date"
            value={draft.dateFrom}
            onChange={(event) => updateField("dateFrom", event.target.value)}
          />
        </Field>

        <Field label="Date to">
          <Input
            required
            type="date"
            value={draft.dateTo}
            onChange={(event) => updateField("dateTo", event.target.value)}
          />
        </Field>

        <Field label="Subject">
          <Select
            disabled={formDisabled}
            value={draft.subjectId}
            onChange={(event) => updateField("subjectId", event.target.value)}
          >
            <option value="">Any subject</option>
            {renderLookupOptions(subjects)}
          </Select>
        </Field>

        {draft.kind !== "room" ? (
          <Field label="Room">
            <Select
              disabled={formDisabled}
              value={draft.roomId}
              onChange={(event) => updateField("roomId", event.target.value)}
            >
              <option value="">Any room</option>
              {renderLookupOptions(rooms)}
            </Select>
          </Field>
        ) : null}

        {draft.kind !== "teacher" ? (
          <Field label="Teacher">
            <Select
              disabled={formDisabled}
              value={draft.teacherId}
              onChange={(event) => updateField("teacherId", event.target.value)}
            >
              <option value="">Any teacher</option>
              {renderLookupOptions(teachers)}
            </Select>
          </Field>
        ) : null}

        <Field label="Limit">
          <Input
            disabled={paginationDisabled}
            max="100"
            min="1"
            required
            type="number"
            value={draft.limit}
            onChange={(event) => updateField("limit", event.target.value)}
          />
        </Field>

        <Field label="Offset">
          <Input
            disabled={paginationDisabled}
            min="0"
            required
            type="number"
            value={draft.offset}
            onChange={(event) => updateField("offset", event.target.value)}
          />
        </Field>

        <div className="form-actions">
          <Button disabled={isLoading || formDisabled} type="submit">
            {isLoading ? "Loading..." : "Load schedule"}
          </Button>
        </div>
      </form>
    </>
  );
}
