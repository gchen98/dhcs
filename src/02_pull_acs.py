"""Pull ACS 5-year detail tables at ZCTA level and subset to the CA universe.

Post-2020 the ACS API no longer supports a `state:` predicate for ZCTAs, so we
pull all ~33k national ZCTAs and inner-join to data/interim/ca_zcta_universe.csv.

Requires a Census API key (free: https://api.census.gov/data/key_signup.html).
Pass via CENSUS_API_KEY env var or --key.

Output: data/raw/acs{YEAR}_zcta_ca_raw.csv  (estimates + MOEs, CA ZCTAs only)
"""

import argparse
import os
import sys
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"

# --- variables backing each SDI component -----------------------------------
# education: B15003 lines 002-016 = less than a regular HS diploma, pop 25+
EDU_LT_HS = [f"B15003_{i:03d}" for i in range(2, 17)]

VARS = {
    "pop_total": ["B01003_001"],
    # Group quarters population: campus/prison/barracks ZCTAs otherwise produce
    # meaningless household rates (a dorm ZCTA reads as "100% poverty").
    "group_quarters": ["B26001_001"],
    "edu": ["B15003_001"] + EDU_LT_HS,
    "poverty": ["B17001_001", "B17001_002"],
    "single_parent": ["B11003_001", "B11003_010", "B11003_016"],
    "rented": ["B25003_001", "B25003_003"],
    "no_vehicle": ["B25044_001", "B25044_003", "B25044_010"],
    "unemployed": ["B23025_003", "B23025_005"],
    "crowding": [
        "B25014_001",
        "B25014_005",
        "B25014_006",
        "B25014_007",
        "B25014_011",
        "B25014_012",
        "B25014_013",
    ],
}
ALL_VARS = [v for group in VARS.values() for v in group]

# MOEs only for the numerators/denominators we actually report on, to keep the
# request list short and the file readable.
MOE_VARS = ["B01003_001", "B17001_002", "B23025_005", "B25044_003", "B25044_010"]


def chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i : i + n]


def fetch(year, varlist, key, suffix):
    """Pull one chunk of variables for all national ZCTAs."""
    cols = [f"{v}{suffix}" for v in varlist]
    url = f"https://api.census.gov/data/{year}/acs/acs5"
    params = {
        "get": ",".join(cols),
        "for": "zip code tabulation area:*",
        "key": key,
    }
    r = requests.get(url, params=params, timeout=300)
    if r.status_code != 200 or not r.text.lstrip().startswith("["):
        sys.exit(f"ACS request failed ({r.status_code}) for {cols[:3]}...\n{r.text[:500]}")
    rows = r.json()
    df = pd.DataFrame(rows[1:], columns=rows[0])
    df = df.rename(columns={"zip code tabulation area": "zcta"})
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    # ACS uses large negative sentinels (-666666666 etc.) for suppressed values
    df[cols] = df[cols].mask(df[cols] < -1e6)
    return df[["zcta"] + cols]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2024, help="ACS 5-year end year")
    ap.add_argument("--key", default=os.environ.get("CENSUS_API_KEY", ""))
    args = ap.parse_args()

    if not args.key:
        sys.exit(
            "No Census API key. Get one free at "
            "https://api.census.gov/data/key_signup.html then either:\n"
            "  export CENSUS_API_KEY=...   or   --key <key>"
        )

    ca = pd.read_csv(INTERIM / "ca_zcta_universe.csv", dtype={"zcta": str})
    print(f"CA ZCTA universe: {len(ca)}")

    out = None
    for i, chunk in enumerate(chunks(ALL_VARS, 45), 1):
        print(f"  estimates chunk {i} ({len(chunk)} vars)...")
        df = fetch(args.year, chunk, args.key, "E")
        out = df if out is None else out.merge(df, on="zcta", how="outer")

    for i, chunk in enumerate(chunks(MOE_VARS, 45), 1):
        print(f"  MOE chunk {i} ({len(chunk)} vars)...")
        df = fetch(args.year, chunk, args.key, "M")
        out = out.merge(df, on="zcta", how="left")

    print(f"National ZCTAs returned: {len(out)}")
    out = ca[["zcta"]].merge(out, on="zcta", how="left")
    missing = out["B01003_001E"].isna().sum()
    print(f"CA rows: {len(out)}  (no ACS data for {missing})")

    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / f"acs{args.year}_zcta_ca_raw.csv"
    out.to_csv(path, index=False)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
