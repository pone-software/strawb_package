import io
import os
from contextlib import redirect_stdout

import dateutil.parser
import h5py
import pandas

import strawb

from strawb import ONCDownloader


class DataProductDownloader(ONCDownloader):
    def download_file(self, dateFrom, dateTo, locationCode, deviceCategoryCode, deviceCode, dataProductCode, **kwargs):
        if isinstance(dateFrom, str):
            dateFrom = dateutil.parser.parse(dateFrom)
        if isinstance(dateTo, str):
            dateTo = dateutil.parser.parse(dateTo)

        filters = {
            'dateFrom': f'{dateFrom.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]}Z',
            'dateTo': f'{dateTo.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]}Z',
            'locationCode': locationCode,
            'deviceCategoryCode': deviceCategoryCode,
            'dataProductCode': dataProductCode,
            **kwargs}

        out_path = os.path.join(strawb.Config.raw_data_dir,
                                deviceCode.lower(),
                                dateFrom.strftime('%Y_%m'))

        dat_pro = self.orderDataProduct(
            downloadResultsOnly=False,
            includeMetadataFile=False,
            filters=filters,
            outPath=out_path)

        # update filters, was changed for orderDataProduct only
        filters.update({'deviceCode': deviceCode,
                        'dateFrom': dateFrom,
                        'dateTo': dateTo})
        df = self.data_pro_return2df(dat_pro, filters)

        return df, dat_pro

    @staticmethod
    def data_pro_return2df(data_pro, filters):
        df = pandas.DataFrame(data={  # 'archiveLocation', 'archivedDate', 'compression',
            'dataProductCode': filters['dataProductCode'],
            'dateFrom': filters['dateFrom'],
            'dateTo': filters['dateTo'],
            'deviceCode': filters['deviceCode'],
            'fileSize': [dat_i['size'] for dat_i in data_pro['downloadResults']],
            'filename': [dat_i['file'] for dat_i in data_pro['downloadResults']],
            'fullPath': [dat_i['fullPath'] for dat_i in data_pro['downloadResults']],
            'outPath': [dat_i['outPath'] for dat_i in data_pro['downloadResults']],
            'uncompressedFileSize': [dat_i['size'] for dat_i in data_pro['downloadResults']],
            'synced': [dat_i['downloaded'] for dat_i in data_pro['downloadResults']]})

        df.set_index('fullPath', inplace=True, drop=False)
        return df


def update_nc_attrs(df):
    # write attributes to file, can be used to restore metadata
    for i in df[df.fullPath.str.endswith('.nc')].to_dict('records'):
        with h5py.File(i['fullPath'], 'a') as f:
            update_dict = {}
            for j in ['dateFrom', 'dateTo']:
                update_dict.update({j: f'{i[j].strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]}Z'})
            for j in ['deviceCode', 'dataProductCode']:
                update_dict.update({j: i[j]})

            for j in update_dict:
                if j not in dict(f.attrs):
                    f.attrs.update({j: update_dict[j]})


def update_db(df2add, db_or_filename):
    df2add = df2add.copy()  # add_new_db pops items
    if isinstance(db_or_filename, str):
        if not os.path.exists(db_or_filename):
            db = strawb.SyncDBHandler(file_name=db_or_filename,
                                      load_db=False)
            db.save_db()
        else:
            db = strawb.SyncDBHandler(file_name=db_or_filename)
    else:
        db = db_or_filename

    if db.dataframe is None:
        db.dataframe = df2add
    else:
        db.add_new_db(df2add)

    db.save_db()


def wraper_download_multiple_files(t_0, dt, filters):
    #     print(t_0, t_0+dt-dateutil.relativedelta.relativedelta(microseconds=1000))
    filters.update({'dateFrom': t_0,
                    'dateTo': t_0 + dt - dateutil.relativedelta.relativedelta(microseconds=1000)})
    f = io.StringIO()
    with redirect_stdout(f):
        df_i, dat_pro = download_file(**filters)
    update_nc_attrs(df_i)
    return df_i, dat_pro, f.getvalue()