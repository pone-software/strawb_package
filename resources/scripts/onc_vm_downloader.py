#!/usr/bin/python3
# coding: utf-8

""" WHAT THIS SCRIPT DOES
This script downloads all files from the ONC server for the all dev_codes defined in `strawb.dev_codes_deployed`
It will download it with the following structure:
  <strawb.Config.raw_data_dir>
      <strawb.Config.raw_data_dir>/<dev_codes[0]>  # i.e. tumlidar001
          <strawb.Config.raw_data_dir>/<dev_codes[0]>/2020_10
              # all files from October
          <strawb.Config.raw_data_dir>/<dev_codes[0]>/2020_11
          ...
      <strawb.Config.raw_data_dir>/<dev_codes[1]>
      ...
In addition, it saves the metadata from the ONC server for all files under: `strawb.Config.pandas_file_sync_db`
This file can be imported with: `pandas.read_pickle(strawb.Config.pandas_file_sync_db)` again.
"""

import datetime
import strawb


def main():
    onc_downloader = strawb.ONCDownloader()
    pd_result = onc_downloader.download_structured(dev_codes=strawb.dev_codes_deployed,
                                                   extensions=None,
                                                   date_from='strawb_all',
                                                   date_to=None,
                                                   download=True,
                                                   )

    # store information in a pandas-file
    pd_result.to_pickle(strawb.Config.pandas_file_sync_db, protocol=4)  # protocol=4 compatible with python>=3.4


# execute only if run as a script
if __name__ == "__main__":
    print(f'Start sync: {datetime.datetime.utcnow().isoformat()}')
    main()
    print(f'Sync ended: {datetime.datetime.utcnow().isoformat()}')
