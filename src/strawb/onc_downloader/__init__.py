# Authors: Kilian Holzapfel <kilian.holzapfel@tum.de>

import threading
import types
import os

import humanize
from onc.modules._util import _formatDuration
from onc.onc import ONC  # pip install onc; https://pypi.org/project/onc/

from strawb.config_parser.__init__ import Config
from strawb.tools import ShareJobThreads


class ONCDownloader(ONC):
    def __init__(self, token=None, outPath=None, **kwargs):
        """ A wrapper class for the basic ONC module. It adds the storage of the result and can download the file inside
        a thread and therefore puts it in the background.

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
            token = Config.onc_token

        ONC.__init__(self, token, outPath=outPath, **kwargs)
        self.archive.getDirectFiles = types.MethodType(get_direct_files_progress, self.archive)  # overload the instance
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


# Overload original function to include a progress bar
def get_direct_files_progress(self, filters: dict, overwrite: bool = False, allPages: bool = False):
    """
    Method to download files from the archivefiles service
    see https://wiki.oceannetworks.ca/display/help/archivefiles for usage and available filters
    """
    # make sure we only get a simple list of files
    if 'returnOptions' in filters:
        del filters['returnOptions']

    # Get a list of files
    try:
        if 'locationCode' in filters and 'deviceCategoryCode' in filters:
            dataRows = self.getListByLocation(filters=filters, allPages=allPages)
        elif 'deviceCode' in filters:
            dataRows = self.getListByDevice(filters=filters, allPages=allPages)
        else:
            raise Exception(
                'getDirectFiles filters require either a combination of "locationCode" and "deviceCategoryCode",'
                'or a "deviceCode" present.')
    except Exception:
        raise

    # Download the files obtained
    class Downloader:
        tries = 1
        successes = 0
        size = 0
        time = 0

        downInfos = []

        def __init__(self, parent):
            self.parent = parent
            self.tries = 1
            self.successes = 0
            self.size = 0
            self.time = 0

            self.downInfos = []
            self.info_lock = threading.Lock()

        def download_file(self, filename):
            outPath = self.parent._config('outPath')
            filePath = '{:s}/{:s}'.format(outPath, filename)
            fileExists = os.path.exists(filePath)

            if (not fileExists) or (fileExists and overwrite):
                # print('   ({:d} of {:d}) Downloading file: "{:s}"'.format(tries, n, filename))
                try:
                    downInfo = self.parent.getFile(filename, overwrite)
                    with self.info_lock:
                        self.size += downInfo['size']
                        self.time += downInfo['downloadTime']
                        self.downInfos.append(downInfo)
                        self.successes += 1
                except Exception:
                    raise
                self.tries += 1
            else:
                # print('   Skipping "{:s}": File already exists.'.format(filename))
                downInfo = {
                    'url': self.parent._getDownloadUrl(filename),
                    'status': 'skipped',
                    'size': 0,
                    'downloadTime': 0,
                    'file': filename
                }
                with self.info_lock:
                    self.downInfos.append(downInfo)

    downloader = Downloader(parent=self)

    share_job_threads = ShareJobThreads(Config.onc_download_threads)
    share_job_threads.do(downloader.download_file, dataRows['files'])

    print('Directory: {self.outPath}; {:d} files; size {:s}; time: {:s}'.format(downloader.successes,
                                                                                humanize.naturalsize(downloader.size),
                                                                                _formatDuration(downloader.time)))

    return {
        'downloadResults': downloader.downInfos,
        'stats': {
            'totalSize': downloader.size,
            'downloadTime': downloader.time,
            'fileCount': downloader.successes
        }
    }
