import os
from unittest import TestCase

from src.strawb.onc_downloader import ONCDownloader
from strawb import Config


class TestONCDownload(TestCase):
    def test_basic(self):
        onc_downloader = ONCDownloader(Config.onc_token, showInfo=False)

        filters = {'deviceCode': 'TUMPMTSPECTROMETER001',
                   'dateFrom': '2021-06-27T00:00:00.000Z',
                   'dateTo': '2021-06-27T23:59:59.000Z',
                   'extension': 'hdf5'}

        # in background
        # onc_downloader.start(filters=filters, allPages=True)

        # in foreground
        onc_downloader.download_file(filters=filters, allPages=True)

        for i in onc_downloader.result['downloadResults']:
            full_path = os.path.join(onc_downloader.outPath, i['file'])
            self.assertTrue(os.path.exists(full_path))
