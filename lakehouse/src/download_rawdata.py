"""Summary

Downloads raw data from url field in the metadata JSON object under result->resources

Output: outfile
"""

import argparse
import json
import shutil
from datetime import datetime

from pathlib import Path

import requests

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metadata",required=True,help="path to JSON formatted metadata file for dataset")
    ap.add_argument("--file_id",required=True,help="UUID for the file. Under JSON field result->resources[]->id")
    ap.add_argument("--output",required=True,help="path of the raw output file")
    args = ap.parse_args()

    with open(args.metadata,"r",encoding='utf-8') as file:
        metadata = json.load(file)

    resource_list = metadata['result']['resources']
    for resource in resource_list:
        if args.file_id == resource['id']:
            url = resource['url']
            metadata_modified = resource['metadata_modified']
            with requests.get(url, stream=True) as response:
                response.raise_for_status()
                with open(args.output, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
            # make a second copy
            orig_path = Path(args.output)
            current_time = datetime.now().isoformat()
            prefix = metadata_modified + "_" + current_time
            timestamped_filename = str(orig_path.with_name(f"{prefix}_{orig_path.name}"))
            shutil.copy2(args.output,timestamped_filename)



if __name__=='__main__':
    main()