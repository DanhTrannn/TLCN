"""Load packaged SQL resources; callers quote values and identifiers explicitly."""

import re
from pathlib import Path, PurePosixPath

_ROOT = Path(__file__).with_name("sql_templates")
_PARAMETER = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")
_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def identifier(value: str) -> str:
    parts = value.split(".")
    if not all(_IDENTIFIER.fullmatch(part) for part in parts):
        raise ValueError(f"Invalid SQL identifier: {value!r}")
    return ".".join(f"`{part}`" for part in parts)


def literal(value: object) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def sql_type(value: str) -> str:
    """Accept Spark's simpleString type representation, never arbitrary statements."""
    if not re.fullmatch(r"[A-Za-z0-9_<>,(): ]+", value):
        raise ValueError(f"Invalid SQL data type: {value!r}")
    return value


def load_sql(name: str) -> str:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name or path.suffix != ".sql":
        raise ValueError(f"Invalid SQL resource path: {name!r}")
    return _ROOT.joinpath(*path.parts).read_text(encoding="utf-8")


def render_sql(name: str, **parameters: str) -> str:
    """Substitute explicit SQL fragments, rejecting missing and unused parameters.

    Use identifier() for catalog/table/column names and literal() for values.
    Fragments such as predicates must be composed from other SQL resources.
    Never pass unquoted user/config input as a fragment.
    """
    template = load_sql(name)
    expected = set(_PARAMETER.findall(template))
    if expected != parameters.keys():
        raise ValueError(
            f"SQL parameters for {name}: missing={expected - parameters.keys()}, unused={parameters.keys() - expected}"
        )
    return _PARAMETER.sub(lambda match: str(parameters[match.group(1)]), template)
