# Authors: Kilian Holzapfel <kilian.holzapfel@tum.de>
import datetime
import os

import numpy as np
import pandas
from onc.onc import ONC  # pip install onc; https://pypi.org/project/onc/
from onc.util.util import add_docs

import strawb
from strawb.tools import human_size


class ONCDownloader(ONC):
    def __init__(self, token=None, outPath=None, download_threads=None, **kwargs):
        """ A wrapper class for the basic ONC module. Which adds: structured_download and the
        Config parameters as default.

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
            outPath = strawb.Config.raw_data_dir

        if token is None:
            token = strawb.Config.onc_token

        if download_threads is None:
            download_threads = strawb.Config.onc_download_threads

        ONC.__init__(self, token, outPath=outPath, download_threads=download_threads, **kwargs)

        self.result = {}

    @add_docs(ONC.getDirectFiles)
    def getDirectFiles(self, filters_or_result: dict = None, overwrite: bool = False, allPages: bool = False):
        self.result = ONC.getDirectFiles(self, filters_or_result=filters_or_result,
                                         overwrite=overwrite,
                                         allPages=allPages)

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

    @staticmethod
    def _read_str_as_timedelta_(string):
        """Try to interpret the string as float which will be used as timedelta in unit days.
        Or as a isofromat datetime string."""
        try:
            d_time = datetime.timedelta(days=float(string))
        except ValueError or TypeError:
            return string
        else:
            return abs(d_time)

    def get_files_structured(self, dev_codes=None, date_from=None, date_to=None,
                             extensions=None, min_file_size=0, max_file_size=.75e9):
        """
        This function gets the dataframe with all metadata of files from the onc server for the specified dev_code(s).
        It also adds a path 'fullPath' to each file. The files are organized in different directories by
        <Config.raw_data_dir>/<dev_code>/<year>_<month>/<file_name>. Files can be filtered by the file size,
        extensions, and date.
        PARAMETERS
        ----------
        date_from: str, datetime, optional
            Takes on of the following:
            - None: takes the today-1day;
            - str in isoformat: '2021-08-31T14:33:25.209715';
            - str in isoformat with Z: '2021-08-31T14:33:25.209715Z';
            - str: 'strawb_all' to get data since STRAWb went online: 01.10.2020
            - str: a float, interpreted as datetime.timedelta(days=float(string)) and used like 'timedelta'
            - timedelta: date_from = now - abs(timedelta)
            - a datetime
        date_to: str, datetime, timedelta, optional
            Takes on of the following:
            - None: takes the today;
            - str in isoformat: '2021-08-31T14:33:25.209715';
            - str in isoformat with Z: '2021-08-31T14:33:25.209715Z';
            - str: a float, interpreted as datetime.timedelta(days=float(string)) and used like 'timedelta'
            - timedelta: date_to = date_from + abs(timedelta)
            - a datetime
        dev_codes: Union[list, str], optional
            List with dev_codes or str for a single dev_code for which the files are downloaded.
            None (default), takes all deployed STRAWb dev_codes
        extensions: list[str], optional
            A list of extensions to download. If None, it takes all possible extensions for STRAWb,
            i.e. ['hdf5', 'hld', 'raw', 'png', 'txt'].
        min_file_size: int, float, optional
            defines the minimum file size
        max_file_size: int, float, optional
            defines the maximum file size
        """
        # TODO: finalise commented part `data_product_names`
        if dev_codes is None:
            dev_codes = strawb.dev_codes_deployed
        elif isinstance(dev_codes, str):  # dev codes must be a list
            dev_codes = [dev_codes]

        date_from = self._read_str_as_timedelta_(date_from)  # try to read it as float -> timedelta
        if date_from is None:
            date_from = datetime.datetime.now() - datetime.timedelta(days=1)
        elif date_from == 'strawb_all':
            date_from = datetime.date(2020, 10, 1)
        elif isinstance(date_from, datetime.datetime):
            date_from = date_from
        elif isinstance(date_from, datetime.timedelta):
            date_from = datetime.datetime.now() - abs(date_from)
        else:
            date_from = datetime.datetime.fromisoformat(date_from.rstrip('Z'))

        date_to = self._read_str_as_timedelta_(date_to)  # try to read it as float -> timedelta
        if date_to is None:
            date_to = datetime.datetime.now()
        elif isinstance(date_to, datetime.datetime):
            date_to = date_to
        elif isinstance(date_to, datetime.timedelta):
            date_to = date_from + abs(date_to)
        else:
            date_to = datetime.datetime.fromisoformat(date_to.rstrip('Z'))

        # get all possible files from the devices
        result = self.get_files_for_dev_codes(dev_codes, date_from=date_from, date_to=date_to, print_stats=False)

        # convert the list to a DataFrame for easier modifications
        pd_result = self._convert_results2dataframe_(result)

        # create the mask for which files to download
        mask = self._mask_pd_results_(pd_result,
                                      min_file_size=min_file_size,
                                      max_file_size=max_file_size,
                                      extensions=extensions)
        return pd_result[mask]

    def download_structured(self, pd_result=None, download=True,
                            extensions=None,
                            min_file_size=0, max_file_size=.75e9, **kwargs):
        """
        This function syncs files from the onc server for the specified dev_codes. The files are organized in different
        directories by <Config.raw_data_dir>/<dev_code>/<year>_<month>/<file_name>.
        Files can be filtered by the file size, extensions,
        PARAMETERS
        ----------
        pd_result: None or dataframe, optional
            If none, it parse the gets the dataframe from get_files_structured(). If it is a dataframe, it should have
            the columns, get_files_structured() returns.
        download: bool, optional
            weather or not to download the files. True (default) downloads the files, and
            False just checks which pass the filter.
        extensions: list[str], optional
            A list of extensions to download. If None, it takes all possible extensions for STRAWb,
            i.e. ['hdf5', 'hld', 'raw', 'png', 'txt']. Applied to pd_result.
        min_file_size: int, float, optional
            defines the minimum file size. Applied to pd_result.
        max_file_size: int, float, optional
            defines the maximum file size. Applied to pd_result.
        kwargs: optional
            are parsed to get_files_structured(). Valid options are: dev_codes, date_from, date_to
        """

        if not isinstance(pd_result, pandas.DataFrame):
            pd_result = self.get_files_structured(min_file_size=min_file_size, max_file_size=max_file_size,
                                                  extensions=extensions, **kwargs)

        # create the mask for which files to download
        mask = self._mask_pd_results_(pd_result,
                                      min_file_size=min_file_size,
                                      max_file_size=max_file_size,
                                      extensions=extensions)

        # mask the results to files which passed the filter, and mask the mask (correct size)
        pd_result = pd_result[mask]
        mask = mask[mask]

        # mask also the files which are already downloaded
        mask &= ~pd_result['synced']

        download_size = (pd_result[mask]['fileSize']).sum()
        print(f'In total: {pd_result.shape[0]} files; exclude: {len(mask[~mask])}; '
              f'size to download: {human_size(download_size)}')
        if download:
            # reduce it with the mask and the columns to 'filename', 'outPath'
            pd_result_masked = pd_result[mask][['filename', 'outPath']]
            filters_or_result = dict(files=pd_result_masked.to_dict(orient='records'))
            self.getDirectFiles(filters_or_result=filters_or_result)

            # also label the synced files as synced
            pd_result['synced'] |= mask

        return pd_result

    @staticmethod
    def _mask_pd_results_(pd_result,
                          min_file_size=0, max_file_size=.75e9,
                          extensions=None,  # data_product_names=None
                          ):
        # mask the by file size
        mask = min_file_size <= pd_result['fileSize']
        mask &= pd_result['fileSize'] <= max_file_size

        if extensions is None:
            pass
        else:
            mask_extensions = np.zeros_like(mask)
            if isinstance(extensions, str):  # extensions must be a list
                extensions = [extensions]

            for i in extensions:
                mask_extensions += pd_result['filename'].str.endswith(i).to_numpy()
            mask &= mask_extensions > 0

        # # Select dataProducts
        # if data_product_names is None:
        #     pass
        # else:
        #     mask_data_product_names = mask.copy()*0
        #     if isinstance(data_product_names, str):  # data_product_names must be a list
        #         data_product_names = [data_product_names]
        #
        #     # get more information for the existing dataProductCodes
        #     dataProduct_all = []
        #     for i in pd_result['dataProductCode'].unique():
        #         dataProduct_all.extend(self.getDataProducts({'dataProductCode': i}))
        #
        #     dataProduct_select = [i for i in dataProduct_all if i['dataProductName'] in data_product_names]
        #     mask &= pd_result['dataProduct'] == dataProduct_select

        return mask

    @staticmethod
    def _convert_results2dataframe_(result):
        # convert the list to a DataFrame for easier modifications
        pd_result = pandas.DataFrame.from_dict(result['files'])

        # convert the datetime columns accordingly
        for key_i in ['archivedDate', 'modifyDate', 'dateFrom', 'dateTo']:
            pd_result[key_i] = pandas.to_datetime(pd_result[key_i])

        # add a 'outPath' column, to specify the outPath per file
        pd_result['outPath'] = strawb.Config.raw_data_dir + '/'
        pd_result['outPath'] += pd_result['deviceCode'].str.lower() + '/' + pd_result['dateFrom'].dt.strftime('%Y_%m')

        # rename 'outPath' to 'fullPath' and cal. the full path
        # pd_result = pd_result.rename(columns={"outPath": "fullPath"})
        pd_result["fullPath"] = pd_result["outPath"] + '/' + pd_result['filename']
        pd_result.set_index("fullPath", inplace=True, verify_integrity=True, drop=False)

        # mask the files which are already downloaded
        pd_result['synced'] = np.array([os.path.exists(i) for i in pd_result["fullPath"]], dtype=bool)
        return pd_result
