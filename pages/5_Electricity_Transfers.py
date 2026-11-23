import calendar
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from api_data import ApiDataError
from transfer_data import load_direction, load_transfers
from ui_feedback import fetch_progress
from transfer_plots import annual_totals, energy_donut, power_lines, COLORS
from popup_ui import in_popup, page_title

page_title('Norway–Denmark electricity transfers')
with (st.popover('Connection and year') if in_popup() else st.container()):
    left, middle, right = (st.container(), st.container(), st.container()) if in_popup() else st.columns([2,1,1])
    left.selectbox('Connection', ['NO2-DK1'], help='Physical flow between southern Norway and western Denmark.')
    current = pd.Timestamp.now(tz='Europe/Oslo').year
    years = list(range(current, 2014, -1))  # The Transparency Platform launched in 2015.
    year = int(middle.selectbox(
        'Year', years, index=1,
        help='Defaults to the previous calendar year. Older years may have gaps or no reported flows for this connection.',
    ))
    if right.button('Refresh data'):
        load_direction.clear(year, "in")
        load_direction.clear(year, "out")
try:
    with fetch_progress("ENTSO-E transfers") as update:
        df = load_transfers(year, update=update)
except (ApiDataError, ValueError) as error:
    st.error(str(error))
    st.stop()
if df.empty:
    st.info('ENTSO-E returned no physical flow observations for this year.')
    st.stop()
annual = df
totals = annual_totals(annual, year)
if not in_popup():
    st.caption('Dark solid = into Norway / import · light dashed = out of Norway / export')
energy, flow, records = st.tabs(['1 · Energy', '2 · Power flow', '3 · Records & method'])

with energy:
    table, chart = st.columns([1, 1])
    with table:
        st.dataframe(totals.rename(index={'in':'Into Norway', 'out':'Out of Norway'}), width='stretch')
        if len(totals) < 2 or (totals.coverage_pct < 99.999).any():
            st.warning('Incomplete annual coverage. Totals include reported intervals only.')
        if (totals.coverage_pct > 100.001).any():
            st.warning('Coverage exceeds 100%. Check for overlapping or duplicate intervals.')
    with chart:
        if totals.energy_mwh.sum() > 0:
            if in_popup():
                import plotly.graph_objects as go
                fig = go.Figure(go.Pie(labels=['Into Norway' if d=='in' else 'Out of Norway' for d in totals.index],
                    values=totals.energy_mwh,hole=.65,sort=False,textinfo='percent',
                    marker=dict(colors=[COLORS[d] for d in totals.index],pattern=dict(shape=['' if d=='in' else '/' for d in totals.index])),
                    insidetextfont=dict(color=['white' if d=='in' else '#083d25' for d in totals.index])))
                fig.update_layout(height=390,margin=dict(t=20,b=50,l=12,r=12),legend=dict(orientation='h',y=-.1),
                    annotations=[dict(text=f'{totals.energy_mwh.sum():,.0f}<br>MWh',showarrow=False)])
                st.plotly_chart(fig,width='stretch')
            else:
                fig = energy_donut(totals, year)
                st.pyplot(fig)
                plt.close(fig)
        else:
            st.info('No positive energy was reported for this year.')

with flow:
    summary, filters = st.columns([6,1])
    with filters.popover('Months', icon=':material/filter_alt:'):
        months = st.multiselect('Choose months', list(range(1,13)), default=[1, 2, 3],
                               help='Compare daily and seasonal flow changes. Select more months to widen the chart.',
                               format_func=lambda m:calendar.month_abbr[m])
    summary.caption('Hourly power · '+(', '.join(calendar.month_abbr[m] for m in sorted(months)) or 'No months selected'))
    if months and annual.time.dt.tz_convert('Europe/Oslo').dt.month.isin(months).any():
        # Keep this call compatible with the earlier two-argument helper.
        fig = power_lines(annual, months)
        fig.set_size_inches(12, 4.5)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
    else:
        st.info('Choose months with reported observations.')

with records:
    st.caption(f'Available: {df.time.min():%Y-%m-%d} to {df.time.max():%Y-%m-%d} UTC · ENTSO-E API')
    st.dataframe(annual.head(100), height=220, width='stretch')
    with st.expander('Source, units and method'):
        st.markdown('''
        **Source:** ENTSO-E physical flows for NO2 ↔ DK1, requested directly by Streamlit.

        Power is MW. Energy is MW × interval hours, in MWh. Transfers are not domestic production.
        Year and month selections use Europe/Oslo. Coverage compares reported hours with the full
        calendar year (8,760 hours, or 8,784 in a leap year). Missing periods are not filled with zero.

        This example covers one connection, not all Norwegian imports and exports.
        ''')
        st.link_button('ENTSO-E API reference', 'https://documenter.getpostman.com/view/7009892/2s93JtP3F6')
