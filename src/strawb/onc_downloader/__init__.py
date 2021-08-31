# Authors: Kilian Holzapfel <kilian.holzapfel@tum.de>
import datetime
import os
import threading

import pandas
from onc.onc import ONC  # pip install onc; https://pypi.org/project/onc/

import strawb
from strawb.config_parser.__init__ import Config


class ONCDownloader(ONC):
    def __init__(self, token=None, outPath=None, download_threads=None, **kwargs):
        """ A wrapper class for the basic ONC module. It adds the storage of the result and can download the file inside
        a thread and therefore puts it in the background.

        PARAMETER
        ---------
        token: str, optional
            The personal access token from ONC 2.0. If None (default), it's the parameter from the config file.
        outPath: str, optional
            The path in which the downloads are saved. If None (default), it's the parameter from the config file.
        download_threads: int, optional
            Defines the number of thread for the download. If None (default) it uses the specified 'threads' form the
            config-file.
        kwargs: dict, optional
            parsed to ONC package initialisation.
        """
        if outPath is None:
            outPath = Config.raw_data_dir

        if token is None:
            token = Config.onc_token

        if download_threads is None:
            download_threads = Config.onc_download_threads

        ONC.__init__(self, token, outPath=outPath, download_threads=download_threads, **kwargs)

        self.filters = {}
        self.result = {}

        self.download_thread = threading.Thread(target=self.download_file)

    def start(self, **kwargs):
        """Starts the download in background (thread). The rests is similar to download_file"""
        if not self.download_thread.is_alive():
            self.download_thread = threading.Thread(target=self.download_file, kwargs=kwargs)
            self.download_thread.start()

    def download_file(self, **kwargs):
        """ Downloads the files and stores the result internally."""
        # print(f'Download in directory: {self.outPath}')
        self.result = self.getDirectFiles(**kwargs)
        for res_i in self.result['downloadResults']:
            if 'file' in res_i:
                res_i['file'] = os.path.abspath(os.path.join(self.outPath, res_i['file']))

    def get_files_for_dev_codes(self, dev_codes: list, date_from: datetime, date_to: datetime,
                                print_stats: bool = True):
        """
        Get all available files on the ONC server for the dev_code and the specified date.
        Parameters
        ---------
        dev_codes: list(str),
            a valid ONC deviceCode
        date_from: datetime,
            e.g. datetime.date(2020, 10, 1)
        date_to: datetime,
            e.g. datetime.datetime.now()
        print_stats: bool, optional
            if the function returns stats
        Returns
        -------
        result: dict
            A dict with at least the key 'files' which is a list of all available files. Each file is a separated dict.
        """

        # get the result dict with all available files
        result = {'files': []}

        if print_stats:
            print('Obtain files from:')
        for dev_i in dev_codes:
            filters = {
                'deviceCode': dev_i,
                'dateFrom': date_from.strftime("%Y-%m-%dT%H:%M:%S.000Z"),  # '2020-10-20T00:00:00.000Z',
                'dateTo': date_to.strftime("%Y-%m-%dT%H:%M:%S.999Z"),  # '2021-10-21T00:00:10.000Z',
                'returnOptions': 'all'}
            result_i = self.getListByDevice(filters=filters, allPages=True)
            result['files'].extend(result_i['files'])

            n_files = len(result_i["files"])
            if print_stats:
                print(f' {dev_i}: {n_files} files')

        if print_stats:
            print(f'In total: {len(result["files"])} files')

        return result

    def download_structured(self, dev_codes=None, date_from=None, date_to=None,
                            extensions=None,  # data_product_names=None,
                            min_file_size=0, max_file_size=.75e9, download=True):
        """
        This function syncs files from the onc server for the specified dev_codes. The files are organized in different
        directories by <Config.raw_data_dir>/<dev_code>/<year>_<month>/<file_name>.
        Files can be filtered by the file size, extensions,
        PARAMETERS
        ----------
        date_from: str, datetime, optional
            Takes on of the following:
            - None: takes the today-1day;
            - str in isoformat: '2021-08-31T14:33:25.209715';
            - str: 'strawb_all' to get data since STRAWb went online
            - timedelta: date_from = now - timedelta
            - a datetime
        date_to: str, datetime, timedelta, optional
            Takes on of the following:
            - None: takes the today;
            - str in isoformat: '2021-08-31T14:33:25.209715';
            - timedelta: date_to = date_from + timedelta
            - a datetime
        download: bool, optional
            weather or not to download the files. True (default) downloads the files, and
            False just checks which pass the filter.
        dev_codes: list, optional
            List with dev_codes for which the files are downloaded. None (default), takes all deployed STRAWb dev_codes
        extensions: list[str], optional
            A list of extensions to download. If None, it takes all possible extensions for STRAWb,
            i.e. ['hdf5', 'hld', 'raw', 'png', 'txt'].
        :return:
        """
        # TODO: add extensions=None, data_product_names
        if dev_codes is None:
            dev_codes = strawb.dev_codes_deployed

        if date_from is None:
            date_from = datetime.datetime.now() - datetime.timedelta(days=1)
        elif date_from == 'strawb_all':
            date_from = datetime.date(2020, 10, 1)
        elif isinstance(date_from, datetime.datetime):
            date_from = date_from
        elif isinstance(date_from, datetime.timedelta):
            date_from = datetime.datetime.now() - date_from
        else:
            date_from = datetime.datetime.fromisoformat(date_from)

        if date_to is None:
            date_to = datetime.datetime.now()
        elif isinstance(date_to, datetime.datetime):
            date_to = date_to
        elif isinstance(date_to, datetime.timedelta):
            date_to = date_from + date_to
        else:
            date_to = datetime.datetime.fromisoformat(date_to)

        # get all possible files from the devices
        result = self.get_files_for_dev_codes(dev_codes, date_from=date_from, date_to=date_to)

        # convert the list to a DataFrame for easier modifications
        pd_result = pandas.DataFrame.from_dict(result['files'])

        # convert the datetime columns accordingly
        for key_i in ['archivedDate', 'modifyDate', 'dateFrom', 'dateTo']:
            pd_result[key_i] = pandas.to_datetime(pd_result[key_i])

        # add a 'outPath' column, to specify the outPath per file
        pd_result['outPath'] = strawb.Config.raw_data_dir + '/'
        pd_result['outPath'] += pd_result['deviceCode'].str.lower() + '/' + pd_result['dateFrom'].dt.strftime('%Y_%m')

        # mask by file size
        mask = min_file_size <= pd_result['fileSize']
        mask &= pd_result['fileSize'] <= max_file_size

        # # Select dataProducts
        # get more information for the existing dataProductCodes
        dataProduct_all = []
        if extensions is not None:  # and data_product_names is not None
            for i in pd_result['dataProductCode'].unique():
                dataProduct_all.extend(self.getDataProducts({'dataProductCode': i}))

        if extensions is None:
            pass
        else:
            mask_extensions = mask.copy()*0
            if isinstance(extensions, str):
                extensions = [extensions]

            for i in extensions:
                mask_extensions += pd_result['filename'].str.endswith(i)
            mask &= mask_extensions
        # if data_product_names is None:
        #     pass
        # else:
        #     dataProduct_all = []
        #     for i in pd_result['dataProductCode'].unique():
        #         dataProduct_all.extend(self.getDataProducts({'dataProductCode': i}))
        #     dataProduct_select = [i for i in dataProduct_all if i['dataProductName'] in data_product_names]
        #     mask &= pd_result['dataProduct'] == dataProduct_select

        print(f'Exclude {len(mask[~mask])} files')
        if download:
            # reduce it with the mask and the columns to 'filename', 'outPath'
            pd_result_masked = pd_result[mask][['filename', 'outPath']]
            filters_or_result = dict(files=pd_result_masked.to_dict(orient='records'))
            self.getDirectFiles(filters_or_result=filters_or_result)

        # add column of which files are synced
        pd_result['synced'] = mask

        # rename 'outPath' to 'fullPath' and cal. the full path
        pd_result = pd_result.rename(columns={"outPath": "fullPath"})
        pd_result["fullPath"] += '/' + pd_result['filename']

        return pd_result
