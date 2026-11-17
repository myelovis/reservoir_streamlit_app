# AI usage

AI helped read the existing app structure, prepare the local upgrade files, explain the region definitions,
write short Python helpers and pages, and create regression tests.

The work included GeoJSON conversion, spatial sampling, shared selectors, weather-property outliers,
weekly rolling correlations, recursive forecasting, and separate Atlas preparation scripts.

Validation included 19 passing automated tests, syntax checks, execution of notebook code with controlled data,
and small live NVE/Open-Meteo reads. One-time credential reuse and local SQLite storage were tested.
Private Atlas publication and empirical regional findings still require the user's own run.

The user requested simple code, simple English comments, a minimal design and no GitHub changes.
All deliverables were prepared locally. No credentials are included in the package.
