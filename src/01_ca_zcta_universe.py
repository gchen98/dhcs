"""Build the CA ZCTA universe: which ZCTAs fall in California, plus land area.

Inputs (already downloaded to data/raw):
  tab20_zcta520_county20_natl.txt  - 2020 ZCTA-to-county relationship file
  2024_Gaz_zcta_national.txt       - 2024 gazetteer (ALAND_SQMI, centroid lat/lon)

A ZCTA is assigned to CA if any part of it falls in a state-06 county. ZCTAs
straddling the state line are kept but flagged (ca_land_share) so they can be
dropped or downweighted later.

Output: data/interim/ca_zcta_universe.csv
"""

import pandas as pd
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
INTERIM = Path(__file__).resolve().parents[1] / "data" / "interim"

rel = pd.read_csv(
    RAW / "tab20_zcta520_county20_natl.txt",
    sep="|",
    dtype=str,
    encoding="utf-8-sig",
)
rel = rel.dropna(subset=["GEOID_ZCTA5_20", "GEOID_COUNTY_20"])
rel["AREALAND_PART"] = pd.to_numeric(rel["AREALAND_PART"], errors="coerce").fillna(0)
rel["state"] = rel["GEOID_COUNTY_20"].str[:2]

# land area of each ZCTA that sits in CA vs. anywhere
by_zcta = rel.groupby("GEOID_ZCTA5_20")["AREALAND_PART"].sum().rename("land_total")
ca_land = (
    rel[rel["state"] == "06"]
    .groupby("GEOID_ZCTA5_20")["AREALAND_PART"]
    .sum()
    .rename("land_ca")
)

ca = pd.concat([ca_land, by_zcta], axis=1, join="inner").reset_index()
ca = ca.rename(columns={"GEOID_ZCTA5_20": "zcta"})
ca["ca_land_share"] = (ca["land_ca"] / ca["land_total"]).where(ca["land_total"] > 0)

# counties touched, for later regional joins
counties = (
    rel[(rel["state"] == "06") & (rel["GEOID_ZCTA5_20"].isin(ca["zcta"]))]
    .sort_values("AREALAND_PART", ascending=False)
    .groupby("GEOID_ZCTA5_20")
    .agg(
        primary_county_fips=("GEOID_COUNTY_20", "first"),
        primary_county_name=("NAMELSAD_COUNTY_20", "first"),
        n_counties=("GEOID_COUNTY_20", "nunique"),
    )
    .reset_index()
    .rename(columns={"GEOID_ZCTA5_20": "zcta"})
)
ca = ca.merge(counties, on="zcta", how="left")

gaz = pd.read_csv(RAW / "2024_Gaz_zcta_national.txt", sep="\t", dtype={"GEOID": str})
gaz.columns = [c.strip() for c in gaz.columns]
gaz = gaz.rename(
    columns={"GEOID": "zcta", "ALAND_SQMI": "aland_sqmi", "INTPTLAT": "lat", "INTPTLONG": "lon"}
)
ca = ca.merge(gaz[["zcta", "aland_sqmi", "lat", "lon"]], on="zcta", how="left")

ca = ca.sort_values("zcta").reset_index(drop=True)
INTERIM.mkdir(parents=True, exist_ok=True)
ca.to_csv(INTERIM / "ca_zcta_universe.csv", index=False)

print(f"CA ZCTAs (any CA land): {len(ca)}")
print(f"  wholly in CA (share >= 0.999): {(ca['ca_land_share'] >= 0.999).sum()}")
print(f"  straddling state line:         {(ca['ca_land_share'] < 0.999).sum()}")
print(f"  missing gazetteer land area:   {ca['aland_sqmi'].isna().sum()}")
print(ca.head())
