import os
from unittest import TestCase

import h5py
import numpy as np

from strawb import tools, BaseFileHandler
from strawb.trb_tools import TRBTools


class TestTRBTools(TestCase):
    def test_diff_counts(self):
        # 1d array
        steps = .5e9
        counts = np.arange(10) * steps
        counts %= 2 ** 31  # TRB overflow
        counts[2] -= 2 ** 31  # active reading
        diff, active_read = TRBTools._diff_counts_(counts)
        self.assertTrue((diff == steps).all(), msg=f'Diff counts should be all {steps}, got: {diff}')

        # 2d array
        counts = np.arange(30).reshape(3, -1) * steps
        counts %= 2 ** 31  # TRB overflow
        counts[2, 5] -= 2 ** 31  # active reading
        counts[0, 2] -= 2 ** 31  # active reading
        diff, active_read = TRBTools._diff_counts_(counts)
        self.assertTrue((diff == steps).all(), msg=f'Diff counts should be all {steps}, got: {diff}')

    def test_calculate_rates(self):
        daq_frequency_readout = [10, 10, 10]
        dcounts_time = np.ones(10) * 10
        steps = 3
        counts = np.ones(10) * steps
        delta_time, rate_arr = TRBTools._calculate_rates_(daq_frequency_readout=daq_frequency_readout,
                                                          dcounts_time=dcounts_time,
                                                          dcounts_arr=counts)

        self.assertEqual(counts.shape, rate_arr.shape)
        self.assertEqual(delta_time.shape, dcounts_time.shape)
        self.assertEqual(np.unique(rate_arr).shape, (1,))  # specific for the given parameters


class TestIntegratedRates(TestCase):
    def setUp(self):
        __daq_frequency_readout__ = 100
        # COUNTS
        # counts for one second
        counts = np.ones((5, __daq_frequency_readout__))

        # set every second entry to 0, but exclude the time counter (`1:`)
        counts[1:, ::2] = 0

        # TIME
        dt = np.arange(counts.shape[1]) / __daq_frequency_readout__
        __time__ = tools.datetime2float(np.datetime64('now')) + dt

        # create empty file
        with h5py.File('test.h5', 'a') as f:
            f.require_group('test')

        class ChildClass(TRBTools):
            @property
            def __daq_frequency_readout__(self):
                return __daq_frequency_readout__

            @property
            def __raw_counts_arr__(self):
                # the raw counts are the cum. sum
                return np.cumsum(counts, axis=-1)

            @property
            def __time__(self):
                return __time__

        self.trb_tools = ChildClass(file_handler=BaseFileHandler(file_name='test.h5'))

    def tearDown(self) -> None:
        os.remove('./test.h5')

    def test_integrate_rates(self):
        # set interp_frequency, setter executes the calculation
        self.trb_tools.interp_frequency = self.trb_tools.daq_frequency_readout / 2.
        self.assertTrue(np.all(self.trb_tools.daq_frequency_readout / 2. == self.trb_tools.interp_rate.round(0)))

    def test_write_hdf5(self):
        self.trb_tools.write_interp_rate()
        self.assertTrue('counts_interpolated' in self.trb_tools.file_handler.file)
        self.assertTrue('time' in self.trb_tools.file_handler.file['counts_interpolated'])
        self.assertTrue('rate' in self.trb_tools.file_handler.file['counts_interpolated'])

        self.trb_tools.remove_interp_rate()
        self.assertTrue('counts_interpolated' not in self.trb_tools.file_handler.file)
