import numpy as np
import pandas

from strawb.sensors.lidar.file_handler import FileHandler
from strawb.trb_tools import TRBTools


class LidarTRBRates(TRBTools):
    def __init__(self, file_handler: FileHandler):
        self.file_handler = file_handler

        # cleaned Counter, similar to PMTSpectrometer. Added to hdf5 ~05.10.2021. -> File version 2
        self._dcounts_time = None  # channel which counts up at a constant frequency -> PMT Spectrometer
        self._dcounts_pmt = None  # the readout/PMT channel.
        self._dcounts_laser = None  # the Laser trigger channel.

        # calculated TRB rates from counts
        self._rate_time = None
        self._rate_pmt = None
        self._rate_laser = None

    # ---- cleaned TRB Counters  ----
    @property
    def dcounts_time(self):
        if self._dcounts_time is None:
            self.diff_counts()
        return self._dcounts_time

    @property
    def dcounts_pmt(self):
        if self._dcounts_pmt is None:
            self.diff_counts()
        return self._dcounts_pmt

    @property
    def dcounts_laser(self):
        if self._dcounts_laser is None:
            self.diff_counts()
        return self._dcounts_laser

    def get_pandas_dcounts(self):
        if self.file_handler.file_version >= 2:
            t = self.file_handler.counts_time.asdatetime()[:]
            return pandas.DataFrame(dict(time=(t[:-1] + np.diff(t) * .5),
                                         dcounts_time=self.dcounts_time,
                                         dcounts_pmt=self.dcounts_pmt,
                                         dcounts_laser=self.dcounts_laser))

    def diff_counts(self):
        if self.file_handler.file_version >= 2:
            data = self._diff_counts_(self.file_handler.counts_ch0,
                                      self.file_handler.counts_ch17,
                                      self.file_handler.counts_ch18)

            self._dcounts_time = data[0]
            self._dcounts_pmt = data[1]
            self._dcounts_laser = data[2]
            return [*data]
        return None

    # ---- TRB Rates ----
    @property
    def rate_time(self):
        if self._rate_time is None:
            self.calculate_counts()
        return self._rate_time

    @property
    def rate_pmt(self):
        if self._rate_pmt is None:
            self.calculate_counts()
        return self._rate_pmt

    @property
    def rate_laser(self):
        if self._rate_laser is None:
            self.calculate_counts()
        return self._rate_laser

    def get_pandas_rate(self):
        if self.file_handler.file_version >= 2:
            t = self.file_handler.counts_time.asdatetime()[:]
            return pandas.DataFrame(dict(time=(t[:-1] + np.diff(t) * .5),
                                         rate_time=self.rate_time,
                                         rate_pmt=self.rate_pmt,
                                         rate_laser=self.rate_laser))

    def calculate_counts(self):
        if self.file_handler.file_version >= 2:
            self._rate_time, rate_data = self._calculate_rates_(
                daq_frequency_readout=self.file_handler.daq_frequency_readout,
                dcounts_time=self.dcounts_time,
                dcounts_pmt=self.dcounts_pmt,
                dcounts_laser=self.dcounts_laser)

            self._rate_pmt = rate_data[0]
            self._rate_laser = rate_data[1]
            return self._rate_time, rate_data
        return None
