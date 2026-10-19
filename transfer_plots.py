"""Notebook units, direction colours and local calendar interpretation."""
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

COLORS = {"in": "#005A9C", "out": "#E05A47"}
LABELS = {"in": "Into Norway (Import)", "out": "Out of Norway (Export)"}

def clip_intervals(df, start, end):
    """Keep only the measured part inside the half-open selection [start, end)."""
    start, end = pd.Timestamp(start).tz_convert("UTC"), pd.Timestamp(end).tz_convert("UTC")
    finish = df.time + pd.to_timedelta(df.hours, unit="h")
    keep = (df.time < end) & (finish > start)
    selected = df.loc[keep].copy()
    selected["time"] = selected.time.clip(lower=start)
    finish = finish.loc[keep].clip(upper=end)
    selected["hours"] = (finish - selected.time).dt.total_seconds()/3600
    selected["energy_mwh"] = selected.power_mw * selected.hours
    selected["year"] = selected.time.dt.tz_convert("Europe/Oslo").dt.year
    return selected

def annual_totals(annual, year):
    annual = clip_intervals(annual,
        pd.Timestamp(year=year, month=1, day=1, tz="Europe/Oslo"),
        pd.Timestamp(year=year+1, month=1, day=1, tz="Europe/Oslo"))
    totals = annual.groupby("direction").agg(
        energy_mwh=("energy_mwh", "sum"), reported_hours=("hours", "sum"))
    expected_hours = (pd.Timestamp(year=year+1, month=1, day=1) -
                      pd.Timestamp(year=year, month=1, day=1)).total_seconds()/3600
    totals["coverage_pct"] = totals.reported_hours / expected_hours * 100
    return totals

def energy_donut(totals, year):
    fig, ax = plt.subplots(figsize=(7, 6), facecolor="#FCFCFC")
    _, _, percentages = ax.pie(totals.energy_mwh,
           labels=["Into Norway" if d == "in" else "Out of Norway" for d in totals.index],
           colors=[COLORS[d] for d in totals.index], autopct="%1.1f%%",
           startangle=140, pctdistance=0.75,
           wedgeprops={"width": 0.45, "edgecolor": "white", "linewidth": 2},
           textprops={"fontsize": 10})
    for text in percentages:
        text.set_color("white")
        text.set_weight("bold")
    ax.text(0, 0, f"Total energy\n{totals.energy_mwh.sum():,.0f}\nMWh",
            ha="center", va="center", fontsize=11, fontweight="bold")
    ax.set_title(f"NO2–DK1: reported transfer energy ({year})", pad=20)
    fig.tight_layout()
    return fig

def power_lines(annual, months):
    year = int(annual.year.iloc[0])
    frames = []
    for month in sorted(set(months)):
        start = pd.Timestamp(year=year, month=month, day=1, tz="Europe/Oslo")
        frames.append(clip_intervals(annual, start, start + pd.DateOffset(months=1)))
    selected = pd.concat(frames).sort_values("time") if frames else annual.iloc[:0]
    fig, ax = plt.subplots(figsize=(11, 4.5), facecolor="#FCFCFC")
    for direction, group in selected.groupby("direction"):
        # Vectorized interval segments retain the measured duration and gaps.
        starts = mdates.date2num(group.time.to_numpy())
        ends = starts + group.hours.to_numpy()/24
        gaps = np.full(len(group), np.nan)
        x = np.column_stack([starts, ends, gaps]).ravel()
        y = np.column_stack([group.power_mw, group.power_mw, gaps]).ravel()
        ax.plot(x, y, color=COLORS[direction], linewidth=1.2,
                label=f"NO2–DK1: {LABELS[direction]}")
    locator = mdates.AutoDateLocator(tz=ZoneInfo("Europe/Oslo"))
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(
        locator, tz=ZoneInfo("Europe/Oslo")))
    ax.set(title="NO2–DK1: reported power flows",
           xlabel="Time (Europe/Oslo)", ylabel="Power (MW)")
    if not selected.empty:
        ax.legend(fontsize=9)
    ax.grid(linestyle="--", alpha=0.3)
    fig.tight_layout()
    return fig
