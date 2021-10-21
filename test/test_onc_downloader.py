import os
from unittest import TestCase

import numpy as np
import pandas

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

    def test_mask_pd_result(self):
        pd_result = pandas.DataFrame([{'filename': 'TEST_1.txt', 'fileSize': 100, 'synced': True},
                                      {'filename': 'TEST_2.hdf5', 'fileSize': 3000, 'synced': True},
                                      {'filename': 'TEST_3.hld', 'fileSize': 81000, 'synced': True},
                                      {'filename': 'TEST_4.txt', 'fileSize': 6000, 'synced': False},
                                      {'filename': 'TEST_5.hdf5', 'fileSize': 21000, 'synced': False}
                                      ])

        # should mask all where synced=False
        mask = ONCDownloader._mask_pd_results_(pd_result)
        self.assertTrue(all(mask))  # check if all False

        mask = ONCDownloader._mask_pd_results_(pd_result, extensions='txt')
        self.assertEqual(np.sum(mask[mask]), 2)  # Only 'TEST_4.txt' pass

        mask = ONCDownloader._mask_pd_results_(pd_result, extensions=['txt', 'hdf5'])
        # self.assertTrue(not any(pd_result[mask]['synced']))  # check if all False
        self.assertEqual(np.sum(mask[mask]), 4)  # 'TEST_5.hdf5' and 'TEST_4.txt' pass

        mask = ONCDownloader._mask_pd_results_(pd_result, min_file_size=10000)
        self.assertEqual(np.sum(mask[mask]), 2)  # 'TEST_5.hdf5' and 'TEST_3.hld' pass

        mask = ONCDownloader._mask_pd_results_(pd_result, max_file_size=10000)
        self.assertEqual(np.sum(mask[mask]), 3)  # 'TEST_3.txt' and 'TEST_5.hdf5' DON'T pass

        mask = ONCDownloader._mask_pd_results_(pd_result, min_file_size=10000, max_file_size=30000)
        self.assertEqual(np.sum(mask[mask]), 1)  # only 'TEST_5.hdf5'  pass

        mask = ONCDownloader._mask_pd_results_(pd_result, min_file_size=10000, max_file_size=30000,
                                               extensions=['txt', 'hld'])
        self.assertEqual(np.sum(mask[mask]), 0)  # nothing pass
