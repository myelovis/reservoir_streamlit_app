"""Choose settings, test on held-out weeks, then forecast."""
import pandas as pd
import streamlit as st
from popup_ui import page_title, settings
from reservoir_data import choose_area
from shared_ui import choose_period, area_id, explain_errors
from weather_data import load_period
from weather_stats import PROPERTIES, weekly_weather
from forecast_tools import future_weather
from forecast_validation import DEFAULT_LEARNING_RATES, MODELS, evaluate_forecast
from plot_tools import forecast_animation


@st.cache_data(ttl=1800, max_entries=12, show_spinner=False)
def fit_forecast(y, model, parameters, horizon, holdout, exog, future, scenario, tune, learning_rates):
    return evaluate_forecast(y, model, parameters, horizon, holdout,
                             exog, future, scenario, tune, learning_rates)


page_title('Filling forecast')
series = choose_area(default_kind='EL', default_number=3)
start, end = choose_period(series)
model = st.radio('Model', list(MODELS), horizontal=True,
                 help='SARIMAX models time dependence. Ridge and Boosting predict from earlier weeks and selected weather.')
with explain_errors():
    observed = (series.loc[str(start):str(end), 'fill_ratio']*100).sort_index()
    observed.index = pd.to_datetime(observed.index, utc=True)
    observed = observed.asfreq('7D')
    if len(observed) < 37:
        raise ValueError('Choose at least 37 weeks: 24 for training and 13 for testing.')

with settings('Forecast settings'):
    with st.form('forecast_controls'):
        a, b, c = st.columns(3)
        history = a.number_input('History (weeks)', 37, min(520, len(observed)), min(208, len(observed)),
                                 help='Use up to four years by default, within the selected dates.')
        holdout = b.number_input('Holdout (weeks)', 1, min(52, int(history)-24), min(13, int(history)-24),
                                  help='Set aside recent weeks to test accuracy before forecasting.')
        horizon = c.number_input('Future (weeks)', 1, 52, 13,
                                  help='Number of weeks to predict after the last observation.')
        properties = st.multiselect('Weather inputs', list(PROPERTIES)[:2],
            format_func=lambda name: PROPERTIES[name][0], key='forecast_weather',
            help='Add weekly temperature or precipitation. Selected properties need complete ERA5 coverage.')
        tune = False
        learning_rates = DEFAULT_LEARNING_RATES
        if model == 'SARIMAX':
            a, b, c = st.columns(3)
            order = (a.number_input('p · past values', 0, 3, 1, help='How many earlier filling values the model uses.'),
                     b.number_input('d · differences', 0, 2, 1, help='How many times the series is differenced to reduce trends.'),
                     c.number_input('q · past errors', 0, 3, 0, help='How many earlier forecast errors the model uses.'))
            st.caption('p: past filling values. d: differencing steps. q: past forecast errors.')
            with st.expander('Seasonal and fit settings'):
                a, b, c, d = st.columns(4)
                seasonal = (a.number_input('P', 0, 2, 0, help='Number of past seasonal cycles used as predictors.'), b.number_input('D', 0, 1, 0, help='Apply a difference across one seasonal cycle.'),
                            c.number_input('Q', 0, 2, 0, help='Number of past seasonal forecast errors used.'), d.number_input('Season length', 2, 104, 52,
                                                                help='Weeks per seasonal cycle, used when P, D, or Q is nonzero.'))
                trend = st.selectbox('Trend', ['n', 'c', 't', 'ct'],
                                     help='n: none. c: constant. t: linear trend. ct: constant and trend.')
                confidence = st.slider('Conditional interval (%)', 80, 99, 95,
                                       help='Controls interval width under the chosen model and future weather scenario.')/100
                stationary = st.checkbox('Keep stationary AR terms', True,
                                         help='Constrains the autoregressive part to be stable.')
                invertible = st.checkbox('Keep invertible MA terms', True,
                                         help='Constrains the moving-average part to a stable representation.')
                maxiter = st.slider('Maximum fit steps', 20, 200, 100,
                                   help='Maximum number of optimizer iterations.')
            parameters = dict(order=order, seasonal=seasonal, trend=trend, confidence=confidence,
                              stationary=stationary, invertible=invertible, maxiter=maxiter)
        else:
            a, b = st.columns(2)
            parameters = dict(lags=a.number_input('Past filling weeks', 1, 104, 8,
                                 help='Number of previous filling values passed to the model.'))
            if model == 'Boosting':
                parameters['learning_rate'] = b.number_input('Learning rate', .001, 1., .03, .01, format='%.3f',
                                                             help='How much each new tree changes the prediction when automatic tuning is off.')
                with st.expander('Boosting settings'):
                    parameters['trees'] = st.slider('Trees', 25, 200, 100, 25,
                                                    help='Number of trees fitted in sequence.')
                    parameters['depth'] = st.slider('Tree depth', 1, 4, 2,
                                                    help='Higher depth lets each tree learn more complex patterns.')
                    tune = st.checkbox('Tune history and learning rate',
                                       help='Compare up to two training-history lengths with your selected rates.')
                    learning_rates = tuple(st.multiselect(
                        'Learning rates to test', [.001, .005, .01, .02, .03, .05, .1, .15, .2, .3, .5, 1.],
                        default=list(DEFAULT_LEARNING_RATES), max_selections=5,
                        format_func=lambda rate: f'{rate:g}',
                        help='Used only when tuning is enabled. Pick up to five rates for up to ten trials.',
                    ))
                    st.caption('Tuning uses an earlier validation period. The final holdout stays unseen.')
            else:
                parameters['alpha'] = b.number_input('Ridge penalty', .01, 100., 1.,
                                                     help='Higher values shrink model coefficients more strongly.')
        scenario = st.selectbox('Weather assumption', ['Recent mean', 'Training seasonal mean', 'Upload CSV'],
                                help='Use the recent average, a week-of-year average from training, or weather from your CSV.')
        upload = st.file_uploader('Optional future weather CSV: date and selected property columns', type='csv',
                                  help='Required for Upload CSV. Supply one dated row per forecast week.')
        st.caption('Open-Meteo ERA5 must cover every training week. Future weather uses the selected scenario.')
        submitted = st.form_submit_button('Run forecast', type='primary')

