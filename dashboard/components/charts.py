"""Reusable Plotly charts for the Streamlit dashboard."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


COLORS = {
    "Emergency": "#E63946",
    "Normal": "#A3A3A3",
    "Fulfilled": "#FFFFFF",
    "Unmet": "#E63946",
}
MODEL_COLORS = ["#E63946", "#FFFFFF", "#A3A3A3"]


def _style(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0B0B0D",
        plot_bgcolor="#18181B",
        font=dict(color="#FFFFFF"),
        title_font=dict(color="#FFFFFF"),
        margin=dict(l=20, r=20, t=55, b=20),
        legend=dict(font=dict(color="#FFFFFF")),
    )
    fig.update_xaxes(showgrid=False, linecolor="#303036", tickfont=dict(color="#A3A3A3"))
    fig.update_yaxes(gridcolor="#303036", linecolor="#303036", tickfont=dict(color="#A3A3A3"))
    return fig


def bar_chart(frame: pd.DataFrame, x: str, y: str, title: str,
              x_label: str = "", y_label: str = "", color: str | None = None):
    fig = px.bar(frame, x=x, y=y, color=color, title=title,
                 color_discrete_map=COLORS, labels={x: x_label, y: y_label})
    _style(fig)
    st.plotly_chart(fig, use_container_width=True)
    return fig


def stacked_fulfillment_chart(frame: pd.DataFrame, title: str = "Fulfilled and unmet units"):
    fig = px.bar(frame, x="category", y="units", color="status", barmode="stack",
                 title=title, color_discrete_map=COLORS,
                 labels={"category": "", "units": "Units", "status": ""})
    _style(fig)
    st.plotly_chart(fig, use_container_width=True)
    return fig


def heatmap(frame: pd.DataFrame, title: str, x_label: str = "", y_label: str = ""):
    fig = go.Figure(go.Heatmap(
        z=frame.to_numpy(), x=list(frame.columns), y=list(frame.index),
        colorscale=[[0, "#18181B"], [0.5, "#6F1D26"], [1, "#E63946"]],
        colorbar_title="Units",
        hovertemplate=f"{y_label}: %{{y}}<br>{x_label}: %{{x}}<br>Units: %{{z}}<extra></extra>",
    ))
    fig.update_layout(title=title)
    _style(fig)
    st.plotly_chart(fig, use_container_width=True)
    return fig


def comparison_chart(frame: pd.DataFrame, y: str, title: str, y_label: str):
    fig = px.bar(frame, x="model_name", y=y, title=title,
                 labels={"model_name": "Model", y: y_label},
                 color="model_name", color_discrete_sequence=MODEL_COLORS)
    fig.update_layout(showlegend=False)
    _style(fig)
    st.plotly_chart(fig, use_container_width=True)
    return fig


def grouped_bar_chart(frame: pd.DataFrame, x: str, y: str, color: str,
                      title: str, x_label: str, y_label: str):
    fig = px.bar(frame, x=x, y=y, color=color, barmode="group", title=title,
                 color_discrete_map=COLORS,
                 labels={x: x_label, y: y_label, color: ""})
    fig.update_layout(height=330)
    _style(fig)
    st.plotly_chart(fig, use_container_width=True)
    return fig
