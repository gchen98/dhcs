"""Summary

Downloads the metadata JSON object associated with a DHCS dataset
after reading the name field as the API ID from the
JSON object when doing a key word search for a dataset

Output: outfile
"""

import argparse

from requests.exceptions import JSONDecodeError
from datetime import datetime,UTC
from common import get_retry_session
import json
import sys
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
    ap.add_argument("--retries", type=int, default=5,
                    help="Number of times to retry API")
    ap.add_argument("--timeout", type=int, default=5,
                    help="Number of second for timeout to API")
    args = ap.parse_args()
    url = args.fetch_url + args.api_id

    session = get_retry_session(args.retries)
    try:
        with session.get(url,timeout=args.timeout) as response:
            try:
                json_obj = response.json()
            except JSONDecodeError as json_err:
                sys.exit(f"JSON could not be decoded status code "
                         f"({response.status_code}) response is  {response.text[:1000]}")
            if 'success' not in json_obj:
                sys.exit("Invalid JSON, missing success field")
            else:
                success_status = json_obj['success']
            if not success_status:
                sys.exit(f"Success status on response was false: {json_obj['error']}")
            response.raise_for_status()
            returned_name = json_obj['result']['name']
            assert returned_name == args.api_id, f"JSON response has a API ID of {returned_name}!"
            metadata_modified_obj = datetime.fromisoformat(json_obj['result']['metadata_modified'])
            metadata_modified = metadata_modified_obj.strftime("%Y%m%d%H%M%S")
            current_time_obj =  datetime.now(UTC)
            current_time = current_time_obj.strftime("%Y%m%d%H%M%S")
            with open(args.output,'w') as file1:
                json.dump(json_obj,file1,indent=4)
                orig_path = Path(args.output)
                prefix = metadata_modified+"_"+current_time
                timestamped_filename = orig_path.with_name(f"{prefix}_{orig_path.name}")
            with open(timestamped_filename, 'w') as file2:
                json.dump(json_obj, file2, indent=4)

    except Exception as e:
        sys.exit(f"Dataset with id {args.api_id} could not be saved! because of {e}")





if __name__=='__main__':
    main()