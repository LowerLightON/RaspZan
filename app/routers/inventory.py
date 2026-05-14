import re

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import distinct, func, select, text
from sqlalchemy.orm import Session

from app.db.legacy import get_legacy_db
from app.models.legacy import (
    LegacyClassroom,
    LegacyDepartment,
    LegacyGroup,
    LegacyUser,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])

DEBUG_TABLES = ("p_group", "p_caf")
SEARCH_COLUMNS = {"groups", "facult", "caf", "caf_code", "fio", "fm", "im", "ot"}
NAME_HINTS = (
    "group",
    "teacher",
    "subject",
    "schedule",
    "rasp",
    "caf",
    "aud",
    "room",
    "lesson",
    "para",
)
CYRILLIC_PATTERN = re.compile(r"[\u0400-\u04FF]")
TABLES_SEARCH_LIMIT = 50


def _quote_identifier(identifier: str) -> str:
    return f'"{identifier.replace(chr(34), chr(34) * 2)}"'


def _public_tables(db: Session) -> list[str]:
    return list(
        db.execute(
            text(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_type = 'BASE TABLE'
                ORDER BY table_name
                """
            )
        ).scalars().all()
    )


def _text_columns(db: Session, table_name: str) -> list[str]:
    return list(
        db.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = :table_name
                  AND data_type IN ('character varying', 'character', 'text')
                ORDER BY ordinal_position
                """
            ),
            {"table_name": table_name},
        ).scalars().all()
    )


def _columns(db: Session, table_name: str) -> list[str]:
    return list(
        db.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = :table_name
                ORDER BY ordinal_position
                """
            ),
            {"table_name": table_name},
        ).scalars().all()
    )


def _column_metadata(db: Session, table_name: str) -> list[dict[str, object]]:
    return [
        dict(row)
        for row in db.execute(
            text(
                """
                SELECT column_name AS name,
                       data_type,
                       udt_name,
                       ordinal_position
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = :table_name
                ORDER BY ordinal_position
                """
            ),
            {"table_name": table_name},
        ).mappings().all()
    ]


def _table_exists(db: Session, table_name: str) -> bool:
    return bool(
        db.scalar(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_type = 'BASE TABLE'
                      AND table_name = :table_name
                )
                """
            ),
            {"table_name": table_name},
        )
    )


def _grid_columns_count(columns: list[dict[str, object]]) -> int:
    return sum(1 for column in columns if str(column["name"]).isdigit())


def _is_grid_like(columns: list[dict[str, object]]) -> bool:
    return len(columns) > 30 and _grid_columns_count(columns) >= 3


def _excluded_columns(exclude_columns: str) -> set[str]:
    return {
        column.strip().lower()
        for column in exclude_columns.split(",")
        if column.strip()
    }


def _name_hints(table_name: str) -> list[str]:
    normalized = table_name.lower()
    return [hint for hint in NAME_HINTS if hint in normalized]


@router.get("/summary")
def inventory_summary(db: Session = Depends(get_legacy_db)) -> dict[str, int]:
    users_count = db.scalar(select(func.count()).select_from(LegacyUser)) or 0
    groups_count = db.scalar(select(func.count()).select_from(LegacyGroup)) or 0
    departments_count = (
        db.scalar(select(func.count(distinct(LegacyDepartment.caf_code)))) or 0
    )
    classrooms_count = db.scalar(select(func.count()).select_from(LegacyClassroom)) or 0

    return {
        "users_count": users_count,
        "groups_count": groups_count,
        "departments_count": departments_count,
        "classrooms_count": classrooms_count,
    }


