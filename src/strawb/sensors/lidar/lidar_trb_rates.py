import pandas

from strawb.sensors.lidar.file_handler import FileHandler
from strawb.trb_tools import TRBTools


class LidarTRBRates(TRBTools):
    def __init__(self, file_handler: FileHandler, *args, **kwargs):
        TRBTools.__init__(self, *args, **kwargs)

        self.file_handler = file_handler

    # ---- cleaned TRB Counters  ----
    @property
    def __daq_frequency_readout__(self):
        """ TRB time counter frequency. Added to hdf5 ~05.10.2021. -> File version 2 """
        if self.file_handler.file_version >= 2:
            return self.file_handler.daq_frequency_readout

    @property
    def raw_counts_arr(self):
        """ Raw counter array. Added to hdf5 ~05.10.2021. -> File version 2.
        - file_handler.counts_ch0: time channel
        - file_handler.counts_ch17: the readout/PMT channel. returns number of counted photons per readout interval
        - file_handler.counts_ch18: returns number of emitted laser pulses per readout interval"""
        if self.file_handler.file_version >= 2:
            return [
                self.file_handler.counts_ch0,  # time channel
                self.file_handler.counts_ch17,  # readout/PMT channel
                self.file_handler.counts_ch18,  # laser channel
            ]

    @property
    def __time__(self):
        """Raw CPU absolute timestamp of counter array. Added to hdf5 ~05.10.2021. -> File version 2."""
        if self.file_handler.file_version >= 2:
            return self.file_handler.counts_time

    @property
    def dcounts_pmt(self):
        return self.dcounts[0]

    @property
    def dcounts_laser(self):
        return self.dcounts[1]

    @property
    def rate_pmt(self):
        return self.rate[0]

    @property
    def rate_laser(self):
        return self.rate[1]

    def get_pandas_dcounts(self):
        if self.file_handler.file_version >= 2:
            df = pandas.DataFrame(
                dict(
                    time=self.time_middle,
                    dcounts_time=self.dcounts_time,
                    dcounts_pmt=self.dcounts_pmt,
                    dcounts_laser=self.dcounts_laser,
                )
            )

            df.set_index('time', drop=False, inplace=True)
            return df

    def get_pandas_rate(self):
        if self.file_handler.file_version >= 2:
            df = pandas.DataFrame(
                dict(
                    time=self.time_middle,
                    rate_time=self.rate_time_middle,
                    rate_pmt=self.rate_pmt,
                    rate_laser=self.rate_laser,
                )
            )

            df.set_index('time', drop=False, inplace=True)
            return df
