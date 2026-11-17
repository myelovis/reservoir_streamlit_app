# Prepared local data

`prepared.sqlite3` already contains the 1,000 sample points: 200 in each price area.
`samples.csv` is a readable export of the same points.

The local preparation adds regional hourly weather to SQLite. The separate uploader then copies
coordinates and regional averages to Atlas. Streamlit reads Atlas, not this local database.

`EL.geojson` was converted from the NVE shapefile in the repository.
`NO.geojson` is the union of those price-area polygons, for the mainland sampling frame.
The shapefile components match the current GitHub files checked on 17 November 2026.
These are not verified historical boundary vintages for every past year.

No official VASS file is included. Add the official three published water-area boundaries as
`VASS.geojson` with `area_id`, `area_type`, `area_number` and `name` properties.
Do not rename the earlier administrative regions to VASS.

Boundary source: Norges vassdrags- og energidirektorat (NVE), under NLOD.
https://kart.nve.no/enterprise/rest/services/Nettomraader/MapServer/0
https://biapi.nve.no/magasinstatistikk/api/Magasinstatistikk/HentOmr%C3%A5der
