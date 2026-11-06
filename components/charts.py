from __future__ import annotations

from typing import Optional, Sequence

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config.constants import CHART_COLORS, PRIMARY_COLOR


def style_figure(fig: go.Figure, height: int = 360, show_legend: bool = False) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=12, r=12, t=44, b=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Helvetica, Arial, sans-serif", size=11, color=PRIMARY_COLOR),
        title_font=dict(size=13, color=PRIMARY_COLOR),
        showlegend=show_legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hoverlabel=dict(bgcolor="#FFFFFF", font_size=11, font_family="Helvetica"),
    )
    fig.update_xaxes(showgrid=False, linecolor="#E2E8F0", tickfont=dict(size=10))
    fig.update_yaxes(showgrid=True, gridcolor="#EDF2F7", zeroline=False, tickfont=dict(size=10))
    return fig


def empty_figure(message: str = "Tidak ada data untuk filter yang dipilih.", height: int = 320) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(size=12, color="#64748B"),
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return style_figure(fig, height=height)


def bar_chart(
    frame: pd.DataFrame,
    x: str,
    y: str,
    title: Optional[str] = None,
    color: Optional[str] = None,
    orientation: str = "v",
    text: Optional[str] = None,
    height: int = 360,
    color_sequence: Optional[Sequence[str]] = None,
) -> go.Figure:
    if frame.empty:
        return empty_figure(height=height)
    fig = px.bar(
        frame,
        x=x if orientation == "v" else y,
        y=y if orientation == "v" else x,
        orientation=orientation,
        title=title,
        color=color,
        text=text,
        color_discrete_sequence=list(color_sequence or CHART_COLORS),
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    return style_figure(fig, height=height, show_legend=bool(color))


def donut_chart(
    frame: pd.DataFrame,
    names: str,
    values: str,
    title: Optional[str] = None,
    height: int = 340,
    center_label: str = "prestasi",
    value_label: str = "prestasi",
) -> go.Figure:
    if frame.empty:
        return empty_figure(height=height)
    fig = px.pie(
        frame,
        names=names,
        values=values,
        title=title,
        hole=0.58,
        color_discrete_sequence=CHART_COLORS,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent",
        hovertemplate=f"%{{label}}<br>%{{value}} {value_label}<extra></extra>",
    )
    fig.update_layout(
        annotations=[
            dict(
                text=f"<b>{int(frame[values].sum()):,}</b><br><span style='font-size:10px'>{center_label}</span>".replace(",", "."),
                x=0.5,
                y=0.5,
                font=dict(size=16, color=PRIMARY_COLOR),
                showarrow=False,
            )
        ]
    )
    return style_figure(fig, height=height, show_legend=True)


def line_chart(
    frame: pd.DataFrame,
    x: str,
    y: str,
    title: Optional[str] = None,
    height: int = 340,
    color: Optional[str] = None,
    text: Optional[str] = None,
) -> go.Figure:
    if frame.empty:
        return empty_figure(height=height)
    fig = px.line(
        frame,
        x=x,
        y=y,
        title=title,
        markers=True,
        color=color,
        text=text,
        color_discrete_sequence=[CHART_COLORS[2]],
    )
    fig.update_traces(line=dict(width=3), marker=dict(size=7), textposition="top center")
    return style_figure(fig, height=height, show_legend=bool(color))


def multi_line_chart(
    frame: pd.DataFrame,
    x: str,
    y: str,
    color: str,
    title: Optional[str] = None,
    height: int = 380,
) -> go.Figure:
    if frame.empty:
        return empty_figure(height=height)
    fig = px.line(
        frame,
        x=x,
        y=y,
        color=color,
        title=title,
        markers=True,
        color_discrete_sequence=CHART_COLORS,
    )
    fig.update_traces(line=dict(width=2.5), marker=dict(size=6))
    return style_figure(fig, height=height, show_legend=True)


def grouped_bar_chart(
    frame: pd.DataFrame,
    x: str,
    y: str,
    color: str,
    title: Optional[str] = None,
    height: int = 380,
    barmode: str = "group",
    text: Optional[str] = None,
) -> go.Figure:
    if frame.empty:
        return empty_figure(height=height)
    fig = px.bar(
        frame,
        x=x,
        y=y,
        color=color,
        title=title,
        barmode=barmode,
        text=text,
        color_discrete_sequence=CHART_COLORS,
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    return style_figure(fig, height=height, show_legend=True)


def heatmap_chart(
    frame: pd.DataFrame,
    x: str,
    y: str,
    values: str,
    title: Optional[str] = None,
    height: int = 380,
    color_scale: Optional[Sequence[str]] = None,
) -> go.Figure:
    if frame.empty:
        return empty_figure(height=height)
    pivot = frame.pivot_table(index=y, columns=x, values=values, aggfunc="sum", fill_value=0)
    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns.tolist(),
            y=pivot.index.tolist(),
            colorscale=color_scale or ["#EAF2FF", "#2F80ED", "#0B1F3A"],
            hovertemplate=f"%{{y}}<br>%{{x}}: %{{z}} {values}<extra></extra>",
            text=pivot.values,
            texttemplate="%{text}",
            textfont=dict(size=10),
        )
    )
    fig.update_layout(title=title)
    return style_figure(fig, height=height)


def ranking_bar_chart(
    frame: pd.DataFrame,
    label: str,
    value: str,
    title: Optional[str] = None,
    top_n: int = 10,
    height: int = 390,
    color: str = CHART_COLORS[2],
) -> go.Figure:
    if frame.empty:
        return empty_figure(height=height)
    data = frame.head(top_n).copy()
    data = data.sort_values(value, ascending=True)
    fig = px.bar(
        data,
        x=value,
        y=label,
        orientation="h",
        title=title,
        text=value,
        color_discrete_sequence=[color],
    )
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(yaxis_title=None, xaxis_title=None)
    return style_figure(fig, height=height)