def _debug_table(db: Session, table_name: str) -> dict[str, object]:
    columns = db.execute(
        text(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = :table_name
            ORDER BY ordinal_position
            """
        ),
        {"table_name": table_name},
    ).scalars().all()

    if not columns:
        return {
            "exists": False,
            "row_count": None,
            "columns": [],
            "sample_rows": [],
        }

    quoted_table = _quote_identifier(table_name)
    row_count = db.scalar(text(f"SELECT count(*) FROM {quoted_table}")) or 0
    sample_rows = db.execute(text(f"SELECT * FROM {quoted_table} LIMIT 3")).mappings().all()

    return {
        "exists": True,
        "row_count": row_count,
        "columns": list(columns),
        "sample_rows": [dict(row) for row in sample_rows],
    }


@router.get("/debug")
def inventory_debug(db: Session = Depends(get_legacy_db)) -> dict[str, object]:
    return {
        table_name: _debug_table(db, table_name)
        for table_name in DEBUG_TABLES
    }


@router.get("/tables-search")
def inventory_tables_search(db: Session = Depends(get_legacy_db)) -> dict[str, object]:
    tables = _public_tables(db)

    results = []

    for table_name in tables:
        quoted_table = _quote_identifier(table_name)
        row_count = db.scalar(text(f"SELECT count(*) FROM {quoted_table}")) or 0

        if row_count == 0:
            continue

        columns = db.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = :table_name
                ORDER BY ordinal_position
                """
            ),
            {"table_name": table_name},
        ).scalars().all()
        sample_rows = (
            db.execute(text(f"SELECT * FROM {quoted_table} LIMIT 2")).mappings().all()
        )

        matched_columns = [
            column for column in columns if column.lower() in SEARCH_COLUMNS
        ]

        results.append(
            {
                "table_name": table_name,
                "row_count": row_count,
                "columns": list(columns),
                "has_matching_columns": bool(matched_columns),
                "matched_columns": matched_columns,
                "sample_rows": [dict(row) for row in sample_rows],
            }
        )

        if len(results) >= TABLES_SEARCH_LIMIT:
            break

    return {
        "limit": TABLES_SEARCH_LIMIT,
        "returned_count": len(results),
        "tables": results,
    }


@router.get("/non-empty-values")
def inventory_non_empty_values(
    limit_tables: int = Query(default=50, ge=1, le=500),
    limit_values_per_table: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_legacy_db),
) -> dict[str, object]:
    results = []

    for table_name in _public_tables(db)[:limit_tables]:
        quoted_table = _quote_identifier(table_name)
        values_for_table = 0

        for column_name in _text_columns(db, table_name):
            if values_for_table >= limit_values_per_table:
                break

            quoted_column = _quote_identifier(column_name)
            remaining_values = limit_values_per_table - values_for_table
            rows = db.execute(
                text(
                    f"""
                    SELECT
                        {quoted_column} AS value,
                        count(*) AS row_count_column_value
                    FROM {quoted_table}
                    WHERE {quoted_column} IS NOT NULL
                      AND btrim({quoted_column}) <> ''
                    GROUP BY {quoted_column}
                    ORDER BY row_count_column_value DESC, value
                    LIMIT :limit_values
                    """
                ),
                {"limit_values": remaining_values},
            ).mappings().all()

            for row in rows:
                results.append(
                    {
                        "table_name": table_name,
                        "column_name": column_name,
                        "row_count_column_value": row["row_count_column_value"],
                        "value": row["value"],
                    }
                )

            values_for_table += len(rows)

    return {
        "limit_tables": limit_tables,
        "limit_values_per_table": limit_values_per_table,
        "returned_count": len(results),
        "values": results,
    }


