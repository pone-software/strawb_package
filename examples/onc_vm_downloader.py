#!/usr/bin/python3

# This examples shows who to download files from the ONC server
import strawb

import os
import pandas as pd
import datetime
from dateutil.relativedelta import relativedelta
import numpy as np


def download_module(dev_code):
    """Download the files of interest for a module over the entire period of STRAW-b
    by wrapping 'download_files_of_interest'.
    PARAMETER
    ---------
    dev_code: str
        e.g. TUMSTANDARDMODULE001
    """

    # get the list of month from start_time to end_time
    start_time = datetime.date(2020, 10, 1)
    end_time = datetime.datetime.now()
    start_time_list = pd.date_range(start_time, end_time, freq='MS')
    end_time_list = pd.date_range(start_time + relativedelta(months=+1),
                                  end_time + relativedelta(months=+1),
                                  freq='MS') - np.timedelta64(1, 's')
    date_list = zip(start_time_list, end_time_list)

    for date_from, date_to in date_list:
        download_files_of_interest(dev_code, date_from, date_to)


def download_files_of_interest(dev_code, date_from, date_to):
    """Download the files of interest of a module in between a time period. Excludes unwanted, i.e. onc log files.
    PARAMETER
    ---------
    dev_code: str
        e.g. TUMSTANDARDMODULE001
    date_from: datetime
    date_to: datetime
    """
    dev_path = os.path.join(strawb.Config.raw_data_dir,
                            dev_code.lower())

    # create ONCDownloader
    downloader_i = strawb.ONCDownloader(showInfo=False,
                                        outPath=os.path.join(dev_path, date_from.strftime("%Y_%m"))
                                        )

    # downloader_i.start(filters=filters, allPages=True)  # start the download in a thread (background)
    filters = {'deviceCode': dev_code,
               'dateFrom': date_from.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
               'dateTo': date_to.strftime("%Y-%m-%dT%H:%M:%S.999Z"),
               'extension': 'hdf5'}

    for extension_i in ['hdf5', 'raw', 'png']:  # 'hld'
        filters['extension'] = extension_i
        downloader_i.download_file(filters=filters, allPages=True)  # start the download in a thread (background)

    filters.pop('extension')

    # Time Over Threshold Data
    for data_product_i in ['PMTTOT', 'LIDARTOT', 'MTTOT']:
        filters['dataProductCode'] = data_product_i
        downloader_i.download_file(filters=filters, allPages=True)  # start the download in a thread (background)


def main():
    # # Get the dev_codes
    # get all possible dev_codes
    dev_codes = set([i['dev_code'] for i in strawb.module_onc_id.values()])
    # subtract not deployed dev_codes
    dev_codes = dev_codes.difference(['TEST', 'UNITTEST', 'TUMSTANDARDMODULE002', 'TUMSTANDARDMODULE003'])

    for i in dev_codes:
        download_module(i)


if __name__ == "__main__":
    # execute only if run as a script
    main()
