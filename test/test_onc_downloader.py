import os
from unittest import TestCase

from src.strawb.onc_downloader import ONCDownload


class TestONCDownload(TestCase):
    def test_basic(self):
        onc_downloader = ONCDownload('0db751f8-9430-47af-bc11-ed6691b38e22', showInfo=False)

        filters = {'deviceCode': 'TUMPMTSPECTROMETER002',
                   'dateFrom': '2021-05-10T19:00:00.000Z',
                   'dateTo': '2021-05-10T21:59:59.000Z',
                   'extension': 'hdf5'}

        # in background
        # onc_downloader.start(filters=filters, allPages=True)

        # in foreground
        onc_downloader.download_file(filters=filters, allPages=True)

        for i in onc_downloader.result['downloadResults']:
            full_path = os.path.join(onc_downloader.outPath, i['file'])
            self.assertTrue(os.path.exists(full_path))
