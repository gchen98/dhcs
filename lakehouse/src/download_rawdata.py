"""Summary

Downloads raw data from url field in the metadata JSON object under result->resources

Output: outfile
"""

import sys
import argparse
import json
import shutil
import hashlib
from datetime import datetime,UTC
from common import get_retry_session

from pathlib import Path

import requests

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metadata",required=True,help="path to JSON formatted metadata file for dataset")
    ap.add_argument("--file_id",required=True,help="UUID for the file. Under JSON field result->resources[]->id")
    ap.add_argument("--output",required=True,help="path of the raw output file")
    ap.add_argument("--retries", type=int, default=5,
                    help="Number of times to retry API")
    ap.add_argument("--timeout", type=int, default=5,
                    help="Number of second for timeout to API")
    args = ap.parse_args()

    with open(args.metadata,"r",encoding='utf-8') as file:
        metadata = json.load(file)

    resource_list = metadata['result']['resources']
    session = get_retry_session(args.retries)
    try:
        for resource in resource_list:
            if args.file_id == resource['id']:
                url = resource['url']
                checksum = resource['hash']
                enable_hash = len(checksum)>0
                metadata_modified_obj = datetime.fromisoformat(metadata['result']['metadata_modified'])
                metadata_modified = metadata_modified_obj.strftime("%Y%m%d%H%M%S")

                hasher = hashlib.md5()
                with session.get(url, stream=True,timeout=args.timeout) as response:
                    response.raise_for_status()
                    with open(args.output, 'wb') as file:
                        for chunk in response.iter_content(chunk_size=8192):
                            file.write(chunk)
                            if enable_hash:
                                hasher.update(chunk)
                        if enable_hash:
                            computed_hash = hasher.hexdigest()
                            assert checksum == computed_hash,f"{checksum} does not match computed hash {computed_hash}"
                    # make a second copy
                    orig_path = Path(args.output)
                    current_time_obj = datetime.now(UTC)
                    current_time = current_time_obj.strftime("%Y%m%d%H%M%S")
                    prefix = metadata_modified + "_" + current_time
                    timestamped_filename = str(orig_path.with_name(f"{prefix}_{orig_path.name}"))
                    shutil.copy2(args.output,timestamped_filename)
    except Exception as e:
        sys.exit(f"File with id {args.file_id} could not be saved because of {e}!")




if __name__=='__main__':
    main()