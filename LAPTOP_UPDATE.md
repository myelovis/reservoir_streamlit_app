# Laptop Home update

Copy `app.py`, `style.css` and `leaf.svg` together into your app's main folder. Replace the matching files, then restart Streamlit. For Cloud, commit all three to the deployed branch and reboot the app. Keep the existing modules, data and secrets.

The leaf uses `st.image()` with a separate SVG file so it renders reliably. It appears at the top right of the Home heading.

Home spacing was checked in a 1366 × 650 browser viewport. The leaf loaded at 58 × 72.5 pixels and the Home content required no vertical scrolling. Physical screen size alone does not determine browser space; browser zoom and Windows scaling can change the available viewport. Smaller screens retain normal scrolling rather than hiding content.
