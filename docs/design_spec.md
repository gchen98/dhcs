# Medi-Cal Capitation & Social Deprivation Training Project — Design Spec

**Purpose:** a self-contained training exercise that reproduces, at small scale, the core Medicaid managed-care risk-adjustment pipeline DHCS actually runs — eligibility/claims → diagnosis-based risk categories (CDPS) → regression-fit weights → risk scores → capitation rates — and then asks a real analytic question of it: does risk-adjusted capitation track a place-based social deprivation index (SDI), or does it under/over-pay in socially deprived zip codes? That question is the throughline connecting your two references (Kronick et al.'s original CDPS methodology, and the more recent SDI/Medi-Cal utilization literature) and gives the ArcGIS map an actual point beyond "here's a heat map."

Scope decisions already made: California statewide (all ZCTAs), real ACS-derived SDI (not synthetic), and CDPS weights fit via your own regression rather than pulled from the published DHCS/CMS table (a validation step against the published table is included as an optional Phase 6).

---

## 0\. Reproducing the inputs

### Environment

Create a conda environment with everything the workflow and the notebook need.
`snakemake` comes from bioconda; everything else from conda-forge:

```bash
conda create -n dhcs-sdi -c conda-forge -c bioconda \
    python=3.12 snakemake-minimal jupyterlab \
    pandas numpy scipy matplotlib statsmodels geopandas pyarrow requests nbconvert

conda activate dhcs-sdi
```

What each one is for: **snakemake-minimal** runs the workflow (the full
`snakemake` package adds cluster/cloud executors this project does not use);
**pandas / numpy** for all tabular work; **scipy** for `expit` in the simulation;
**statsmodels** for the GLM and OLS cost regressions; **matplotlib** for the 26
figures; **geopandas** for the ZCTA boundary join and choropleths; **pyarrow**
for the Parquet claims file; **requests** for the Census API pull; **nbconvert**
for the headless `notebook` rule; **jupyterlab** to open the notebook by hand.

Then launch the notebook — pick the **Python 3 (ipykernel)** kernel, which is
this environment's:

```bash
jupyter lab notebooks/01_sdi_construction.ipynb
```

Verified on 2026-09-14: a fresh env built with the command above (Python 3.12,
pandas 3.0.5, geopandas 1.1.4, snakemake 9.x) runs the whole workflow and the
notebook end to end from an empty directory. Note that conda-forge currently
resolves to pandas 3.x; the notebook runs clean on both 2.3 and 3.0, and
`sdi_by_zcta.csv` agrees between them to 3e-14.

### Running it

Everything the notebook opens on startup is built by the `Snakefile` at the repo
root — four public downloads plus the two derived files:

```
snakemake -c4            # build all inputs for notebooks/01_sdi_construction.ipynb
snakemake -c1 notebook   # the above, then execute the notebook headlessly
snakemake -c1 -n         # dry run: what is missing / stale
```

| Target | Source | Used by |
|---|---|---|
| `data/raw/tab20_zcta520_county20_natl.txt` | Census 2020 ZCTA-county relationship file | CA membership |
| `data/raw/2024_Gaz_zcta_national.txt` | Census 2024 gazetteer | land area, density denominator |
| `data/interim/ca_zcta_universe.csv` | `src/01_ca_zcta_universe.py` | notebook §1 |
| `data/raw/acs2024_zcta_ca_raw.csv` | `src/02_pull_acs.py` (needs `CENSUS_API_KEY`) | notebook §2-5 |
| `data/raw/rgc_sdi_2015_2019_zcta.csv` | Robert Graham Center published SDI | notebook §7 validation |
| `data/raw/geo/cb_2020_us_zcta520_500k.*` | Census 2020 cartographic boundaries | notebook §5.2 choropleths |

The ACS pull needs a free Census API key, read from `$CENSUS_API_KEY` or the
untracked `.census_api_key` file at the repo root. URLs, the ACS vintage, and
the boundary-file stem live in `config/pipeline.yaml`.

Rules invoke the same interpreter that is running Snakemake, so whichever
environment you launch `snakemake` from is the one the scripts and the notebook
execute in — no per-rule activation, and no way for the workflow to silently
drift into a different Python than the one you tested.

---

## 1\. Pipeline overview

ACS 5-year data (ZCTA)          Synthetic eligibility file          Synthetic claims file

        |                                |                                  |

        v                                v                                  v

   SDI composite  \-------------\>  person-year table  \<------------  ICD/NDC-coded encounters

    (per ZCTA)          (zip assigned per person,           (linked to person-year by ID)

                          drawn with SDI-correlated

                          demographic mix)

                                        |

                                        v

                          CDPS category flags per person-year

                          (from ICD dx codes \+ NDC-based Rx categories)

                                        |

                                        v

                    Regression: cost \~ CDPS categories (+ age/sex/aid cat)

                                        |

                                        v

                       Fitted category weights \-\> individual risk score

                                        |

                                        v

              Plan-specific capitation \= base rate x risk score x plan adjustment

                                        |

                                        v

                  Aggregate to zip (mean capitation, mean risk score, N)

                                        |

                                        v

                          Join to ZCTA shapefile \-\> ArcGIS choropleth

                                        |

                                        v

                    Overlay/compare against SDI choropleth \-\> correlation analysis

---

## 2\. Step 1 — SDI construction (real data, ZCTA level)

**Source:** American Community Survey 5-year estimates (most recent vintage, e.g. 2018–2022 ACS) at the ZCTA level, pulled via the Census API (`api.census.gov`) or `tidycensus`/`census` Python package. All CA ZCTAs (\~1,760).

**Candidate input variables** (mirrors the Robert Graham Center's published Social Deprivation Index, which you could optionally pull directly as a sanity-check benchmark rather than rebuild):

- % population with less than high school education  
- % population in poverty  
- % single-parent households  
- % households in rented housing (inverse of home ownership)  
- % households with no vehicle  
- % population unemployed (civilian labor force 16+)  
- population density (persons per sq mile, from Census TIGER land area)  
- % households below a housing-cost-burden or overcrowding threshold (optional extension)

**Method:** standardize each variable (z-score), combine via either (a) simple unweighted average of z-scores, matching the original SDI paper (Butler et al. 2013\) methodology, or (b) a first-principal-component score from PCA — worth doing both and comparing, since PCA weighting is a nice thing to show you understand versus an arbitrary equal-weight index. Rescale composite to 0–100 for interpretability.

**Deliverable:** `sdi_by_zcta.csv` with columns `zcta, sdi_score, sdi_rank, [component variables]`.

**Note:** ACS margins of error at ZCTA level get noisy for small-population zips — worth flagging/filtering zips below a population threshold (e.g. \<500) or noting the limitation, since DHCS analysts would care about this.

---

## 3\. Step 2 — Simulated eligibility and claims data

This is the "17M person-year" structure from your second reference, scaled down to something tractable (suggest starting at \~200K–500K simulated person-years, or a random sample of ZCTAs, before deciding whether to push to full scale).

**Eligibility file** — one row per person-year:

- `person_id`, `year`, `zcta` (drawn from CA ZCTA list, population-weighted so denser zips get more enrollees)  
- `age`, `sex`  
- `aid_category` (e.g. TANF/child, disabled/SSI, adult expansion — three broad categories mirroring your reference's disabled/children/adult split, \~1.4M / 9.2M / 6.4M ratio if you want to preserve realistic proportions)  
- `months_enrolled` (1–12, with partial-year enrollment realistically more common at the edges of the year)  
- `mco_plan_id` (assign 3–6 synthetic MCO plans per region, since capitation is plan-specific)

**Claims file** — one or more rows per person-year:

- `person_id`, `year`, `service_date`  
- `procedure_code` (CPT/HCPCS, can be coarse — just enough to distinguish encounter types)  
- `icd_code` (diagnosis codes — this is the key field for CDPS)  
- `ndc_code` (for Rx-based CDPS categories — CDPS+Rx model)  
- `amount_paid`

**Simulation logic (important — this is what makes the exercise meaningful rather than just noise):**

1. Assign each person a "true" latent morbidity level, correlated with `age`, `aid_category`, and — deliberately — with their zip's `sdi_score` (to simulate the real-world pattern that deprivation correlates with worse baseline health access/outcomes). This SDI-morbidity link is what you'll later "discover" in the analysis, so document the ground-truth relationship you bake in.  
2. From latent morbidity, draw a set of CDPS-relevant condition categories (e.g. diabetes, cardiovascular, psychiatric, pulmonary, CNS, renal, substance use, pregnancy, skeletal, etc. — CDPS has \~20 major categories, several with severity sub-tiers) using category-specific prevalence rates.  
3. For each assigned category, generate plausible ICD-10 codes that would map to it (a lookup table you build once) and, for Rx-relevant categories, plausible NDC codes.  
4. Generate `amount_paid` as a function of assigned categories using a **known synthetic weight** (e.g. base cost \+ Σ true\_category\_weight \+ noise) — keep this "true" generative weight separate from what your regression later recovers, so you can validate the regression against ground truth.

**Deliverables:** `eligibility.csv`, `claims.csv`, and a `sim_ground_truth_weights.csv` documenting the weights you baked in (for later validation).

---

## 4\. Step 3 — CDPS category assignment and weight regression

1. **ICD/NDC → CDPS category mapping:** build (or find) a crosswalk table. The full CDPS diagnostic classification categories/ICD mapping is published by UCSD's CDPS project (cdps.ucsd.edu) — worth pulling the real category list even if you're simulating codes, so your categories match the real model (e.g. Diabetes, Psychiatric, Cardiovascular, Renal, Pulmonary, CNS, Skeletal, Substance Abuse, Pregnancy, Cancer, plus Rx-based categories). For the exercise you don't need the entire multi-thousand-code ICD crosswalk — a representative subset per category is enough.  
2. **Flag construction:** for each person-year, create binary (or highest-severity-tier) indicator columns per CDPS category based on any qualifying diagnosis/NDC in their claims.  
3. **Regression:** fit total annual cost \~ CDPS category flags (+ optionally age band, sex, aid category as covariates, matching how concurrent risk-adjustment models are actually specified). Use a model appropriate for cost data — OLS on log-cost, or a GLM with gamma/log link (this is a good place to show you know cost-data modeling isn't naive OLS on raw dollars, which is a real critique of some early risk-adjustment work).  
4. **Recovered weights** \= the fitted coefficients per category. Compare against `sim_ground_truth_weights.csv` (does the regression recover what you put in?) and optionally against the real published DHCS/CMS CDPS+Rx weight table as a face-validity check.

**Deliverable:** `cdps_category_weights.csv`, plus a short model diagnostics writeup (R², residual plots, comparison to ground truth).

---

## 5\. Step 4 — Risk scores and capitation rates

1. **Risk score** per person-year \= sum of their fitted category weights (+ demographic coefficients), following standard concurrent/prospective risk-adjustment convention.  
2. **Capitation rate** per person-year \= `plan_base_rate[mco_plan_id, rate_cell] × risk_score × plan_adjustment_factor`. Keep it simple at first: one statewide base rate, or base rates varying by rate cell (aid category × age band) — this mirrors how DHCS actually sets Medi-Cal managed care capitation, which varies by rate region and aid category, not a single number.  
3. Note the CDPS convention of normalizing risk scores to a population mean of 1.0 before applying to a base rate — worth implementing since it's how it's actually done and easy to explain in an interview.

**Deliverable:** `capitation_by_person.csv`.

---

## 6\. Step 5 — Aggregation and ArcGIS visualization

1. Aggregate `capitation_by_person.csv` to zip: mean capitation, mean risk score, enrollee count, mean SDI (join back from Step 1).  
2. Join to a CA ZCTA boundary shapefile (Census TIGER/Line ZCTA5 shapefiles, or CA-clipped extract).  
3. Build in ArcGIS (Pro or Online):  
   - Choropleth \#1: mean capitation rate by zip  
   - Choropleth \#2: SDI score by zip  
   - A bivariate/dual-variable map or side-by-side comparison to visually assess correlation  
   - Optionally a scatter (capitation vs. SDI, zip-level, sized by enrollee N) as a companion chart, since a map alone won't show you the correlation, just the pattern  
4. Suppress or flag zips with very low enrollee counts (unstable/noisy averages) rather than mapping them at full confidence — another real analytic practice worth demonstrating.

**Deliverable:** `.gdb`/`.shp` or feature layer package, plus 2–3 exported map images.

---

## 7\. Validation / QA checklist (recommend as an explicit final phase)

- Regression-recovered weights vs. ground-truth simulated weights — correlation/scatter  
- Recovered weights vs. published DHCS/CMS CDPS+Rx table — face validity, sign/magnitude sanity  
- Aggregate capitation sums to something plausible relative to real Medi-Cal per-member-per-month figures (order-of-magnitude check)  
- SDI construction sanity-check against the real Robert Graham Center SDI values for a handful of known CA zips (e.g. a known high-poverty Fresno/Central Valley zip vs. a known affluent Bay Area zip)  
- Document every place synthetic data deviates from real-world structure, so it's honestly presentable as a training exercise rather than "real findings"

---

## 8\. Suggested tech stack

- **Python** (pandas, numpy, statsmodels or scikit-learn for the regression, `census`/`cenpy` or direct Census API calls for ACS pull)  
- **Geopandas** for the ZCTA join/aggregation before export  
- **ArcGIS Pro** (or ArcGIS Online if you don't have Pro) for the final map — export aggregated CSV \+ shapefile and bring in as a joined layer

---

## 9\. Phased build order (recommended)

1. Pull real ACS data for CA ZCTAs, build SDI composite → sanity-check against RGC published SDI  
2. Build the CDPS category list \+ a lightweight synthetic ICD/NDC crosswalk  
3. Simulate eligibility \+ claims (start small, e.g. 50K person-years, before scaling)  
4. Fit the cost regression, recover weights, validate against ground truth  
5. Compute risk scores → capitation → aggregate to zip  
6. Bring into ArcGIS, build the maps, run the SDI-vs-capitation comparison  
7. (Optional) scale up to full \~17M-style volume and/or full CA ZCTA set if the small-scale run works cleanly

---

## Open decisions for next session

- Target simulation scale (start at 50K–500K person-years?)  
- Number of synthetic MCO plans and whether base rates vary by rate region (Medi-Cal really does have distinct rate regions)  
- ArcGIS Pro vs. ArcGIS Online availability on your end  
- How deep to go on the ICD/NDC → CDPS crosswalk (full official crosswalk vs. representative subset)

