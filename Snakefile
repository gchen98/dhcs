"""Reproduce every external input required by notebooks/01_sdi_construction.ipynb.

The notebook is the interactive analytic surface: everything from component
construction onward lives there and re-runs in seconds. This workflow handles
the slow, cached, run-once part — the four public downloads and the two derived
files the notebook opens on startup.

    Snakefile
      |
      +-- tab20_zcta520_county20_natl.txt  (Census 2020 ZCTA-county relationship)
      +-- 2024_Gaz_zcta_national.txt       (Census gazetteer: land area, centroid)
      |        \
      |         `-> src/01_ca_zcta_universe.py -> data/interim/ca_zcta_universe.csv
      |                                                    |
      +-- src/02_pull_acs.py <----------------------------'
      |        `-> data/raw/acs2024_zcta_ca_raw.csv        (needs CENSUS_API_KEY)
      |
      +-- rgc_sdi_2015_2019_zcta.csv       (published RGC SDI, section 7 validation)
      +-- cb_2020_us_zcta520_500k.shp      (ZCTA boundaries, section 5.2 choropleths)

Usage
-----
    snakemake -c1                  # build all notebook inputs
    snakemake -c1 notebook         # the above, then execute the notebook
    snakemake -c1 -n               # dry run
    snakemake -c1 --delete-all-output   # drop everything this workflow made

The Census API key is read from $CENSUS_API_KEY, falling back to the untracked
.census_api_key file at the repo root. Get one free at
https://api.census.gov/data/key_signup.html

Environment: the `pd-qtl` conda env (pandas, geopandas, statsmodels, scipy,
pyarrow, matplotlib, requests, nbconvert, snakemake).
"""

import os
import sys
from pathlib import Path

from snakemake.exceptions import WorkflowError

configfile: "config/pipeline.yaml"


ROOT = Path(workflow.basedir)
RAW = "data/raw"
INTERIM = "data/interim"
OUT = "data/out"

ACS_YEAR = config["acs_year"]
GAZ_YEAR = config["gazetteer_year"]
URLS = config["urls"]
BOUNDARY_STEM = config["boundary_stem"]

# The interpreter running Snakemake, so the analysis scripts land in the same
# environment as the workflow rather than whatever `python` PATH happens to
# resolve to. Override with --config python=/path/to/python.
PYTHON = config.get("python") or sys.executable
# geopandas needs the sidecars alongside the .shp; declaring them keeps a
# half-finished unzip from being mistaken for a complete one.
BOUNDARY_EXTS = [".shp", ".shx", ".dbf", ".prj", ".cpg"]


def census_api_key():
    """$CENSUS_API_KEY, else the untracked .census_api_key at the repo root.

    Returns "" rather than raising when neither is set: params are resolved
    while the DAG is built, so raising here would break even a dry run or a
    re-run that never touches the ACS rule. src/02_pull_acs.py prints the
    sign-up instructions and exits if it is handed an empty key.
    """
    key = os.environ.get("CENSUS_API_KEY", "").strip()
    if key:
        return key
    keyfile = ROOT / ".census_api_key"
    if keyfile.exists():
        return keyfile.read_text().strip()
    return ""


# --- targets ----------------------------------------------------------------

NOTEBOOK_INPUTS = [
    f"{INTERIM}/ca_zcta_universe.csv",
    f"{RAW}/acs{ACS_YEAR}_zcta_ca_raw.csv",
    f"{RAW}/rgc_sdi_2015_2019_zcta.csv",
    *[f"{RAW}/geo/{BOUNDARY_STEM}{ext}" for ext in BOUNDARY_EXTS],
]


rule all:
    input:
        NOTEBOOK_INPUTS


# --- downloads --------------------------------------------------------------

rule download_zcta_county_relationship:
    """Which ZCTAs touch which counties — the only way to get 'is this ZCTA in
    California?', since ZCTAs carry no state field."""
    output:
        f"{RAW}/tab20_zcta520_county20_natl.txt",
    params:
        url=URLS["zcta_county_rel"],
    retries: 2
    shell:
        "curl -fsSL --retry 3 --retry-delay 5 -o {output} {params.url:q}"


rule download_gazetteer:
    """Land area (ALAND_SQMI) and internal centroid per ZCTA — the population
    density denominator."""
    output:
        f"{RAW}/{GAZ_YEAR}_Gaz_zcta_national.zip",
    params:
        url=URLS["gazetteer"],
    retries: 2
    shell:
        "curl -fsSL --retry 3 --retry-delay 5 -o {output} {params.url:q}"


