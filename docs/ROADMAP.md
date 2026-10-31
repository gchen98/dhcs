# Roadmap

Order of work: (1) real data, (2) Power BI, (3) ArcGIS. Update this file as items are done.

## 1. Real public data (data.ca.gov / CHHS)
- Dataset (confirmed 2026-10-22): **Medi-Cal Managed Care Enrollment Report** (`medi-cal-managed-care-enrollment-report` on data.ca.gov, DHCS). Columns: Enrollment Month, Plan Type, County, Plan Name, Count of Enrollees, plus annotation code/description (suppression). Monthly from 2007-01. **No aid category.** Counties are names, not FIPS; counts are comma-formatted text.
- Granularity is county x plan x month. Roll ZCTA SDI up to county (population-weighted) and compare **enrollment per capita** (enrollees / ACS county population from the same rollup) and plan type across SDI levels. Plan type is set countywide, so it describes county context, not member mix.
- Add `src/03_pull_medi_cal_enrollment.py` and a Snakemake rule; cache raw files under `data/raw/`.
- Keep real and simulated results clearly separated in all figures and tables.

## 2. Power BI
- Export tidy tables: `zcta_summary.csv`, `county_summary.csv`, `predictive_ratio_by_sdi.csv`.
- Report pages: SDI map, capitation vs. SDI scatter, predictive ratio by decile, county enrollment (real data).
- Note: Power BI Desktop runs on Windows only. Publish a screenshot set and the .pbix to the repo; only list Power BI as a skill after it exists.

## 3. ArcGIS
- Load `data/gis/medi_cal_capitation_zcta.gpkg` into ArcGIS Pro (or ArcGIS Online) and rebuild the three maps there.
- Pro requires a license; ArcGIS Online has a free public account with limits. QGIS is an acceptable fallback but does not count as ArcGIS experience.
