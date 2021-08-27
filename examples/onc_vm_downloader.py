#!/usr/bin/python3
# coding: utf-8

# This examples shows who to download files from the ONC server

import datetime
import pandas as pd
import strawb

onc_downloader = strawb.ONCDownloader()


def main():
    # get all possible files from the devices
    result = onc_downloader.get_files_for_dev_code(strawb.dev_codes_deployed,
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


# execute only if run as a script
if __name__ == "__main__":
    print('Start sync')
    main()
    print('Sync ended')
