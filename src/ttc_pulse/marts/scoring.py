from __future__ import annotations

W1 = 0.35
W2 = 0.30
W3 = 0.20
W4 = 0.15


def z_expr(column_name: str) -> str:
    return (
        f"coalesce((({column_name} - avg({column_name}) over()) / "
        f"nullif(stddev_pop({column_name}) over(), 0)), 0.0)"
    )


def composite_score_expr(
    freq_col: str = "freq_events",
    sev_col: str = "sev90_delay",
    reg_col: str = "reg90_gap",
    cause_col: str = "cause_mix",
) -> str:
    zf = z_expr(freq_col)
    zs = z_expr(sev_col)
    zr = z_expr(reg_col)
    return (
        f"({W1} * {zf}) + ({W2} * {zs}) + ({W3} * {zr}) + "
        f"({W4} * coalesce({cause_col}, 0.0))"
    )
