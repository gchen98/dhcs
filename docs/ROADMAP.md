# Roadmap

Order of work: (1) real data, (2) Power BI, (3) ArcGIS. Update this file as items are done.

## 1. Real public data (data.ca.gov / CHHS)
- Candidate dataset: Medi-Cal Managed Care Enrollment Report (monthly enrollment by county, plan, and aid category) on the California open data portal. Confirm the current dataset id, columns, and update schedule before building on it.
- Granularity is county, not ZCTA. Roll ZCTA SDI up to county (population-weighted) and compare real enrollment mix (aid category, plan) across SDI levels.
- Add `src/03_pull_medi_cal_enrollment.py` and a Snakemake rule; cache raw files under `data/raw/`.
- Keep real and simulated results clearly separated in all figures and tables.

## 2. Power BI
- Export tidy tables: `zcta_summary.csv`, `county_summary.csv`, `predictive_ratio_by_sdi.csv`.
- Report pages: SDI map, capitation vs. SDI scatter, predictive ratio by decile, county enrollment (real data).
- Note: Power BI Desktop runs on Windows only. Publish a screenshot set and the .pbix to the repo; only list Power BI as a skill after it exists.

## 3. ArcGIS
- Load `data/gis/medi_cal_capitation_zcta.gpkg` into ArcGIS Pro (or ArcGIS Online) and rebuild the three maps there.
- Pro requires a license; ArcGIS Online has a free public account with limits. QGIS is an acceptable fallback but does not count as ArcGIS experience.
