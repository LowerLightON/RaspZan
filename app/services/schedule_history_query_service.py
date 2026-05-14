from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import ScheduleChangeType
from app.models.schedule import ScheduleChange, ScheduleEntry


@dataclass(frozen=True)
class ScheduleEntryHistory:
    requested_entry_id: int
    root_entry: ScheduleEntry
    changes: list[ScheduleChange]
    truncated: bool = False


class ScheduleHistoryQueryService:
    def __init__(self, max_depth: int = 50) -> None:
        self.max_depth = max_depth

    def get_entry_history(
        self,
        db: Session,
        entry_id: int,
    ) -> ScheduleEntryHistory | None:
        seed_entry = db.get(ScheduleEntry, entry_id)
        if seed_entry is None:
            return None

        root_entry, root_truncated = self._find_root_entry(db, seed_entry)
        changes, chain_truncated = self._collect_forward_changes(db, root_entry)

        return ScheduleEntryHistory(
            requested_entry_id=entry_id,
            root_entry=root_entry,
            changes=changes,
            truncated=root_truncated or chain_truncated,
        )

    def _find_root_entry(
        self,
        db: Session,
        seed_entry: ScheduleEntry,
    ) -> tuple[ScheduleEntry, bool]:
        current_entry = seed_entry
        visited_entry_ids = {seed_entry.id}

        for _ in range(self.max_depth):
            incoming_change = db.scalar(
                self._ordered_changes_statement().where(
                    ScheduleChange.replacement_entry_id == current_entry.id,
                )
            )
            if incoming_change is None:
                return current_entry, False

            original_entry = db.get(ScheduleEntry, incoming_change.original_entry_id)
            if original_entry is None or original_entry.id in visited_entry_ids:
                return current_entry, True

            visited_entry_ids.add(original_entry.id)
            current_entry = original_entry

        return current_entry, True

    def _collect_forward_changes(
        self,
        db: Session,
        root_entry: ScheduleEntry,
    ) -> tuple[list[ScheduleChange], bool]:
        current_entry = root_entry
        visited_entry_ids = {root_entry.id}
        visited_change_ids: set[int] = set()
        changes: list[ScheduleChange] = []

        for _ in range(self.max_depth):
            outgoing_changes = list(
                db.scalars(
                    self._ordered_changes_statement().where(
                        ScheduleChange.original_entry_id == current_entry.id,
                    )
                ).all()
            )
            if not outgoing_changes:
                return changes, False

            next_entry: ScheduleEntry | None = None
            for change in outgoing_changes:
                if change.id in visited_change_ids:
                    return changes, True

                visited_change_ids.add(change.id)
                changes.append(change)

                if change.change_type == ScheduleChangeType.CANCELLATION:
                    continue

                if next_entry is None and change.replacement_entry_id is not None:
                    replacement_entry = db.get(
                        ScheduleEntry,
                        change.replacement_entry_id,
                    )
                    if (
                        replacement_entry is not None
                        and replacement_entry.id not in visited_entry_ids
                    ):
                        next_entry = replacement_entry

            if next_entry is None:
                return changes, False

            visited_entry_ids.add(next_entry.id)
            current_entry = next_entry

        return changes, True

    def _ordered_changes_statement(self):
        return select(ScheduleChange).order_by(
            ScheduleChange.effective_date,
            ScheduleChange.created_at,
            ScheduleChange.id,
        )
