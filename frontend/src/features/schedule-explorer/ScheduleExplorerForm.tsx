import type { FormEvent } from "react";
import { Button } from "../../shared/ui/Button";
import { Field } from "../../shared/ui/Field";
import { Input } from "../../shared/ui/Input";
import { Select } from "../../shared/ui/Select";
import type {
  ScheduleExplorerDraft,
  ScheduleExplorerKind,
} from "./scheduleExplorerTypes";

type ScheduleExplorerFormProps = {
  draft: ScheduleExplorerDraft;
  isLoading: boolean;
  onChange: (draft: ScheduleExplorerDraft) => void;
  onSubmit: () => void;
};

const scheduleTypeLabels: Record<ScheduleExplorerKind, string> = {
  group: "Group",
  teacher: "Teacher",
  room: "Room",
};

export function ScheduleExplorerForm({
  draft,
  isLoading,
  onChange,
  onSubmit,
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

  return (
    <form className="panel form-grid" onSubmit={handleSubmit}>
      <Field label="Schedule type">
        <Select
          value={draft.kind}
          onChange={(event) =>
            updateField("kind", event.target.value as ScheduleExplorerKind)
          }
        >
          {Object.entries(scheduleTypeLabels).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </Select>
      </Field>

      <Field label={`${scheduleTypeLabels[draft.kind]} ID`}>
        <Input
          min="1"
          required
          type="number"
          value={draft.entityId}
          onChange={(event) => updateField("entityId", event.target.value)}
        />
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

      <Field label="Subject ID">
        <Input
          min="1"
          type="number"
          value={draft.subjectId}
          onChange={(event) => updateField("subjectId", event.target.value)}
        />
      </Field>

      {draft.kind !== "room" ? (
        <Field label="Room ID">
          <Input
            min="1"
            type="number"
            value={draft.roomId}
            onChange={(event) => updateField("roomId", event.target.value)}
          />
        </Field>
      ) : null}

      {draft.kind !== "teacher" ? (
        <Field label="Teacher ID">
          <Input
            min="1"
            type="number"
            value={draft.teacherId}
            onChange={(event) => updateField("teacherId", event.target.value)}
          />
        </Field>
      ) : null}

      <Field label="Limit">
        <Input
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
          min="0"
          required
          type="number"
          value={draft.offset}
          onChange={(event) => updateField("offset", event.target.value)}
        />
      </Field>

      <div className="form-actions">
        <Button disabled={isLoading} type="submit">
          {isLoading ? "Loading..." : "Load schedule"}
        </Button>
      </div>
    </form>
  );
}
