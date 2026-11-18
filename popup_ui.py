"""Small layout helpers shared by pages and Home popups."""
from contextlib import contextmanager
from contextvars import ContextVar
import streamlit as st

_panel = ContextVar('popup_controls', default=None)


def in_popup():
    return _panel.get() is not None


def controls_panel():
    return _panel.get() if in_popup() else st.sidebar


@contextmanager
def popup_layout(panel):
    token = _panel.set(panel)
    try:
        yield
    finally:
        _panel.reset(token)


def page_title(title):
    if not in_popup():
        st.title(title)


def settings(label):
    return st.popover(label) if in_popup() else st.container()
