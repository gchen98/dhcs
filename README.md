# Medi-Cal Capitation & Social Deprivation Analysis

An independent, end-to-end analytic project that asks one question of a
Medi-Cal-style managed-care payment pipeline: **does diagnosis-based risk-adjusted
capitation track place-based social deprivation, or does it under- or over-pay in
socially deprived areas?**

> **Data note.** Deprivation measures are built from **real, public American
> Community Survey (ACS) data**. Eligibility and claims records are **simulated**
> (no real Medi-Cal member data is used). Findings about payment adequacy are
> therefore properties of the modeled pipeline, not statements about actual DHCS
> rates. This is a training and portfolio project, not DHCS work.

## What it does

| Stage | What happens | Output |
|---|---|---|
| 1. SDI | Builds a ZCTA-level Social Deprivation Index for California from ACS 2020-2024 5-year data. Compares an equal-weight z-score composite with a first-principal-component composite and validates against the published Robert Graham Center SDI. | `sdi_by_zcta.csv` |
| 2. Simulation | Builds a CDPS category reference (57 categories) and ICD-10 crosswalk, then simulates 250,000 person-years of eligibility and about 879,000 claims with known ground-truth cost weights. | `eligibility.csv`, `claims.parquet`, `sim_ground_truth_weights.csv` |
| 3. Cost model | Fits cost models (OLS, log-cost OLS, gamma GLM with log link) on CDPS flags plus demographics; compares recovered weights with the ground truth. | `cdps_category_weights.csv` |
| 4. Capitation | Normalizes risk scores to a mean of 1.0, applies rate-cell base rates, and checks adequacy with predictive ratios. | `capitation_by_person.csv` |
| 5. Mapping | Aggregates to ZCTA with small-cell suppression, joins Census boundaries, draws choropleths, and exports a GeoPackage and shapefile. | `data/gis/` |
| 6. Sensitivity | Isolates which mechanisms create the payment gradient across deprivation levels. | Figure 26 |

## Selected results (simulated payment pipeline)

- SDI covers 1,497 California ZCTAs (99.5% of state population); equal-weight and PCA composites correlate at r = 0.99; 1,492 of 1,497 ZCTAs match the published RGC SDI.
- Predictive ratio falls from 1.029 in the least deprived areas to 0.971 in the most deprived (about 5.8 points of under-payment), with a linear trend of about -0.6 points per decile.
- The sensitivity analysis found the **unscored-member rule** (members with thin diagnostic history receive their rate-cell average risk score) was the largest real contributor to the gradient. The initial hypothesis, diagnosis-capture differences, turned out to be a minor mechanism.
- Small ZCTAs are suppressed: predictive-ratio SD is 0.86 for ZCTAs with 10 or fewer enrollees versus 0.20 for 30-100.

## Reproducing it

```bash
conda create -n dhcs-sdi -c conda-forge -c bioconda \
    python=3.12 snakemake-minimal jupyterlab \
    pandas numpy scipy matplotlib statsmodels geopandas pyarrow requests nbconvert
conda activate dhcs-sdi

export CENSUS_API_KEY=...        # free key: https://api.census.gov/data/key_signup.html
snakemake -c4                    # download inputs and build intermediate files
snakemake -c1 notebook           # execute notebooks/01_sdi_construction.ipynb
```

Inputs (all public): Census ZCTA-county relationship file, Census 2024
gazetteer, ACS 5-year API, Robert Graham Center SDI, Census 2020 ZCTA
cartographic boundaries. URLs and vintages are in `config/pipeline.yaml`.

## Repository layout

```
Snakefile                      workflow for downloads and derived inputs
config/pipeline.yaml           URLs, ACS vintage
src/                           acquisition and helper scripts
notebooks/01_sdi_construction.ipynb   analysis (Steps 1-6)
docs/design_spec.md            original design specification
docs/ROADMAP.md                planned extensions
```

## Status and roadmap

Implemented: Steps 1-6 above, with a GeoPackage and shapefile export intended
for GIS tools. Maps in this repository are drawn with geopandas and matplotlib.

Planned (not yet done; see `docs/ROADMAP.md`):
- **ArcGIS layer:** publish the ZCTA GeoPackage and build the capitation, SDI, and predictive-ratio maps in ArcGIS.
- **Power BI report:** a dashboard over the ZCTA and county aggregates.
- **Real public data:** add real Medi-Cal enrollment data from data.ca.gov (county-level managed-care enrollment) alongside the simulated pipeline.

## Limitations

- Claims and eligibility are simulated; the SDI-morbidity link is built in by design, so the payment-adequacy findings describe the modeled pipeline.
- ACS ZCTA estimates are noisy for small populations; thresholds are set in the notebook configuration.
- Plan factors are arbitrary stand-ins for negotiated plan adjustments.
