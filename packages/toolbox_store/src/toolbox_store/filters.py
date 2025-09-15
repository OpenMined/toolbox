from datetime import datetime, timezone
from typing import Any

from toolbox_store.models import is_valid_field_identifier

OPERATORS = {
    "eq": "=",
    "ne": "!=",
    "gt": ">",
    "gte": ">=",
    "lt": "<",
    "lte": "<=",
    "in": "IN",
    "contains": "LIKE",
    "isnull": "IS",
}


def validate_field(field: str) -> None:
    if not field or len(field) > 255:
        raise ValueError(f"Invalid field name: '{field}'. Must be 1-255 characters.")

    parts = field.split(".")
    for part in parts:
        if not is_valid_field_identifier(part):
            raise ValueError(
                f"Invalid field name: '{field}'. Supported characters: [a-zA-Z0-9_-] and '.' for JSON paths."
            )


def parse_filter_key(key: str) -> tuple[str, str]:
    """Parse 'field__op' into ('field', 'op'). Default op is 'eq'."""
    if "__" in key:
        field, op = key.rsplit("__", 1)
    else:
        field, op = key, "eq"
    return field, op


def build_sql_field(field: str, table_alias: str = "d") -> str:
    """
    Convert field name to SQL field reference.
    Handles JSON paths: 'metadata.created_at' -> json_extract(...)
    """
    if "." in field:
        parts = field.split(".", 1)
        return f"json_extract({table_alias}.{parts[0]}, '$.{parts[1]}')"
    return f"{table_alias}.{field}"


def prepare_value(value: Any, op: str) -> Any:
    """Prepare value for SQL based on operator."""
    if isinstance(value, datetime):
        # Ensure UTC and convert to ISO format for SQLite
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)
        return value.isoformat()

    if isinstance(value, bool):
        return 1 if value else 0

    if op == "contains":
        return f"%{value}%"

    return value


def build_condition(
    field: str, op: str, value: Any, param_base: str, params: dict[str, Any]
) -> str:
    """Build SQL condition for a single filter."""
    sql_field = build_sql_field(field, "d")

    if op == "isnull":
        return f"{sql_field} IS {'NULL' if value else 'NOT NULL'}"

    if value is None:
        if op == "eq":
            return f"{sql_field} IS NULL"
        elif op == "ne":
            return f"{sql_field} IS NOT NULL"
        else:
            raise ValueError(f"Cannot use {op} with NULL value")

    if op == "in":
        if not value:
            return "1=0"
        placeholders = [f":{param_base}_{i}" for i in range(len(value))]
        for i, item in enumerate(value):
            params[f"{param_base}_{i}"] = prepare_value(item, "eq")
        return f"{sql_field} IN ({','.join(placeholders)})"

    if op not in OPERATORS:
        raise ValueError(f"Unknown operator: {op}")

    params[param_base] = prepare_value(value, op)
    return f"{sql_field} {OPERATORS[op]} :{param_base}"


def build_where_clause(
    filters: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """
    Convert filter dictionary to SQL WHERE clause.

    Examples:
        {"content__contains": "hello"}
        {"metadata.created_at__gte": "2025-01-01"}
        {"active": True}
        {"tags__in": ["python", "sql"]}
        {"deleted__isnull": True}
        {"created_at__gte": datetime.now()}

    Returns:
        (where_clause, params) - SQL string and parameter dict
    """
    if not filters:
        return "", {}

    conditions = []
    params = {}

    for key, value in filters.items():
        field, op = parse_filter_key(key)
        validate_field(field)
        param_base = f"p{len(params)}"
        condition = build_condition(field, op, value, param_base, params)
        conditions.append(condition)

    return " AND ".join(conditions), params