@router.get("/raw-values")
def inventory_raw_values(
    limit_tables: int = Query(default=50, ge=1, le=500),
    limit_values_per_table: int = Query(default=20, ge=1, le=200),
    exclude_columns: str = Query(default="count,id"),
    min_value_length: int = Query(default=2, ge=1, le=300),
    db: Session = Depends(get_legacy_db),
) -> dict[str, object]:
    results = []
    skipped_columns = []
    excluded_columns = _excluded_columns(exclude_columns)

    for table_name in _public_tables(db)[:limit_tables]:
        quoted_table = _quote_identifier(table_name)
        values_for_table = 0

        for column_name in _columns(db, table_name):
            if values_for_table >= limit_values_per_table:
                break
            if column_name.lower() in excluded_columns:
                continue

            quoted_column = _quote_identifier(column_name)
            remaining_values = limit_values_per_table - values_for_table

            try:
                rows = db.execute(
                    text(
                        f"""
                        SELECT DISTINCT
                            left(btrim(({quoted_column})::text), 300) AS value
                        FROM {quoted_table}
                        WHERE {quoted_column} IS NOT NULL
                          AND btrim(({quoted_column})::text) <> ''
                          AND length(btrim(({quoted_column})::text)) >= :min_value_length
                        ORDER BY value
                        LIMIT :limit_values
                        """
                    ),
                    {
                        "limit_values": remaining_values,
                        "min_value_length": min_value_length,
                    },
                ).mappings().all()
            except Exception as exc:
                db.rollback()
                skipped_columns.append(
                    {
                        "table_name": table_name,
                        "column_name": column_name,
                        "error": str(exc),
                    }
                )
                continue

            for row in rows:
                results.append(
                    {
                        "table_name": table_name,
                        "column_name": column_name,
                        "value": row["value"],
                    }
                )

            values_for_table += len(rows)

    return {
        "limit_tables": limit_tables,
        "limit_values_per_table": limit_values_per_table,
        "exclude_columns": sorted(excluded_columns),
        "min_value_length": min_value_length,
        "returned_count": len(results),
        "values": results,
        "debug": {
            "skipped_columns_count": len(skipped_columns),
            "skipped_columns": skipped_columns,
        },
    }


@router.get("/tables-overview")
def inventory_tables_overview(
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    only_non_empty: bool = Query(default=True),
    only_grids: bool = Query(default=False),
    db: Session = Depends(get_legacy_db),
) -> dict[str, object]:
    tables = _public_tables(db)[offset:]
    results = []
    skipped_tables = []

    for table_name in tables:
        quoted_table = _quote_identifier(table_name)

        try:
            row_count = db.scalar(text(f"SELECT count(*) FROM {quoted_table}")) or 0
            columns = _column_metadata(db, table_name)
        except Exception as exc:
            db.rollback()
            skipped_tables.append(
                {
                    "table_name": table_name,
                    "error": str(exc),
                }
            )
            continue

        if only_non_empty and row_count == 0:
            continue

        grid_columns_count = _grid_columns_count(columns)
        column_names = {str(column["name"]).lower() for column in columns}
        looks_like_grid = "count" in column_names and _is_grid_like(columns)

        if only_grids and not looks_like_grid:
            continue

        results.append(
            {
                "table_name": table_name,
                "row_count": row_count,
                "columns_count": len(columns),
                "columns": columns,
                "looks_like_grid": looks_like_grid,
                "grid_columns_count": grid_columns_count,
                "has_cyrillic_in_name": bool(CYRILLIC_PATTERN.search(table_name)),
                "name_hints": _name_hints(table_name),
            }
        )

        if len(results) >= limit:
            break

    return {
        "limit": limit,
        "offset": offset,
        "only_non_empty": only_non_empty,
        "only_grids": only_grids,
        "returned_count": len(results),
        "tables": results,
        "debug": {
            "skipped_tables_count": len(skipped_tables),
            "skipped_tables": skipped_tables,
        },
    }


@router.get("/table-preview")
def inventory_table_preview(
    table_name: str = Query(...),
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    exclude_empty_rows: bool = Query(default=False),
    db: Session = Depends(get_legacy_db),
) -> dict[str, object]:
    if not _table_exists(db, table_name):
        raise HTTPException(status_code=404, detail="Table not found in public schema.")

    columns = _columns(db, table_name)
    if not columns:
        return {
            "table_name": table_name,
            "columns": [],
            "rows": [],
        }

    quoted_table = _quote_identifier(table_name)
    select_columns = [
        f"({_quote_identifier(column_name)})::text AS {_quote_identifier(column_name)}"
        for column_name in columns
    ]

    where_clause = ""
    if exclude_empty_rows:
        non_service_columns = [
            column_name
            for column_name in columns
            if column_name.lower() not in {"count", "id"}
        ]
        if not non_service_columns:
            return {
                "table_name": table_name,
                "columns": columns,
                "rows": [],
            }

        non_empty_checks = [
            f"btrim(({_quote_identifier(column_name)})::text) <> ''"
            for column_name in non_service_columns
        ]
        where_clause = f"WHERE {' OR '.join(non_empty_checks)}"

    try:
        rows = db.execute(
            text(
                f"""
                SELECT {", ".join(select_columns)}
                FROM {quoted_table}
                {where_clause}
                LIMIT :limit
                OFFSET :offset
                """
            ),
            {
                "limit": limit,
                "offset": offset,
            },
        ).mappings().all()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "table_name": table_name,
        "columns": columns,
        "rows": [dict(row) for row in rows],
    }


