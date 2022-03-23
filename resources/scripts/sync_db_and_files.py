#!/usr/bin/python3
# coding: utf-8

"""
WHAT THIS SCRIPT DOES
---------------------
1. This script downloads all files from the ONC server
2. it saves the metadata from the ONC server for all files under:
   >>> import strawb.Config
   >>> strawb.Config.pandas_file_sync_db
"""
import argparse
import datetime

import strawb


def parser_args():
    parser = argparse.ArgumentParser(description='Sync local DB with the ONC DB and if set download missing files.')
    parser.add_argument('--download', action='store_true',
                        help='If set, download files. (default: %(default)s)')  # if set, args.download is True
    parser.add_argument('-s', '--start', type=str, default=None,
                        help="Defines the start time of the query. Supports: \n"
                             " - str in isoformat: '2021-08-31T14:00:00.000' or '2021-08-31T14:00:00.000Z' \n"
                             " - str: 'strawb_all' to get data since STRAWb went online: 01.10.2020 \n"
                             " - not set (default) yesterday")
    parser.add_argument('-t', '--to', type=str, default=None,
                        help="Defines the end time of the query. Supports: \n"
                             " - str in isoformat: '2021-08-31T14:30:00.000' or '2021-08-31T14:30:00.000Z'\n"
                             " - not set (default) today")
    parser.add_argument('-d', '--devcode', type=str,
                        default=None, nargs='+', metavar='DEVCODE',
                        choices=['ONCMJB016', *list(strawb.dev_codes_deployed)],
                        help="Defines one or multiple dev_code(s) which should be synced. "
                             "The dev_codes are: %(choices)s")
    parser.add_argument('-e', '--extensions', type=str, default=None, nargs='+',
                        help="Defines the file extensions which should be synced,"
                             "e.g.  ['hdf5', 'hld', 'raw', 'png', 'txt'].")
    parser.add_argument('-l', '--min', type=float, default=0,
                        help="Defines the minimum file size in Byte which should be synced, e.g.  1024 [=1kB] "
                             "(default: %(default)s)")
    parser.add_argument('-m', '--max', type=float, default=.75e9,
                        help="Defines the minimum file size in Byte which should be synced, e.g.  1e6 [~1MB] "
                             "(default: %(default)s)")

    return parser.parse_args()


def main(download=False, dev_codes=None, date_from=None, date_to=None,
         extensions=None, min_file_size=0, max_file_size=.75e9):
    """
    This function downloads all files from the ONC server for the all dev_codes defined in `strawb.dev_codes_deployed`
    It will download it with the following structure:
      <strawb.Config.raw_data_dir>
          <strawb.Config.raw_data_dir>/<dev_codes[0]>  # i.e. tumlidar001
              <strawb.Config.raw_data_dir>/<dev_codes[0]>/2020_10
                  # all files from October
              <strawb.Config.raw_data_dir>/<dev_codes[0]>/2020_11
              ...
          <strawb.Config.raw_data_dir>/<dev_codes[1]>
          ...

    In addition, it saves/updateds the metadata to the local data base (DB) with the data from the ONC server for all
    files under: `strawb.Config.pandas_file_sync_db`
    This file DB be imported again with:
    >>> import strawb
    >>> db = strawb.SyncDBHandler(file_name='Default')
    >>> db.dataframe
    """

    db_handler = strawb.SyncDBHandler(file_name='Default')  # with no dataframe loaded

    # sync all if the db doesn't exist
    if db_handler.dataframe is None:
        date_from = 'strawb_all'

    db_handler.load_onc_db(output=True,
                           dev_codes=dev_codes,
                           date_from=date_from, date_to=date_to,
                           min_file_size=min_file_size, max_file_size=max_file_size,
                           add_hdf5_attributes=True,
                           add_file_version=True,
                           add_dataframe=True,
                           download=download,
                           extensions=extensions)

    db_handler.save_db()


# execute only if run as a script
if __name__ == "__main__":
    args = parser_args()

    print(f'Start sync: {datetime.datetime.utcnow().isoformat()}')
    main(download=args.download,
         dev_codes=args.devcode,
         date_from=args.start, date_to=args.to,
         extensions=args.extensions,
         min_file_size=int(args.min), max_file_size=int(args.max),
         )
    print(f'Sync ended: {datetime.datetime.utcnow().isoformat()}')
