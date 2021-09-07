import os
from unittest import TestCase

from src.strawb.onc_downloader import ONCDownloader
from src.strawb import dev_codes_deployed


class TestONCDownload(TestCase):
    def test_basic(self):
        onc_downloader = ONCDownloader(showInfo=False)
        pd_result = onc_downloader.download_structured(dev_codes=dev_codes_deployed[:2],
                                                       extensions=None,
                                                       date_from='2021-08-30T00:00:00.000',
                                                       date_to='2021-08-30T01:00:00.000',
                                                       download=False,
                                                       )
        # in foreground, select only 5 files
        n_files = 5
        pd_result_masked = pd_result[:n_files]
        onc_downloader.getDirectFiles(filters_or_result=pd_result_masked)

        # in background
        # onc_downloader.start(filters=filters, allPages=True)

        # in foreground

        for i in pd_result[:n_files]['fullPath']:
            self.assertTrue(os.path.exists(i))
