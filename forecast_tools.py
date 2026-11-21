"""Recursive forecasts. Future weather must be supplied or assumed."""
import warnings
from threadpoolctl import threadpool_limits
import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def check_training(y, exog=None):
    y = y.astype(float).sort_index()
    if len(y) < 24 or not np.isfinite(y.to_numpy()).all():
        raise ValueError('Use at least 24 complete weeks of training data.')
    if not y.index.to_series().diff().dropna().eq(pd.Timedelta(days=7)).all():
        raise ValueError('Training weeks have gaps or duplicates. Choose a complete time frame.')
    if exog is not None and (not exog.index.equals(y.index) or not np.isfinite(exog.to_numpy()).all()):
        raise ValueError('Training weather must match every reservoir week.')
    return y


def future_weather(history, dates, method='Recent mean'):
    if history.empty or history.isna().any().any():
        raise ValueError('Future-weather assumptions need complete training weather.')
    if method == 'Recent mean':
        return pd.DataFrame(np.tile(history.tail(4).mean().to_numpy(), (len(dates),1)), index=dates, columns=history.columns)
    by_week = history.groupby(history.index.isocalendar().week.to_numpy()).mean()
    rows = [by_week.loc[date.isocalendar().week] if date.isocalendar().week in by_week.index else history.mean() for date in dates]
    return pd.DataFrame(rows, index=dates, columns=history.columns)


def sarimax_forecast(y, steps=12, order=(1,1,0), seasonal=(0,0,0,52),
                     exog=None, future_exog=None, trend='n', confidence=.95,
                     stationary=True, invertible=True, maxiter=100):
    y = check_training(y, exog)
    if steps < 1 or not .5 < confidence < 1:
        raise ValueError('Choose a positive horizon and confidence between 0.5 and 1.')
    if any(seasonal[:3]) and len(y)<2*seasonal[3]:
        raise ValueError('Seasonal SARIMAX needs at least two full seasonal cycles.')
    if exog is not None and (future_exog is None or len(future_exog)!=steps or list(exog.columns)!=list(future_exog.columns) or not np.isfinite(future_exog.to_numpy()).all()):
        raise ValueError('Provide one complete future weather row per forecast week.')
    states = max(order[0] + seasonal[0]*seasonal[3], order[2] + seasonal[2]*seasonal[3] + 1) + order[1] + seasonal[1]*seasonal[3]
    if states > 110 or len(y) > 520:
        raise ValueError('For this shared app, use a smaller seasonal model and at most 10 years of training data.')
    with threadpool_limits(limits=1), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        try:
            fitted = SARIMAX(y, exog=exog, order=order, seasonal_order=seasonal, trend=trend,
                             enforce_stationarity=stationary, enforce_invertibility=invertible).fit(disp=False, maxiter=maxiter)
        except np.linalg.LinAlgError as error:
            raise ValueError('The model could not fit these settings. Use fewer parameters or more training weeks.') from error
    prediction = fitted.get_forecast(steps, exog=future_exog)
    intervals = prediction.conf_int(alpha=1-confidence)
    dates = pd.date_range(y.index[-1]+pd.Timedelta(days=7), periods=steps, freq='7D')
    result = pd.DataFrame({'forecast': np.asarray(prediction.predicted_mean),
                           'lower': intervals.iloc[:,0].to_numpy(), 'upper': intervals.iloc[:,1].to_numpy()}, index=dates)
    if not np.isfinite(result.to_numpy()).all():
        raise ValueError('The model returned invalid forecasts. Use a simpler model.')
    notes = list(dict.fromkeys(str(w.message) for w in caught))
    if not fitted.mle_retvals.get('converged', True):
        notes.append('The model did not converge. Try fewer parameters or more training weeks.')
    return result, notes


def ridge_forecast(y, steps=12, lags=8, alpha=1., exog=None, future_exog=None):
    y = check_training(y, exog)
    if steps < 1 or not 1 <= lags < len(y)-10 or alpha <= 0:
        raise ValueError('Use fewer lags than training weeks and a positive Ridge penalty.')
    if exog is not None and (future_exog is None or len(future_exog)!=steps or list(exog.columns)!=list(future_exog.columns) or not np.isfinite(future_exog.to_numpy()).all()):
        raise ValueError('Provide complete future weather for the selected variables.')
    features = pd.concat([y.shift(i).rename(f'lag_{i}') for i in range(1,lags+1)], axis=1)
    if exog is not None:
        features = features.join(exog)
    usable = features.notna().all(axis=1)
    model = make_pipeline(StandardScaler(), Ridge(alpha=alpha))
    model.fit(features.loc[usable].to_numpy(), y.loc[usable])
    history, predicted = y.tolist(), []
    for step in range(steps):
        row = history[-lags:][::-1]
        if exog is not None:
            row += future_exog.iloc[step].tolist()
        value = float(model.predict(np.array(row).reshape(1,-1))[0])
        if not np.isfinite(value):
            raise ValueError('The model returned an invalid forecast. Check the future inputs.')
        predicted.append(value)
        history.append(value)  # Use the prediction, not a future observation.
    dates = pd.date_range(y.index[-1]+pd.Timedelta(days=7), periods=steps, freq='7D')
    return pd.DataFrame({'forecast': predicted}, index=dates), []

