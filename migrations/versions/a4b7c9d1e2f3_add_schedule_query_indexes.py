"""add schedule query indexes

Revision ID: a4b7c9d1e2f3
Revises: 274c8eda9f3c
Create Date: 2026-05-14 16:30:00.000000
"""

from collections.abc import Sequence

from alembic import op


revision: str = "a4b7c9d1e2f3"
down_revision: str | Sequence[str] | None = "274c8eda9f3c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_schedule_entries_teacher_date_period",
        "schedule_entries",
        ["teacher_id", "lesson_date", "period_number"],
        unique=False,
    )
    op.create_index(
        "ix_schedule_entries_room_date_period",
        "schedule_entries",
        ["room_id", "lesson_date", "period_number"],
        unique=False,
    )
    op.create_index(
        "ix_schedule_entries_date_period",
        "schedule_entries",
        ["lesson_date", "period_number"],
        unique=False,
    )
    op.create_index(
        "ix_schedule_entry_groups_group_entry",
        "schedule_entry_groups",
        ["study_group_id", "schedule_entry_id"],
        unique=False,
    )
    op.create_index(
        "ix_schedule_entry_groups_entry",
        "schedule_entry_groups",
        ["schedule_entry_id"],
        unique=False,
    )
    op.create_index(
        "ix_schedule_changes_original_type",
        "schedule_changes",
        ["original_entry_id", "change_type"],
        unique=False,
    )
    op.create_index(
        "ix_schedule_changes_replacement_entry",
        "schedule_changes",
        ["replacement_entry_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_schedule_changes_replacement_entry",
        table_name="schedule_changes",
    )
    op.drop_index(
        "ix_schedule_changes_original_type",
        table_name="schedule_changes",
    )
    op.drop_index(
        "ix_schedule_entry_groups_entry",
        table_name="schedule_entry_groups",
    )
    op.drop_index(
        "ix_schedule_entry_groups_group_entry",
        table_name="schedule_entry_groups",
    )
    op.drop_index(
        "ix_schedule_entries_date_period",
        table_name="schedule_entries",
    )
    op.drop_index(
        "ix_schedule_entries_room_date_period",
        table_name="schedule_entries",
    )
    op.drop_index(
        "ix_schedule_entries_teacher_date_period",
        table_name="schedule_entries",
    )
