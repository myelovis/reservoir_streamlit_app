"""Shared progress and chart presentation for the interactive pages."""
from contextlib import contextmanager
from html import escape

import streamlit as st


@contextmanager
def fetch_progress(label):
    """Report completed request and processing steps, including cache hits."""
    slot = st.empty()

    def update(percent, stage):
        description = escape(f"{label} · {percent}% · {stage}")
        slot.html(f"""
            <div style="color:#153f31;font-weight:700;overflow-wrap:anywhere">
                {description}
            </div>
            <div role="progressbar" aria-label="{description}"
                 aria-valuenow="{percent}" aria-valuemin="0" aria-valuemax="100"
                 style="height:8px;margin-top:6px;background:#d9eadc;border-radius:8px;overflow:hidden">
                <div style="width:{percent}%;height:100%;background:#153f31"></div>
            </div>
        """)

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
