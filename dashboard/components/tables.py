"""Reusable tables, KPI cards, and download controls."""

import json

import pandas as pd
import streamlit as st


def show_kpis(values: dict[str, object], columns: int = 4,
              highlighted: set[str] | None = None) -> None:
    highlighted = highlighted or set()
    cards = st.columns(columns)
    for index, (label, value) in enumerate(values.items()):
        with cards[index % columns].container(border=True):
            if label in highlighted:
                st.markdown(
                    f'<div class="kpi-highlight-label">{label}</div>',
                    unsafe_allow_html=True,
                )
                st.metric(label=label, value=value, label_visibility="collapsed")
            else:
                st.metric(label, value)


def show_workflow(steps: list[str]) -> None:
    """Render an informational workflow without implying execution state."""
    columns = st.columns(len(steps) * 2 - 1)
    for index, step in enumerate(steps):
        with columns[index * 2].container(border=True):
            st.markdown(f"**{index + 1:02d}**")
            st.markdown(step)
        if index < len(steps) - 1:
            columns[index * 2 + 1].markdown(
                '<div class="workflow-arrow" aria-hidden="true">→</div>',
                unsafe_allow_html=True,
            )


def show_status(status: str, verification: str | None = None) -> None:
    """Show solver and verification state with text, not color alone."""
    label = f"Solver status: {status}"
    if verification is not None:
        label += f" | Verification: {verification}"
    if status == "OPTIMAL" and verification in (None, "PASS"):
        st.success(label)
    elif status in {"INFEASIBLE", "UNBOUNDED", "INVALID_DATA"} or verification == "FAIL":
        st.error(label)
    else:
        st.warning(label)


def show_table(frame: pd.DataFrame, title: str | None = None) -> None:
    if title:
        st.subheader(title)
    if frame.empty:
        st.info("No records match the current filters.")
    else:
        st.dataframe(frame, width="stretch", hide_index=True)


def download_data(label: str, data: pd.DataFrame | dict, filename: str,
                  mime: str | None = None) -> None:
    if isinstance(data, pd.DataFrame):
        payload = data.to_csv(index=False)
        mime = mime or "text/csv"
    else:
        payload = json.dumps(data, indent=2)
        mime = mime or "application/json"
    st.download_button(label, payload, file_name=filename, mime=mime)