@router.get("/grid-cells")
def inventory_grid_cells(
    limit_tables: int = Query(default=20, ge=1, le=500),
    limit_cells_per_table: int = Query(default=100, ge=1, le=1000),
    exclude_columns: str = Query(default="count,id"),
    min_value_length: int = Query(default=2, ge=1, le=300),
    debug_include_raw: bool = Query(default=False),
    db: Session = Depends(get_legacy_db),
) -> dict[str, object]:
    results = []
    skipped_tables = []
    skipped_columns = []
    errors = []
    scanned_tables = 0
    scanned_cells = 0
    non_null_cells = 0
    non_empty_after_python_filter = 0
    excluded_columns = _excluded_columns(exclude_columns)

    for table_name in _public_tables(db):
        if scanned_tables >= limit_tables:
            break

        try:
            columns = _column_metadata(db, table_name)
        except Exception as exc:
            db.rollback()
            skipped_tables.append(
                {
                    "table_name": table_name,
                    "error": str(exc),
                }
            )
            continue

        if not _is_grid_like(columns):
            continue

        scanned_tables += 1
        quoted_table = _quote_identifier(table_name)
        cells_for_table = 0
        numeric_columns = [
            str(column["name"])
            for column in columns
            if str(column["name"]).isdigit()
            and str(column["name"]).lower() not in excluded_columns
        ]

        for column_name in numeric_columns:
            if cells_for_table >= limit_cells_per_table:
                break

            quoted_column = _quote_identifier(column_name)

            try:
                rows = db.execute(
                    text(
                        f"""
                        SELECT row_index,
                               value
                        FROM (
                            SELECT
                                row_number() OVER (ORDER BY ctid) AS row_index,
                                ({quoted_column})::text AS value
                            FROM {quoted_table}
                        ) AS grid_values
                        ORDER BY row_index
                        """
                    ),
                ).mappings().all()
            except Exception as exc:
                db.rollback()
                skipped_columns.append(
                    {
                        "table_name": table_name,
                        "column_name": column_name,
                        "error": str(exc),
                    }
                )
                continue

            for row in rows:
                if cells_for_table >= limit_cells_per_table:
                    break

                scanned_cells += 1
                raw_value = row["value"]
                if raw_value is not None:
                    non_null_cells += 1
                trimmed_value = str(raw_value).strip() if raw_value is not None else ""
                is_non_empty = trimmed_value != ""

                if is_non_empty:
                    non_empty_after_python_filter += 1

                if not is_non_empty and not debug_include_raw:
                    continue

                results.append(
                    {
                        "table_name": table_name,
                        "row_index": row["row_index"],
                        "column_name": column_name,
                        "value": trimmed_value[:300] if is_non_empty else raw_value,
                    }
                )

                cells_for_table += 1

    return {
        "limit_tables": limit_tables,
        "limit_cells_per_table": limit_cells_per_table,
        "exclude_columns": sorted(excluded_columns),
        "min_value_length": min_value_length,
        "debug_include_raw": debug_include_raw,
        "returned_count": len(results),
        "cells": results,
        "debug": {
            "scanned_grid_tables": scanned_tables,
            "scanned_cells": scanned_cells,
            "non_null_cells": non_null_cells,
            "non_empty_after_python_filter": non_empty_after_python_filter,
            "skipped_tables": skipped_tables,
            "skipped_columns": skipped_columns,
            "errors": errors,
        },
    }
