# Home page update

The three changes follow the coloured marks in your screenshot:

- Green: **Select region and dates** opens a modal popup containing the area controls, dates and map. **Done** closes it. The shared selection is saved in session state. There is no separate Map entry in the navigation.
- Blue: the three source names link to the NVE Magasinstatistikk API, Open-Meteo Historical Weather API documentation, and ENTSO-E REST API guide.
- Orange: the links inside each card are moved further right, below the heading. Their text can wrap on smaller screens.

Replace these files in your existing project, keeping their folder locations:

```text
app.py
region_picker.py       # New popup
reservoir_data.py      # Controls can appear in the popup or sidebar
shared_ui.py           # Dates can appear in the popup or sidebar
style.css              # Warm cream, clay, sage and gold
.streamlit/config.toml # Matching app theme
```

Restart the local app, or redeploy your Cloud app after updating those source files. No database upload, password change or new weather download is needed. This ZIP contains no database or credentials. GitHub was not changed by Codex.

The automated popup test uses controlled reservoir data and a stubbed map component. It checks opening, selector rendering, saved selection and closing. Browser appearance and actual map events are not covered by that test.

The minimal Bohemian design uses system serif headings, softly coloured cards, rounded borders and a small circle-and-line accent. It loads no external fonts, images or animations.
