from __future__ import annotations


def as_int(value: float | int | None) -> str:
    if value is None:
        return "0"
    try:
        return f"{int(round(float(value))):,}"
    except Exception:
        return "0"


def as_pct(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "0.00%"
    try:
        return f"{float(value) * 100:.{digits}f}%"
    except Exception:
        return "0.00%"


def as_float(value: float | int | None, digits: int = 2) -> str:
    if value is None:
        return "0.00"
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return "0.00"