# Keep old results hidden when the settings change.
context = repr((area_id(series), str(start), str(end), model, history, holdout,
                horizon, parameters, properties, scenario, tune, learning_rates if tune else ()))
if upload is not None:
    import hashlib
    context += hashlib.sha256(upload.getvalue()).hexdigest()
if submitted:
    with explain_errors():
        y = observed.tail(int(history))
        exog = future = None
        if properties:
            weather, _ = load_period(
                area_id(series), y.index[0].date() - pd.Timedelta(days=6), y.index[-1].date()
            )
            exog = weekly_weather(weather).reindex(y.index)[properties]
            if exog.isna().any().any():
                raise ValueError('Weather does not cover every history week. Choose dates with complete ERA5 weeks or remove weather inputs.')
            dates = pd.date_range(y.index[-1]+pd.Timedelta(days=7), periods=horizon, freq='7D')
            if scenario == 'Upload CSV':
                if upload is None:
                    raise ValueError('Upload future weather, or choose a weather assumption.')
                future = pd.read_csv(upload)
                if not {'date', *properties}.issubset(future.columns):
                    raise ValueError('The CSV needs date and every selected weather property.')
                future.index = pd.to_datetime(future.pop('date'), utc=True)
                future = future[properties].apply(pd.to_numeric)
            else:
                future = future_weather(exog, dates, scenario)
        with st.spinner('Testing unseen weeks and fitting the future forecast…'):
            result = fit_forecast(y, model, parameters, int(horizon), int(holdout),
                                  exog, future, scenario, tune, learning_rates)
        st.session_state['forecast_result_v2'] = (context, result)

saved = st.session_state.get('forecast_result_v2')
if saved and saved[0] == context:
    result = saved[1]
    for note in result['notes']:
        st.warning(note)
    chart, values, method = st.tabs(['Forecast', 'Scores and values', 'Method'])
    with chart:
        fig = forecast_animation(result['observed'], result['future'],
            f'{area_id(series)} · {model}', result['holdout'])
        st.plotly_chart(fig, width='stretch', config={'displaylogo': False})
        a, b, c = st.columns(3)
        for column, (name, value) in zip([a, b, c], result['scores'].items()):
            column.metric(name, f'{value:.2f}')
        if result['future'].forecast.lt(0).any() or result['future'].forecast.gt(100).any():
            st.warning('Some forecasts fall outside 0–100%. Try a simpler model.')
    with values:
        table = pd.concat([result['holdout'].assign(period='Holdout'),
                           result['future'].assign(period='Future')])
        table['observed'] = result['observed'].reindex(table.index)
        st.dataframe(table, width='stretch', height=220)
        st.download_button('Download predictions', table.to_csv().encode(), 'forecast.csv', 'text/csv')
        st.write({'History weeks': result['history_weeks'], **result['parameters']})
        if not result['tuning'].empty:
            st.caption(f"Selected learning rate: {result['parameters']['learning_rate']:g} · lowest validation MAE")
            st.dataframe(result['tuning'], hide_index=True, width='stretch')
    with method:
        st.write('Holdout predictions use only earlier filling values. We then fit again using all selected history to forecast the future. Each forecast uses its own earlier predictions.')
        st.write('Persistence repeats the last value before the holdout. Errors are in percentage points. Lower is better.')
        st.write('Weather in the holdout is also assumed from earlier weeks; actual holdout weather is not used. SARIMAX intervals assume the weather scenario is correct. Ridge and Boosting show point forecasts.')
        st.caption('For uploaded future weather, holdout testing uses the training seasonal mean.')
        st.write('Learning rate controls each boosting step. It is not a SARIMAX parameter. Smaller values often need more trees. History controls how many recent weeks are used.')
else:
    st.caption('Choose settings, then run the forecast. Hover, zoom, click legend labels or play the future weeks.')
