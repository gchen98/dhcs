"""Summary

Description

Output: outfile
"""

import argparse
import os
import sys
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"


def main():
    ap = argparse.ArgumentParser()
    # ap.add_argument("--paramkey",type=int,default=2024,help="")
    # ap.add_argument("--key",default=os.environ.get("CENSUS_API_KEY",""))
    args = ap.parse_args()

    if not args.key:
        sys.exit(
            # "No Census API key. Get one free at "
            # "https://api.census.gov/data/key_signup.html then either:\n"
            # "  export CENSUS_API_KEY=...   or   --key <key>"
        )
    url = f"https://api.census.gov/data/{args.year}/acs/acs5"
    params = {
        "get":"NAME,B01003_001E",
        "for": "county:*",
        "in": "state:06",
        "key": args.key,
    }
    r = requests.get(url, params= params, timeout=300)
    if r.status_code!=200 or not r.text.lstrip().startswith("["):
        sys.exit(f"ACS request failed ({r.status_code}) for {r.text[:1000]}")
    rows = r.json()
    df = pd.DataFrame(rows[1:],columns = rows[0])
    # do sanity checks.
    # we expect 58 counties in CA
    assert len(df) == TOTAL_COUNTIES, "not equal to 58 counties"
    df = df.rename( columns={"NAME":"name_full","B01003_001E":"population"})
    
    df['population'] = pd.to_numeric(df['population'],errors='coerce')
    # set to NaN where we see sentinel values of missing (large neg ints)
    df['population'] = df['population'].mask(df['population'] < -1e6)
    missing_pop = df['population'].isna().sum()
    if missing_pop:
        print("Error: some counties are missing values")
        print(df.loc[df['population'].isna()])
        assert False,"missing some county populations"
    assert df['name_full'].str.endswith(" County, California").sum() == TOTAL_COUNTIES, "Some names did not end with County, California"
    df["name_short"] = df["name_full"].str.replace(" County, California","")
    df["county_fips"] = df['state'] + df['county']
    assert df["county_fips"].nunique() == TOTAL_COUNTIES,"Non unique state-county values"
    bad_lengths = (df["county_fips"].str.len()!=5).sum()
    assert bad_lengths==0,"There were some fips codes not length 5"
    print(f"Example first row:\ndf {df.iloc[0,:]}")
    RAW.mkdir(parents = True, exist_ok = True)
    path = RAW / f"acs{args.year}_county_counts_ca_raw.csv"
    df.to_csv(path,index = False)
    print(f"wrote {path}")


if __name__=='__main__':
    main()