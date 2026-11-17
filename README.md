# Reservoir app: Part 4

Start with **[START_HERE.md](START_HERE.md)**.

This local package adds a selectable region map, weather-property outliers,
rolling correlation, and recursive SARIMAX / Ridge forecasts to the existing app.

The five price areas have **200 sampled points each**, **1,000 points total**.
The points are already saved in a small local SQLite database.
National weather uses area-weighted averages of those samples.
Official VASS geometry is still needed for water-area mapping and derived weather.

No GitHub changes, live weather publication or database changes were made while preparing this package.
Run the preparation commands yourself before using the new Atlas datasets.

```text
prepare_regions.py → local sample database
prepare_all_weather.py → local weather database
publish_local.py → MongoDB Atlas
app.py → reads Atlas
```

Run `setup_local.py` once to save credentials privately outside this folder.

The design is plain and small. The helper files contain the calculations;
the page files connect them to Streamlit controls.
