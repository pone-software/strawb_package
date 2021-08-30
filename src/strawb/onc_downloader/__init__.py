# Authors: Kilian Holzapfel <kilian.holzapfel@tum.de>
import datetime
import os
import threading

from onc.onc import ONC  # pip install onc; https://pypi.org/project/onc/

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
