import os
from unittest import TestCase

from src.strawb.onc_downloader import ONCDownloader
from strawb import dev_codes_deployed


class TestONCDownload(TestCase):
    def test_basic(self):
        onc_downloader = ONCDownloader(showInfo=False)
        dev_codes = list(dev_codes_deployed)
        dev_codes.sort()
        pd_result = onc_downloader.download_structured(dev_codes=dev_codes[:2],
                                                       extensions=None,
                                                       date_from='2021-08-30T00:00:00.000',
                                                       date_to='2021-08-30T01:00:00.000',
                                                       download=False,
                                                       )
        # in foreground, select only 5 files
        n_files = 5
        pd_result_masked = pd_result[:n_files][['filename', 'outPath']]
        filters_or_result = dict(files=pd_result_masked.to_dict(orient='records'))
        onc_downloader.getDirectFiles(filters_or_result=filters_or_result)

        # in background
        # onc_downloader.start(filters=filters, allPages=True)

        # in foreground

        for i in pd_result[:n_files]['fullPath']:
            self.assertTrue(os.path.exists(i))
