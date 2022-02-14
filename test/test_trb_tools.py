from unittest import TestCase

import numpy as np

from strawb import tools
from strawb.trb_tools import TRBTools


class TestLidarTRBTools(TestCase):
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

    def test_integrate_rates(self):
        trb_tools = TRBTools()
        trb_tools.__daq_frequency_readout__ = 100

        # COUNTS
        # counts for one second
        counts = np.ones((5, trb_tools.__daq_frequency_readout__))

        # set every second entry to 0, but exclude the time counter (`1:`)
        counts[1:, ::2] = 0
        # the raw counts are the cum. sum
        trb_tools.__raw_counts_arr__ = np.cumsum(counts, axis=-1)

        # TIME
        dt = np.arange(counts.shape[1]) / trb_tools.__daq_frequency_readout__
        trb_tools.__time__ = tools.datetime2float(np.datetime64('now')) + dt

        # set interp_frequency, setter executes the calculation
        trb_tools.interp_frequency = trb_tools.daq_frequency_readout/2.
        self.assertTrue(np.all(trb_tools.daq_frequency_readout/2. == trb_tools.interp_rate.round(0)))