import numpy as np
import pandas

from strawb import tools
from strawb.sensors.pmtspec.file_handler import FileHandler
from strawb.trb_tools import TRBTools


class PMTSpecTRBRates(TRBTools):
    def __init__(self, file_handler: FileHandler):
        if isinstance(file_handler, (FileHandler)):
            self.file_handler = file_handler
        else:
            raise TypeError(f"Expected pmtspec.FileHandler got: {type(file_handler)}")

        # time the absolute timestamp for the reading, corresponding to the middle of the read interval.
        # It is the absolute time for 'dcounts' and 'rate'
        self._time = None

        # cleaned Counter, similar to PMTSpectrometer. Added to hdf5 ~05.10.2021. -> File version 2
        self._dcounts_time = (
            None  # channel which counts up at a constant frequency -> PMT Spectrometer
        )
        self._dcounts = (
            None  # [ch1, ch3, ch5, ch6, ch7, ch8, ch9, ch10, ch11, ch12, ch13, ch15]
        )

        # TRB time delta
        self._rate_delta_t = (
            None  # time delta which corresponds to each counter read in seconds.
        )
        # TRB time since start of file
        self._delta_t0 = (
            None  # time since start of file in seconds.
        )
        # calculated TRB rates from counts
        self._rate = (
            None  # [ch1, ch3, ch5, ch6, ch7, ch8, ch9, ch10, ch11, ch12, ch13, ch15]
        )

    # Properties
    # ---- cleaned TRB Counters  ----
    @property
    def time(self):
        """The absolute timestamp of the counter reading, corresponding to the middle of the read interval. It is the
        absolute time for 'dcounts' and 'rate'. 1darray with axis [time_i]"""
        if self._time is None:
            self.diff_counts()
        return self._time

    @property
    def dcounts_time(self):
        """The delta of the TRB counts from the TRB channel 0 which counts at a fixed frequency,
        which is 10 kHz, see self.file_handler.daq_frequency_readout. 
        This means the width of the time bin is dcounts_time * file_handler.daq_frequency_readout
        
        1darray with axis [time_i]"""
        if self._dcounts_time is None:
            self.diff_counts()
        return self._dcounts_time

    @property
    def dcounts(self):
        """The delta of the TRB counts from the TRB channels as a 2darray with axes: [channel, time_i]."""
        if self._dcounts is None:
            self.diff_counts()
        return self._dcounts

    @property
    def delta_t0(self):
        """The time delta (in seconds) since start of file, reference is the middle of the time
        readout interval.
        """
        if self._delta_t0 is None:
            self.calculate_rates()
        return self._delta_t0
    
    # ---- TRB Rates ----
    @property
    def rate_delta_t(self):
        """The time delta (in seconds) which corresponds to the rates. 
        The time delta is calculated from the TRB channel_0 counts and the counting frequency,
        which is 10 kHz, see self.file_handler.daq_frequency_readout. 
        This delivers a more precise time because it is based on the raw
        delta_t from the TRB and it is more precise than the np.datetime64 can deliver. 
        However, its not an absolute timestamp, which is saved in self.time.
        EXAMPLE
        -------
        >>> trb_rates = PMTSpecTRBRates()
        >>> np.cumsum(trb_rates.rate_delta_t)  # gives the time in seconds from the start.
        >>> trb_rates.rate_delta_t.reshape(1,-1) * trb_rates.rate  # are the counts per channel <-> trb_rates.dcounts
        """
        if self._rate_delta_t is None:
            self.calculate_rates()
        return self._rate_delta_t

    @property
    def rate(self):
        """The rate (in Hz) per channel. It is calculated from: dcounts/rate_delta_t."""
        if self._rate is None:
            self.calculate_rates()
        return self._rate

    # ---- Pandas DataFrames ----
    def get_pandas_dcounts(self):
        """Returns a pandas dataframe with the dcounts, and an absolute timestamp"""
        if self.file_handler.file_version >= 1:
            return pandas.DataFrame(
                dict(
                    time=tools.asdatetime(self.time),
                    dcounts_time=self.dcounts_time,
                    dcounts_ch1=self.dcounts[0],
                    dcounts_ch3=self.dcounts[1],
                    dcounts_ch5=self.dcounts[2],
                    dcounts_ch6=self.dcounts[3],
                    dcounts_ch7=self.dcounts[4],
                    dcounts_ch8=self.dcounts[5],
                    dcounts_ch9=self.dcounts[6],
                    dcounts_ch10=self.dcounts[7],
                    dcounts_ch11=self.dcounts[8],
                    dcounts_ch12=self.dcounts[9],
                    dcounts_ch13=self.dcounts[10],
                    dcounts_ch15=self.dcounts[11],
                )
            )

    def get_pandas_rate(self):
        """Returns a pandas dataframe with the rates, the rate_delta_t, and an absolute timestamp"""
        if self.file_handler.file_version >= 1:
            return pandas.DataFrame(
                dict(
                    time=tools.asdatetime(self.time),
                    rate_time=self.rate_delta_t,
                    rate_ch1=self.rate[0],
                    rate_ch3=self.rate[1],
                    rate_ch5=self.rate[2],
                    rate_ch6=self.rate[3],
                    rate_ch7=self.rate[4],
                    rate_ch8=self.rate[5],
                    rate_ch9=self.rate[6],
                    rate_ch10=self.rate[7],
                    rate_ch11=self.rate[8],
                    rate_ch12=self.rate[9],
                    rate_ch13=self.rate[10],
                    rate_ch15=self.rate[11],
                )
            )

    # ---- Calculate dcounts and rates ----
    def diff_counts(self):
        """Calculates the diff of the counts for the PMT."""
        if (
            self.file_handler.file_version >= 1
        ):  # 1 is the base file_version, therefore, its all files
            # time the absolute timestamp for the reading, corresponding to the middle of the read interval
            # calculate the mid of the time bin
            self._time = (
                self.file_handler.counts_time[1:] + self.file_handler.counts_time[:-1]
            ) * 0.5
            data = self._diff_counts_(
                self.file_handler.counts_ch0,
                self.file_handler.counts_ch1,
                self.file_handler.counts_ch3,
                self.file_handler.counts_ch5,
                self.file_handler.counts_ch6,
                self.file_handler.counts_ch7,
                self.file_handler.counts_ch8,
                self.file_handler.counts_ch9,
                self.file_handler.counts_ch10,
                self.file_handler.counts_ch11,
                self.file_handler.counts_ch12,
                self.file_handler.counts_ch13,
                self.file_handler.counts_ch15,
            )

            self._dcounts_time = data[0]
            self._dcounts = data[1:]
            return [*data]
        return None

    def calculate_rates(self):
        """Calculates the rates of the PMTs based on the TRB counts.
        Returns:
        _delta_t0
        _rate_delta_t
        _rate
        """
        if (
            self.file_handler.file_version >= 1
        ):  # 1 is the base file_version, therefore, its all files
            self._rate_delta_t, self._rate = self._calculate_rates_(
                daq_frequency_readout=self.file_handler.daq_frequency_readout,
                dcounts_time=self.dcounts_time,
                dcounts_ch1=self.dcounts[0],
                dcounts_ch3=self.dcounts[1],
                dcounts_ch5=self.dcounts[2],
                dcounts_ch6=self.dcounts[3],
                dcounts_ch7=self.dcounts[4],
                dcounts_ch8=self.dcounts[5],
                dcounts_ch9=self.dcounts[6],
                dcounts_ch10=self.dcounts[7],
                dcounts_ch11=self.dcounts[8],
                dcounts_ch12=self.dcounts[9],
                dcounts_ch13=self.dcounts[10],
                dcounts_ch15=self.dcounts[11],
            )
            self._delta_t0 = np.cumsum(self._rate_delta_t) - self._rate_delta_t * .5
            return self._delta_t0, self._rate_delta_t, self._rate
        return None
