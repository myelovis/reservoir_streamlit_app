"""Consistent dataframe display, including a native-Arrow fallback."""
import pandas as pd
import streamlit as st

def display_dataframe(frame, **kwargs):
    try:
        return st.dataframe(frame, **kwargs)
    except ImportError:
        # Escaping keeps database text from becoming HTML markup.
        st.caption('Interactive table unavailable. Showing a standard table.')
        st.html(frame.to_html(index=not kwargs.get('hide_index', False), escape=True))

def reservoir_summary(month, metrics):
    """Preserve numeric-field sparklines, using Arrow-compatible float lists."""
    fields = month.reset_index()
    return pd.DataFrame([{
        'Field': metrics.get(column, column.replace('_', ' ').title()),
        'Role': 'Measure' if column in metrics else 'Metadata',
        'Latest value': str(fields[column].iloc[-1]),
        'First month': ([float(value) for value in fields[column]]
                        if pd.api.types.is_numeric_dtype(fields[column]) else []),
    } for column in fields.columns])
