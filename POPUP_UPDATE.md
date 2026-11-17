# Laptop region popup

Replace these files in your existing app folder:

```text
region_picker.py
reservoir_data.py
shared_ui.py
style.css
```

Restart Streamlit. On Cloud, update the deployed source branch and reboot the app. No database or credential changes are needed.

The popup uses a 15% left control column and an 85% right map column. Start and end dates have separate fields so they stay readable. The map is 400 pixels high. Weather-property selection appears when Colour by is Weather property.

Checked at a 1366 × 650 browser viewport using controlled reservoir data and the real bundled region polygons. The dialog was 551 pixels high and did not require scrolling; its map measured 1038 × 400 pixels. Two targeted checks passed for popup operation and shared date controls. The temporary preview code is not included.

Small browser windows may still need scrolling. Keep the previous Home files, including `leaf.svg`, beside these updated modules.
