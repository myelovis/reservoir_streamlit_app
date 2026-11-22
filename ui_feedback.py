"""Shared progress and chart presentation for the interactive pages."""
from contextlib import contextmanager

import streamlit as st


@contextmanager
def fetch_progress(label):
    """Report completed request and processing steps, including cache hits."""
    slot = st.empty()

    def update(percent, stage):
        slot.progress(percent, text=f"{label} · {percent}% · {stage}")

    update(0, "Starting")
    try:
        yield update
    except BaseException:
        slot.empty()
        raise
    else:
        update(100, "Ready")


def show_chart(figure):
    figure.update_traces(hoverinfo="skip", hovertemplate=None)
    figure.update_layout(
        hovermode=False,
        paper_bgcolor="#f7faf7",
        plot_bgcolor="#f7faf7",
        font_color="#153f31",
    )
    figure.update_xaxes(gridcolor="#dce9df", zerolinecolor="#b4cbb9")
    figure.update_yaxes(gridcolor="#dce9df", zerolinecolor="#b4cbb9")
    st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})
