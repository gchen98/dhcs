# CLAUDE.md

Project: Medi-Cal capitation & social deprivation analysis (independent portfolio
project by Gary Chen). Read `README.md` for the overview and `docs/ROADMAP.md`
for what to do next.

## Ground rules (important)
- **Honesty about data and tools.** Claims and eligibility records are *simulated*; only ACS/Census inputs (and any data.ca.gov data added later) are real. Say so in every README, figure caption, and write-up. Never describe this as DHCS work.
- **Do not claim a tool until it has actually been used here.** ArcGIS and Power BI are *planned*; maps in the repo are geopandas/matplotlib. Move them from "planned" to "implemented" in README only after the artifact exists in the repo (screenshots, .pbix, or ArcGIS project/package).
- Keep real and simulated results visibly separate in outputs.
- Never commit API keys. The Census key lives in `$CENSUS_API_KEY` or the untracked `.census_api_key`.
- Don't commit large generated data (`data/raw`, `data/interim`, `data/out`); the Snakefile rebuilds them. Small summary CSVs and figures used by the README are fine.

## Environment
- Conda env: `dhcs-sdi` (Python 3.12, snakemake-minimal, pandas, numpy, scipy, statsmodels, geopandas, matplotlib, pyarrow, requests, nbconvert, jupyterlab).
- The Snakefile runs scripts with the same interpreter that runs Snakemake, so activate the env first.

## Commands
```
conda activate dhcs-sdi
snakemake -c4              # build inputs (needs CENSUS_API_KEY)
snakemake -c1 -n           # dry run
snakemake -c1 notebook     # execute notebooks/01_sdi_construction.ipynb headlessly
jupyter lab notebooks/01_sdi_construction.ipynb
```

## Layout
- `Snakefile`, `config/pipeline.yaml`: downloads and derived inputs (URLs, ACS vintage)
- `src/`: acquisition scripts (`01_ca_zcta_universe.py`, `02_pull_acs.py`) and plotting theme
- `notebooks/01_sdi_construction.ipynb`: analysis, Steps 1-6
- `docs/design_spec.md`: original design; `docs/ROADMAP.md`: planned work

## Current state
Steps 1-6 are implemented in the notebook (SDI, CDPS reference and simulation, cost
models, capitation, ZCTA mapping/export, sensitivity analysis).

## Next steps (in order; see docs/ROADMAP.md)
1. Real data: add data.ca.gov Medi-Cal Managed Care Enrollment Report (county level). First confirm the dataset id, columns and update schedule on the portal. Add `src/03_pull_medi_cal_enrollment.py` and a Snakemake rule; roll ZCTA SDI up to county (population-weighted).
2. Power BI: export tidy tables (`zcta_summary.csv`, `county_summary.csv`, `predictive_ratio_by_sdi.csv`) and build the report (Power BI Desktop is Windows-only).
3. ArcGIS: load `data/gis/medi_cal_capitation_zcta.gpkg` and rebuild the maps.

## Style
- Prefer scripts for slow, cached acquisition; keep the notebook as the interactive analysis surface.
- Make analytic choices explicit in the notebook configuration cell.
- Update README results and ROADMAP status whenever a step is finished.
