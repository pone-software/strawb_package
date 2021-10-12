import numpy as np
import pandas

from strawb.base_processed_data_store import BaseProcessedDataStore
from strawb.sensors.lidar.file_handler import FileHandler
from strawb.tools import TRBTools


class LidarProcessedDataStore(BaseProcessedDataStore, TRBTools):
    def __init__(self, file_handler: FileHandler):
        self.file_handler = file_handler

        # cleaned Counter, similar to PMTSpectrometer. Added to hdf5 ~05.10.2021. -> File version 2
        self._counts_ch_time = None  # channel which counts up at a constant frequency -> PMT Spectrometer
        self._counts_pmt = None  # the readout/PMT channel.
        self._counts_laser = None  # the Laser trigger channel.

        # calculated TRB rates from counters
        self._rate_time = None
        self._rate_pmt = None
        self._rate_laser = None

    # ---- cleaned TRB Counters  ----
    @property
    def counts_ch_time(self):
        if self._counts_ch_time is None:
            self.calculate_counts()
        return self._counts_ch_time

    @property
    def counts_pmt(self):
        if self._counts_pmt is None:
            self.calculate_counts()
        return self._counts_pmt

    @property
    def counts_laser(self):
        if self._counts_laser is None:
            self.calculate_counts()
        return self._counts_laser

    def get_pandas_cleaned_counts(self):
        if self.file_handler.file_version >= 2:
            return pandas.DataFrame(dict(time=self.file_handler.counts_time.asdatetime()[:],
                                         counters_ch_time=self.counts_ch_time,
                                         counts_pmt=self.counts_pmt,
                                         counts_laser=self.counts_laser))

    def clean_counts(self):
        if self.file_handler.file_version >= 2:
            data = TRBTools._clean_counts_(self.file_handler.counts_ch0,
                                           self.file_handler.counts_ch17,
                                           self.file_handler.counts_ch18)

            self._counts_ch_time = data[0]
            self._counts_pmt = data[1]
            self._counts_laser = data[2]
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
            self._rate_time, rate_data = TRBTools._calculate_counts_(
                daq_pulser_readout=self.file_handler.daq_pulser_readout,
                ch_time=self.counts_ch_time,
                counts_pmt=self.counts_pmt,
                counts_laser=self.counts_laser)

            self._rate_pmt = rate_data[0]
            self._rate_laser = rate_data[1]
            return self._rate_time, rate_data
        return None
