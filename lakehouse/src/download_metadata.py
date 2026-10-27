"""Summary

Downloads the metadata JSON object associated with a DHCS dataset
after reading the name field as the API ID from the
JSON object when doing a key word search for a dataset

Output: outfile
"""

import argparse
from datetime import datetime
import json

from pathlib import Path

import requests

def main():
    ap = argparse.ArgumentParser()

    ap.add_argument("--fetch_url",
                    default="https://publish.data.ca.gov/api/3/action/package_show?id=",
                    help="The base URL string. Needs an API ID endpoint to append.")
    ap.add_argument("--api_id",required=True,
                    help="The API ID for the dataset which is shown as name in the"
                         " JSON response of a ca.data.gov search")
    ap.add_argument("--output",required=True,
                    help="Name of the JSON format output file.")
    args = ap.parse_args()
    url = args.fetch_url + args.api_id

    with requests.get(url,stream=True) as response:
        response.raise_for_status()
        json_obj = response.json()
        metadata_modified = json_obj['result']['metadata_modified']
        current_time =  datetime.now().isoformat()
        with open(args.output,'w') as file:
            json.dump(json_obj,file,indent=4)
        orig_path = Path(args.output)
        prefix = metadata_modified+"_"+current_time
        timestamped_filename = orig_path.with_name(f"{prefix}_{orig_path.name}")
        with open(timestamped_filename, 'w') as file:
            json.dump(json_obj, file, indent=4)




if __name__=='__main__':
    main()