"""Small layout helpers shared by pages and Home popups."""
from contextlib import contextmanager
from contextvars import ContextVar
import streamlit as st

_panel = ContextVar('popup_controls', default=None)
_shared = ContextVar('home_selection_only', default=False)


def uses_home_selection():
    return _shared.get()


def in_popup():
    return _panel.get() is not None


def controls_panel():
    return _panel.get() if in_popup() else st.sidebar


@contextmanager
def popup_layout(panel, shared=False):
    token = _panel.set(panel)
    selection = _shared.set(shared)
    try:
        yield
    finally:
        _shared.reset(selection)
        _panel.reset(token)


def page_title(title):
    if not in_popup():
        st.title(title)


def settings(label):
    return st.popover(label) if in_popup() else st.container()
