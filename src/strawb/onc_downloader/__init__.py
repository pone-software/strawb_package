# Authors: Kilian Holzapfel <kilian.holzapfel@tum.de>
import threading
from onc.onc import ONC  # pip install onc; https://pypi.org/project/onc/
# from ..config_parser.config_parser import Config
from strawb.config_parser.config_parser import Config
import os


class ONCDownloader(ONC):
    def __init__(self, token=None, outPath=None, **kwargs):
        """A wrapper class for the basic ONC module. It adds the storage of the result and can download the file inside a
        thread and therefore puts it in the background.

        PARAMETER
        ---------
        token: str, optional
            The personal access token from ONC 2.0. If None (default), it's the parameter from the config file.
        outPath: str, optional
            The path in which the downloads are saved. If None (default), it's the parameter from the config file.
        kwargs: dict, optional
            parsed to ONC package initialisation.
        """
        if outPath is None:
            outPath = Config.raw_data_dir

        if token is None:
            token = Config.token

        ONC.__init__(self, token, outPath=outPath, **kwargs)
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
        print(f'Download in directory: {self.outPath}')
        self.result = self.getDirectFiles(**kwargs)
        for res_i in self.result['downloadResults']:
            if 'file' in res_i:
                res_i['file'] = os.path.abspath(os.path.join(self.outPath, res_i['file']))
