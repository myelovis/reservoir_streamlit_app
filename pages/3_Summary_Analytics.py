# Final Code Cell: Plotting all columns together handling different scales

import matplotlib.pyplot as plt

# Filter out non-numeric and date-related columns
numeric_cols = [
    "fill_ratio",
    "capacity_twh",
    "storage_twh",
    "fill_ratio_previous_week",
    "fill_ratio_change",
]

# Option 1: Dual Y-Axis Plot (Grouping by physical scale)
# Aggregate data across all price areas by date to get national total/averages
df_national = (
    df.groupby("date_id")
    .agg(
        {
            "capacity_twh": "sum",
            "storage_twh": "sum",
            "fill_ratio": "mean",
        }
    )
    .reset_index()
)

fig, ax1 = plt.subplots(figsize=(12, 6))

# Left Y-Axis: Energy quantities in Terawatt-hours (TWh)
color_cap = "#2b5c8f"
color_stor = "#4682b4"
ax1.set_xlabel("Date", fontsize=11, fontweight="bold")
ax1.set_ylabel("Energy Potential (TWh)", color=color_cap, fontsize=11, fontweight="bold")
line1 = ax1.plot(
    df_national["date_id"],
    df_national["capacity_twh"],
    color=color_cap,
    linestyle="--",
    linewidth=1.5,
    label="Capacity (TWh)",
)
line2 = ax1.plot(
    df_national["date_id"],
    df_national["storage_twh"],
    color=color_stor,
    linewidth=2,
    label="Storage (TWh)",
)
ax1.tick_params(axis="y", labelcolor=color_cap)

# Right Y-Axis: Fill ratio ratio (0.0 to 1.0 or 0% to 100%)
ax2 = ax1.twinx()
color_ratio = "#d95f02"
ax2.set_ylabel("Fill Ratio (0–1)", color=color_ratio, fontsize=11, fontweight="bold")
line3 = ax2.plot(
    df_national["date_id"],
    df_national["fill_ratio"],
    color=color_ratio,
    linewidth=1.5,
    alpha=0.8,
    label="Mean Fill Ratio",
)
ax2.tick_params(axis="y", labelcolor=color_ratio)
ax2.set_ylim(0, 1.05)

# Combine legends from both axes
lines = line1 + line2 + line3
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc="upper left", frameon=True)

plt.title("Norwegian Reservoir Overview: Capacity, Storage, and Fill Ratio Over Time", fontsize=13, fontweight="bold", pad=12)
plt.grid(True, linestyle=":", alpha=0.6)
plt.tight_layout()
plt.show()

# Option 2: Min-Max Normalized Comparison (Plotting all numeric metrics together on 0-1 scale)
df_normalized = df_national.copy()
for col in ["capacity_twh", "storage_twh", "fill_ratio"]:
    min_val = df_normalized[col].min()
    max_val = df_normalized[col].max()
    df_normalized[col] = (df_normalized[col] - min_val) / (max_val - min_val)

plt.figure(figsize=(12, 5))
plt.plot(df_normalized["date_id"], df_normalized["capacity_twh"], label="Capacity (Normalized)", linestyle="--")
plt.plot(df_normalized["date_id"], df_normalized["storage_twh"], label="Storage (Normalized)")
plt.plot(df_normalized["date_id"], df_normalized["fill_ratio"], label="Fill Ratio (Normalized)", alpha=0.7)

plt.title("Normalized Comparison of All Reservoir Indicators (0-1 Scale)", fontsize=13, fontweight="bold")
plt.xlabel("Date", fontsize=11)
plt.ylabel("Normalized Scale (0 to 1)", fontsize=11)
plt.legend(loc="upper left")
plt.grid(True, linestyle=":", alpha=0.6)
plt.tight_layout()
plt.show()
