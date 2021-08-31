#!/usr/bin/python3
# coding: utf-8

""" WHAT THIS SCRIPT DOES
This script downloads all files from the ONC server for the all dev_codes defined in `strawb.dev_codes_deployed`
It will download it with the following structure:
  $strawb.Config.raw_data_dir$
      $strawb.Config.raw_data_dir$/$dev_codes[0]$  # i.e. tumlidar001
          $strawb.Config.raw_data_dir$/$dev_codes[0]$/2020_10
              # all files from October
          $strawb.Config.raw_data_dir$/$dev_codes[0]$/2020_11
          ...
      $strawb.Config.raw_data_dir$/$dev_codes[1]$
      ...
In addition, it saves the metadata from the ONC server for all files under: `strawb.Config.pandas_file_sync_db`
This file can be imported with: `pandas.read_pickle(strawb.Config.pandas_file_sync_db)` again.
"""

import datetime
import pandas as pd
import strawb

onc_downloader = strawb.ONCDownloader()


def main():
    # get all possible files from the devices
    result = onc_downloader.get_files_for_dev_codes(strawb.dev_codes_deployed,
                                                    date_from=datetime.date(2020, 10, 1),
                                                    date_to=datetime.datetime.now())

    # convert the list to a DataFrame for easier modifications
    pd_result = pd.DataFrame.from_dict(result['files'])

    # convert the datetime columns accordingly
    for key_i in ['archivedDate', 'modifyDate', 'dateFrom', 'dateTo']:
        pd_result[key_i] = pd.to_datetime(pd_result[key_i])

    # add a 'outPath' column, to specify the outPath per file
    pd_result['outPath'] = strawb.Config.raw_data_dir + '/'
    pd_result['outPath'] += pd_result['deviceCode'].str.lower() + '/' + pd_result['dateFrom'].dt.strftime('%Y_%m')

    # mask by file size
    mask = pd_result['fileSize'] < .75e9
    print(f'Exclude {len(mask[~mask])} files')

    # ## Select dataProducts
    # dataProduct_all = []
    # for i in pd_result['dataProductCode'].unique():
    #     print(i)
    #     dataProduct_all.extend(onc.getDataProducts({'dataProductCode': i}))
    #
    # dataProduct_select = [i for i in dataProduct_all if i['extension'] in ['hdf5', 'hld', 'raw', 'png']]
    # dataProduct_select.extend(
    #     [i for i in dataProduct_all if i['extension'] == 'txt' and i['dataProductName'] != 'Log File'])

    # reduce it with the mask and the columns to 'filename', 'outPath'
    pd_result_masked = pd_result[mask][['filename', 'outPath']]
    filters_or_result = dict(files=pd_result_masked.to_dict(orient='records'))
    onc_downloader.getDirectFiles(filters_or_result=filters_or_result)

    # add column of which files are synced
    pd_result['synced'] = mask

    # rename 'outPath' to 'fullPath' and cal. the full path
    pd_result = pd_result.rename(columns={"outPath": "fullPath"})
    pd_result["fullPath"] += '/' + pd_result['filename']

    # store information in a pandas-file
    pd_result.to_pickle(strawb.Config.pandas_file_sync_db, protocol=4)  # protocol=4 compatible with python>=3.4


# execute only if run as a script
if __name__ == "__main__":
    print(f'Start sync: {datetime.datetime.utcnow().isoformat()}')
    main()
    print(f'Sync ended: {datetime.datetime.utcnow().isoformat()}')
