import os
import random
from unittest import TestCase
import numpy as np
import pandas

from src.strawb.sensors.pmtspec.file_handler import FileHandler
from src.strawb.sensors.pmtspec.pmtspec_trb_rates import PMTSpecTRBRates
from strawb import SyncDBHandler


def get_files():
    db = SyncDBHandler(file_name='Default')  # loads the db

    # mask by device
    mask = db.dataframe['deviceCode'] == 'TUMPMTSPECTROMETER001'
    mask &= db.dataframe.dataProductCode == 'PMTSD'
    mask &= db.dataframe.synced  # only downloaded files

    file_list = db.dataframe.fullPath[mask].to_list()

    return file_list, mask, db


class TestPMTSpecFileHandlerInit(TestCase):
    def setUp(self):
        file_list, mask, db = get_files()

        self.full_path = random.choice(file_list)  # select a random file
        self.file_name = os.path.split(self.full_path)[-1]

    def test_init_full_path(self):
        pmt_spec = FileHandler(self.full_path)
        # check here only the time
        self.assertIsInstance(pmt_spec.daq_time[:],
                              np.ndarray,
                              f'pmt_spec.time[:] has to be a np.ndarray, got: {type(pmt_spec.daq_time)}')

    def test_init_default_path(self):
        pmt_spec = FileHandler(self.file_name)
        # check here only the time
        self.assertIsInstance(pmt_spec.daq_time[:],
                              np.ndarray,
                              f'pmt_spec.time[:] has to be a np.ndarray, got: {type(pmt_spec.daq_time)}')

    def tearDown(self):
        print(self.full_path)


class TestPMTSpecHandler(TestCase):
    def setUp(self):
        file_list, mask, db = get_files()
        self.full_path = random.choice(file_list)  # select a random file

        self.pmt_spec_file = FileHandler(self.full_path)
        self.pmt_spec_file.get_pandas_counts()

    def test_pandas(self):
        a = self.pmt_spec_file.get_pandas_counts()
        self.assertIsInstance(a, pandas.DataFrame)

        a = self.pmt_spec_file.get_pandas_hv()
        self.assertIsInstance(a, pandas.DataFrame)

        a = self.pmt_spec_file.get_pandas_daq()
        self.assertIsInstance(a, pandas.DataFrame)

        a = self.pmt_spec_file.get_pandas_padiwa()
        self.assertIsInstance(a, pandas.DataFrame)


class TestPMTSpecTRBRates(TestCase):
    def setUp(self):
        file_list, mask, db = get_files()

        self.full_path = random.choice(file_list)  # select a random file
        self.file_name = os.path.split(self.full_path)[-1]

        self.pmt_spec_file = FileHandler(self.full_path)

    def test_init(self):
        self.assertRaises(TypeError, PMTSpecTRBRates, self.file_name)  # needs a file handler

        trb_rates = PMTSpecTRBRates(FileHandler(self.file_name))

        self.assertIsInstance(trb_rates.dcounts_time, np.ndarray)
        self.assertGreater(trb_rates.dcounts_time.shape[0], 1)
        self.assertIsInstance(trb_rates.dcounts, np.ndarray)
        self.assertEqual(trb_rates.dcounts.shape[0], 12)

        self.assertIsInstance(trb_rates.time, np.ndarray)
        self.assertGreater(trb_rates.time.shape[0], 1)
        self.assertIsInstance(trb_rates.rate, np.ndarray)
        self.assertEqual(trb_rates.rate.shape[0], 12)
