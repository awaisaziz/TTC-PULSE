from __future__ import annotations

import altair as alt
import pandas as pd


def bar_chart(df: pd.DataFrame, x: str, y: str, color: str | None = None, title: str = "") -> alt.Chart | None:
    if df.empty:
        return None
    encode = {
        "x": alt.X(x, title=x),
        "y": alt.Y(y, title=y),
        "tooltip": list(df.columns),
    }
    if color:
        encode["color"] = alt.Color(color)
    return alt.Chart(df).mark_bar().encode(**encode).properties(title=title)


def line_chart(df: pd.DataFrame, x: str, y: str, color: str | None = None, title: str = "") -> alt.Chart | None:
    if df.empty:
        return None
    encode = {
        "x": alt.X(x, title=x),
        "y": alt.Y(y, title=y),
        "tooltip": list(df.columns),
    }
    if color:
        encode["color"] = alt.Color(color)
    return alt.Chart(df).mark_line(point=True).encode(**encode).properties(title=title)


def heatmap(df: pd.DataFrame, x: str, y: str, color: str, title: str = "") -> alt.Chart | None:
    if df.empty:
        return None
    return (
        alt.Chart(df)
        .mark_rect()
        .encode(
            x=alt.X(x, title=x),
            y=alt.Y(y, title=y),
            color=alt.Color(color, title=color),
            tooltip=list(df.columns),
        )
        .properties(title=title)
    )


def stacked_bar(df: pd.DataFrame, x: str, y: str, stack_color: str, title: str = "") -> alt.Chart | None:
    if df.empty:
        return None
    return (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X(x, title=x),
            y=alt.Y(y, title=y),
            color=alt.Color(stack_color, title=stack_color),
            tooltip=list(df.columns),
        )
        .properties(title=title)
    )
