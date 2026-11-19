"""Reusable tables, KPI cards, and download controls."""

import json

import pandas as pd
import streamlit as st


def show_kpis(values: dict[str, object], columns: int = 4) -> None:
    cards = st.columns(columns)
    for index, (label, value) in enumerate(values.items()):
        cards[index % columns].metric(label, value)


def show_table(frame: pd.DataFrame, title: str | None = None) -> None:
    if title:
        st.subheader(title)
    if frame.empty:
        st.info("No records match the current filters.")
    else:
        st.dataframe(frame, use_container_width=True, hide_index=True)


def download_data(label: str, data: pd.DataFrame | dict, filename: str,
                  mime: str | None = None) -> None:
    if isinstance(data, pd.DataFrame):
        payload = data.to_csv(index=False)
        mime = mime or "text/csv"
    else:
        payload = json.dumps(data, indent=2)
        mime = mime or "application/json"
    st.download_button(label, payload, file_name=filename, mime=mime)
