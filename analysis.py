"""Pure analysis functions shared by Streamlit and Jupyter. No network calls."""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.fft import dct, idct
from scipy.signal import spectrogram
from scipy.stats import median_abs_deviation
from sklearn.neighbors import LocalOutlierFactor
from statsmodels.tsa.seasonal import STL


def regular_series(series, interval, minimum=3):
    y = series.copy().astype(float)
    y.index = pd.to_datetime(y.index, utc=True)
    y = y.sort_index()
    if len(y) < minimum or not np.isfinite(y.to_numpy()).all():
        raise ValueError(f"Provide at least {minimum} finite observations, without missing values.")
    if not (y.index.to_series().diff().dropna() == pd.Timedelta(interval)).all():
        raise ValueError(f"Observations must be consecutive and spaced {interval} apart. Resolve duplicates or gaps first.")
    return y


def stl_analysis(filling, seasonal=13, trend=89, robust=True, label="Selected region"):
    y = regular_series(filling, "7D", minimum=104)
    if not isinstance(seasonal, int) or seasonal < 7 or seasonal % 2 == 0:
        raise ValueError("Seasonal smoother must be an odd integer of at least 7.")
    if not isinstance(trend, int) or trend <= 52 or trend % 2 == 0:
        raise ValueError("Trend smoother must be an odd integer greater than 52.")
    result = STL(y, period=52, seasonal=seasonal, trend=trend, robust=robust).fit()
    components = pd.DataFrame({"observed": y, "trend": result.trend,
                               "seasonal": result.seasonal, "residual": result.resid})
    fig, axes = plt.subplots(4, 1, figsize=(11, 8), sharex=True, constrained_layout=True)
    colors = ["#2563eb", "#d97706", "#0d9488", "#be123c"]
    for ax, name, color in zip(axes, components, colors):
        ax.plot(y.index, components[name], color=color, linewidth=1.1)
        ax.set_ylabel(name.title() + (" (%)" if name in ("observed", "trend") else " (pp)"))
        ax.grid(alpha=.15)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].plot(y.index, result.trend, color=colors[1], label="Trend", linewidth=1.5)
    axes[0].legend(loc="upper right")
    axes[-1].set_xlabel("Observation date")
    fig.suptitle(f"{label} · reservoir filling decomposition")
    return fig, components


def spectrogram_analysis(filling, window_length=104, window_overlap=78, label="Selected region"):
    if not isinstance(window_length, int) or not isinstance(window_overlap, int):
        raise ValueError("Window and overlap must be integer numbers of weeks.")
    if window_length < 4 or not 0 <= window_overlap < window_length:
        raise ValueError("Use a window of at least 4 weeks and overlap smaller than the window.")
    y = regular_series(filling, "7D", minimum=2 * window_length - window_overlap)
    frequency, times, power = spectrogram(y.to_numpy(), fs=52, window="hann",
        nperseg=window_length, noverlap=window_overlap, detrend="linear", scaling="density")
    dates = y.index[0] + pd.to_timedelta(times * 52 * 7, unit="D")
    relative = power[1:] / max(float(power[1:].max()), np.finfo(float).tiny)
    decibels = 10 * np.log10(np.maximum(relative, 1e-12))
    fig, ax = plt.subplots(figsize=(11, 4.8), constrained_layout=True)
    image = ax.pcolormesh(dates, frequency[1:], decibels, shading="auto", cmap="magma", vmin=-60, vmax=0)
    ax.axhline(1, color="cyan", linestyle="--", linewidth=1, label="Annual cycle")
    ax.set(title=f"{label} · reservoir filling spectrogram", xlabel="Window centre",
           ylabel="Frequency (cycles/year)", ylim=(0, 6))
    ax.legend(loc="upper right")
    fig.colorbar(image, ax=ax, label="Power relative to maximum (dB)")
    table = pd.DataFrame(power[1:].T, index=dates, columns=frequency[1:])
    table.index.name = "window_centre"
    table.columns.name = "cycles_per_year"
    return fig, table


def precipitation_spc(weather, cutoff_days=30, n_sigma=3, label="Selected region"):
    y = regular_series(weather["precipitation"], "1h")
    if not np.isfinite(cutoff_days) or cutoff_days <= 1 / 12 or not np.isfinite(n_sigma) or n_sigma <= 0:
        raise ValueError("Use cutoff_days > 1/12 and a positive sigma multiplier.")
    coefficients = dct(y.to_numpy(), norm="ortho")
    coefficients[np.arange(len(y)) / (2 * len(y)) < 1 / (24 * cutoff_days)] = 0
    residual = idct(coefficients, norm="ortho")
    baseline = y.to_numpy() - residual
    centre = np.median(residual)
    sigma = float(median_abs_deviation(residual, scale="normal"))
    if sigma <= np.finfo(float).eps:
        raise ValueError("Residual variability is too small to estimate meaningful SPC limits.")
    lower, upper = baseline + centre - n_sigma * sigma, baseline + centre + n_sigma * sigma
    flagged = (y.to_numpy() < lower) | (y.to_numpy() > upper)
    results = pd.DataFrame({"precipitation": y, "lower_limit": lower, "upper_limit": upper, "outlier": flagged})
    fig, ax = plt.subplots(figsize=(11, 4), constrained_layout=True)
    ax.plot(y.index, y, color="#2563eb", linewidth=.7, label="Regional precipitation")
    ax.plot(y.index, lower, "--", color="#d97706", label="SPC limits")
    ax.plot(y.index, upper, "--", color="#d97706")
    ax.scatter(y.index[flagged], y.iloc[flagged], color="crimson", s=12, label="Outliers", zorder=3)
    ax.set(title=f"{label} · precipitation DCT/SPC", xlabel="Time (UTC)", ylabel="Precipitation (mm/hour)")
    ax.legend()
    summary = {"hours": len(y), "outlier_hours": int(flagged.sum()),
               "outlier_percent": float(100 * flagged.mean()), "robust_sigma": sigma}
    return fig, results, summary


def temperature_lof(weather, proportion=.01, neighbours=20, label="Selected region"):
    y = regular_series(weather["temperature_2m"], "1h")
    if not 0 < proportion <= .5 or not isinstance(neighbours, int) or not 1 <= neighbours < len(y):
        raise ValueError("Use proportion in (0, 0.5] and integer neighbours between 1 and number of hours − 1.")
    model = LocalOutlierFactor(n_neighbors=neighbours, contamination=proportion)
    flagged = model.fit_predict(y.to_numpy().reshape(-1, 1)) == -1
    results = pd.DataFrame({"temperature_2m": y, "lof_score": -model.negative_outlier_factor_, "anomaly": flagged})
    fig, ax = plt.subplots(figsize=(11, 4), constrained_layout=True)
    ax.plot(y.index, y, color="#2563eb", linewidth=.7, label="Regional temperature")
    ax.scatter(y.index[flagged], y.iloc[flagged], color="crimson", s=15, label="LOF anomalies", zorder=3)
    ax.set(title=f"{label} · temperature LOF", xlabel="Time (UTC)", ylabel="Temperature (°C)")
    ax.legend()
    return fig, results, {"hours": len(y), "anomaly_hours": int(flagged.sum()), "anomaly_percent": float(100 * flagged.mean())}
