# Authors: Kilian Holzapfel <kilian.holzapfel@tum.de>
import threading
from onc.onc import ONC  # pip install onc; https://pypi.org/project/onc/
from config_parser import Config


# Where can I find my token?
# On any of our Oceans 2.0 pages, once you are logged in, on the top right click on the Profile link,
# then on the Web Services API tab and that will take you to your token.
# https://data.oceannetworks.ca/home?TREETYPE=1&LOCATION=11&TIMECONFIG=0


class ONCDownload(ONC):
    """A wrapper class for the basic ONC module. It adds the storage of the result and can download the file inside a
    thread and therefore puts it in the background."""
    def __init__(self, token, outPath=None, **kwargs):
        if outPath is None:
            outPath = Config.raw_data_dir
            print(outPath)
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
        self.result = self.getDirectFiles(**kwargs)
