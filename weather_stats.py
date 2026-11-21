"""Simple weather analysis. No database calls here."""
import numpy as np
import pandas as pd
from scipy.fft import dct, idct
from scipy.stats import median_abs_deviation
from sklearn.neighbors import LocalOutlierFactor

PROPERTIES = {'temperature_2m': ('Temperature', '°C', 'mean'),
              'precipitation': ('Precipitation', 'mm', 'sum'),
              'snowfall': ('Snowfall', 'cm', 'sum'),
              'et0_fao_evapotranspiration': ('Evapotranspiration', 'mm', 'sum')}


def hourly_series(series):
    y = series.astype(float).sort_index()
    y.index = pd.to_datetime(y.index, utc=True)
    if len(y) < 3 or not np.isfinite(y.to_numpy()).all():
        raise ValueError('Use at least three hours with no missing values.')
    if not y.index.to_series().diff().dropna().eq(pd.Timedelta(hours=1)).all():
        raise ValueError('Weather must have one row for every hour, with no duplicates.')
    return y


def spc(series, cutoff_days=30, sigma_count=3):
    y = hourly_series(series)
    if cutoff_days <= 1/12 or sigma_count <= 0:
        raise ValueError('Choose a positive cutoff and sigma count.')
    coefficients = dct(y.to_numpy(), norm='ortho')
    frequency = np.arange(len(y)) / (2 * len(y))
    coefficients[frequency < 1 / (24 * cutoff_days)] = 0
    residual = idct(coefficients, norm='ortho')
    scale = float(median_abs_deviation(residual, scale='normal'))
    if scale <= np.finfo(float).eps:
        raise ValueError('There is too little variation for useful SPC limits.')
    middle = y.to_numpy() - residual + np.median(residual)
    result = pd.DataFrame({'value': y, 'lower': middle-sigma_count*scale,
                           'upper': middle+sigma_count*scale})
    result['flag'] = (result.value < result.lower) | (result.value > result.upper)
    return result


def lof(series, proportion=.01, neighbours=20):
    y = hourly_series(series)
    if not 0 < proportion <= .5 or not 1 < neighbours < len(y):
        raise ValueError('Use a proportion from 0 to 0.5 and fewer neighbours than hours.')
    model = LocalOutlierFactor(n_neighbors=int(neighbours), contamination=proportion)
    result = pd.DataFrame({'value': y})
    result['flag'] = model.fit_predict(y.to_numpy().reshape(-1, 1)) == -1
    result['score'] = -model.negative_outlier_factor_
    return result


def weekly_weather(weather):
    result = {}
    for column in weather:
        if column not in PROPERTIES:
            continue
        values = hourly_series(weather[column])
        groups = values.resample('W-SUN')
        weekly = groups.agg(PROPERTIES[column][2])
        result[column] = weekly.where(groups.count().eq(168))
    return pd.DataFrame(result)


def combine_weekly(reservoir, weather):
    weekly = weekly_weather(weather)
    filling = reservoir.copy()
    filling.index = pd.to_datetime(filling.index, utc=True).normalize()
    filling = filling.sort_index().asfreq('7D')
    result = pd.DataFrame({'filling': filling * 100})
    result['filling_change'] = result.filling.diff()
    return result.join(weekly)


def sliding_correlation(frame, property_name, target='filling_change', lag=1, window=12):
    if lag < 0 or window < 4:
        raise ValueError('Use a non-negative lag and a window of at least four weeks.')
    # A positive lag asks if earlier weather is linked to later filling.
    values = pd.DataFrame({'weather': frame[property_name].shift(int(lag)),
                           'reservoir': frame[target]})
    values['correlation'] = values.weather.rolling(int(window), min_periods=int(window)).corr(values.reservoir)
    return values

