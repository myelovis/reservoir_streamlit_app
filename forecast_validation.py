"""Test on unseen weeks, then fit again for the future."""
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from forecast_tools import check_training, future_weather, ridge_forecast, sarimax_forecast


def boosting_forecast(y, steps=12, lags=8, learning_rate=.03,
                      trees=100, depth=2, exog=None, future_exog=None):
    y = check_training(y, exog)
    if not 1 <= lags < len(y)-10 or steps < 1 or not 0 < learning_rate <= 1:
        raise ValueError('Use fewer lags, a positive horizon and learning rate in (0, 1].')
    dates = pd.date_range(y.index[-1]+pd.Timedelta(days=7), periods=steps, freq='7D')
    if exog is not None and (future_exog is None or not future_exog.index.equals(dates)
                            or list(exog.columns) != list(future_exog.columns)
                            or not np.isfinite(future_exog.to_numpy()).all()):
        raise ValueError('Provide complete weather for every forecast week.')
    x = pd.concat([y.shift(i).rename(f'lag_{i}') for i in range(1, lags+1)], axis=1)
    if exog is not None:
        x = x.join(exog)
    model = GradientBoostingRegressor(learning_rate=learning_rate, n_estimators=trees,
                                      max_depth=depth, random_state=42)
    model.fit(x.iloc[lags:].to_numpy(), y.iloc[lags:])
    history, values = y.tolist(), []
    for step in range(steps):
        row = history[-lags:][::-1]
        if exog is not None:
            row += future_exog.iloc[step].tolist()
        value = float(model.predict([row])[0])
        values.append(value)
        history.append(value)  # Use predictions after the last known week.
    return pd.DataFrame({'forecast': values}, index=dates), []


MODELS = {'SARIMAX': sarimax_forecast, 'Ridge regression': ridge_forecast,
          'Boosting': boosting_forecast}


def tune_boosting(y, exog=None, parameters=None, scenario='Recent mean'):
    """Try at most six settings using only the training period."""
    parameters = dict(parameters or {})
    validation = min(8, len(y)//5)
    fit, test = y.iloc[:-validation], y.iloc[-validation:]
    rows = []
    for history in sorted({min(104, len(fit)), len(fit)}):
        for rate in [.03, .1, .2]:
            train = fit.tail(history)
            if len(train) < max(24, parameters.get('lags', 8)+11):
                continue
            x = None if exog is None else exog.reindex(train.index)
            future = None if x is None else future_weather(x, test.index, scenario)
            prediction, _ = boosting_forecast(train, len(test), exog=x,
                future_exog=future, **{**parameters, 'learning_rate': rate})
            rows.append({'history_weeks': history, 'learning_rate': rate,
                         'validation_MAE': float(np.abs(test-prediction.forecast).mean())})
    if not rows:
        raise ValueError('Choose more history or fewer lags before tuning.')
    return pd.DataFrame(rows).sort_values('validation_MAE').reset_index(drop=True)


def evaluate_forecast(y, model, parameters, horizon=12, holdout=13,
                      exog=None, future_exog=None, scenario='Recent mean', tune=False):
    y = check_training(y, exog)
    if model not in MODELS or horizon < 1:
        raise ValueError('Choose a supported model and a positive forecast horizon.')
    dates = pd.date_range(y.index[-1]+pd.Timedelta(days=7), periods=horizon, freq='7D')
    if exog is not None and (future_exog is None or not future_exog.index.equals(dates)
                            or list(exog.columns) != list(future_exog.columns)
                            or not np.isfinite(future_exog.to_numpy()).all()):
        raise ValueError('Future weather must match each forecast week and property.')
    if holdout < 1 or len(y)-holdout < 24:
        raise ValueError('Keep at least 24 training weeks before the holdout.')
    train, test = y.iloc[:-holdout], y.iloc[-holdout:]
    parameters = dict(parameters)
    tuning = pd.DataFrame()
    history = len(y)
    if tune:
        if model != 'Boosting':
            raise ValueError('Automatic tuning is available for Boosting.')
        tuning = tune_boosting(train, None if exog is None else exog.reindex(train.index), parameters, scenario)
        parameters['learning_rate'] = float(tuning.iloc[0].learning_rate)
        # The final fit adds the holdout weeks to the chosen training history.
        train = train.tail(int(tuning.iloc[0].history_weeks))
        history = len(train)+holdout
        y = y.tail(history)
        if exog is not None:
            exog = exog.reindex(y.index)
            if scenario != 'Upload CSV':
                future_exog = future_weather(exog, dates, scenario)
    x = None if exog is None else exog.reindex(train.index)
    assumed = None if x is None else future_weather(x, test.index, scenario)
    function = MODELS[model]
    predicted, notes = function(train, holdout, exog=x, future_exog=assumed, **parameters)
    future, warnings = function(y, horizon, exog=exog, future_exog=future_exog, **parameters)
    if not predicted.index.equals(test.index):
        raise ValueError('Holdout dates do not match the forecast dates.')
    error = test-predicted.forecast
    scores = pd.Series({'Holdout MAE (pp)': float(error.abs().mean()),
                        'Holdout RMSE (pp)': float(np.sqrt((error**2).mean())),
                        'Persistence MAE (pp)': float((test-train.iloc[-1]).abs().mean())})
    return dict(observed=y, holdout=predicted, future=future, scores=scores,
                notes=list(dict.fromkeys(notes+warnings)), parameters=parameters,
                history_weeks=history, tuning=tuning)

