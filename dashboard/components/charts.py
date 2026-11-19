"""Reusable Plotly charts for the Streamlit dashboard."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


COLORS = {"Emergency": "#b42318", "Normal": "#2563eb", "Fulfilled": "#2563eb", "Unmet": "#b42318"}


def bar_chart(frame: pd.DataFrame, x: str, y: str, title: str,
              x_label: str = "", y_label: str = "", color: str | None = None):
    fig = px.bar(frame, x=x, y=y, color=color, title=title,
                 color_discrete_map=COLORS, labels={x: x_label, y: y_label})
    fig.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=55, b=20))
    st.plotly_chart(fig, use_container_width=True)
    return fig


def stacked_fulfillment_chart(frame: pd.DataFrame, title: str = "Fulfilled and unmet units"):
    fig = px.bar(frame, x="category", y="units", color="status", barmode="stack",
                 title=title, color_discrete_map=COLORS,
                 labels={"category": "", "units": "Units", "status": ""})
    fig.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=55, b=20))
    st.plotly_chart(fig, use_container_width=True)
    return fig


def heatmap(frame: pd.DataFrame, title: str, x_label: str = "", y_label: str = ""):
    fig = go.Figure(go.Heatmap(
        z=frame.to_numpy(), x=list(frame.columns), y=list(frame.index),
        colorscale="Blues", colorbar_title="Units",
        hovertemplate=f"{y_label}: %{{y}}<br>{x_label}: %{{x}}<br>Units: %{{z}}<extra></extra>",
    ))
    fig.update_layout(title=title, template="plotly_white",
                      margin=dict(l=20, r=20, t=55, b=20))
    st.plotly_chart(fig, use_container_width=True)
    return fig


def comparison_chart(frame: pd.DataFrame, y: str, title: str, y_label: str):
    fig = px.bar(frame, x="model_name", y=y, title=title,
                 labels={"model_name": "Model", y: y_label},
                 color="model_name", color_discrete_sequence=["#2563eb", "#b42318", "#64748b"])
    fig.update_layout(template="plotly_white", showlegend=False,
                      margin=dict(l=20, r=20, t=55, b=20))
    st.plotly_chart(fig, use_container_width=True)
    return fig