rule unzip_gazetteer:
    input:
        rules.download_gazetteer.output,
    output:
        f"{RAW}/{GAZ_YEAR}_Gaz_zcta_national.txt",
    shell:
        "unzip -o -j -DD {input} -d $(dirname {output})"


rule download_rgc_sdi:
    """The published Robert Graham Center SDI (ACS 2015-2019, ZCTA level), used
    in section 7 as an external face-validity check on our composite.

    Hosted on the AAFP asset CDN; the versioned path is what
    graham-center.org/maps-data-tools/social-deprivation-index.html links to."""
    output:
        f"{RAW}/rgc_sdi_2015_2019_zcta.csv",
    params:
        url=URLS["rgc_sdi_zcta"],
    retries: 2
    shell:
        "curl -fsSL --retry 3 --retry-delay 5 -o {output} {params.url:q}"


rule download_zcta_boundaries:
    """2020 cartographic boundary file (500k generalized) rather than
    full-resolution TIGER/Line: an eighth the size and matched in vintage to the
    ZCTA universe. ~67 MB."""
    output:
        f"{RAW}/geo/{BOUNDARY_STEM}.zip",
    params:
        url=URLS["zcta_boundaries"],
    retries: 2
    shell:
        "curl -fsSL --retry 3 --retry-delay 5 -o {output} {params.url:q}"


rule unzip_zcta_boundaries:
    input:
        rules.download_zcta_boundaries.output,
    output:
        multiext(f"{RAW}/geo/{BOUNDARY_STEM}", *BOUNDARY_EXTS),
    shell:
        "unzip -o -DD {input} -d $(dirname {input})"


# --- derived inputs ---------------------------------------------------------

rule ca_zcta_universe:
    """Intersect the relationship file with state FIPS 06 to get the CA ZCTA
    list, attach gazetteer land area, and flag ZCTAs straddling a state line."""
    input:
        rel=rules.download_zcta_county_relationship.output,
        gaz=rules.unzip_gazetteer.output,
        script="src/01_ca_zcta_universe.py",
    output:
        f"{INTERIM}/ca_zcta_universe.csv",
    log:
        "logs/01_ca_zcta_universe.log",
    shell:
        f"{PYTHON} {{input.script}} > {{log}} 2>&1"


rule pull_acs:
    """Pull the ACS 5-year detail tables backing the eight SDI components.

    Post-2020 the ACS API rejects a `state:` predicate on ZCTAs, so the script
    pulls all ~33k national ZCTAs and inner-joins to the CA universe — which is
    why the universe is an input here and not just a downstream join."""
    input:
        universe=rules.ca_zcta_universe.output,
        script="src/02_pull_acs.py",
    output:
        f"{RAW}/acs{ACS_YEAR}_zcta_ca_raw.csv",
    params:
        year=ACS_YEAR,
        key=lambda wildcards: census_api_key(),
    log:
        "logs/02_pull_acs.log",
    shell:
        f"{PYTHON} {{input.script}} --year {{params.year}} --key {{params.key:q}} > {{log}} 2>&1"


# --- optional: run the notebook end to end ----------------------------------

rule notebook:
    """Execute 01_sdi_construction.ipynb headlessly (Steps 1-6).

    Not part of `all`: the notebook is meant to be run interactively. This rule
    exists so the whole chain can be verified in CI or after a clean checkout.
    Outputs listed are the deliverables other steps consume; the notebook also
    writes the figures/ PNGs and data/gis/ layers."""
    input:
        NOTEBOOK_INPUTS,
        notebook="notebooks/01_sdi_construction.ipynb",
        theme="src/sdi_theme.py",
    output:
        executed=f"{OUT}/01_sdi_construction.executed.ipynb",
        sdi=f"{OUT}/sdi_by_zcta.csv",
        weights=f"{OUT}/cdps_category_weights.csv",
        capitation=f"{OUT}/capitation_by_person.csv",
        by_zcta=f"{OUT}/capitation_by_zcta.csv",
    log:
        "logs/01_sdi_construction.log",
    shell:
        f"{PYTHON} -m nbconvert --to notebook --execute "
        "--ExecutePreprocessor.timeout=-1 "
        f"--output-dir {OUT} "
        "--output 01_sdi_construction.executed.ipynb "
        "{input.notebook} > {log} 2>&1"
