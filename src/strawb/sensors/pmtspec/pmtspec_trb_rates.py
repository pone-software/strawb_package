import pandas

from strawb.sensors.pmtspec.file_handler import FileHandler
from strawb.trb_tools import TRBTools


class PMTSpecTRBRates(TRBTools):
    def __init__(self, file_handler: FileHandler, *args, **kwargs):
        TRBTools.__init__(self, *args, **kwargs)

        if isinstance(file_handler, FileHandler):
            self.file_handler = file_handler
        else:
            raise TypeError(f"Expected `strawb.sensors.pmtspec.FileHandler` got: {type(file_handler)}")

    @ property
    def __daq_frequency_readout__(self):
        """Overwrite the property of TRBTools"""
        return self.file_handler.daq_frequency_readout

    @property
    def raw_counts_arr(self):
        """Overwrite the property of TRBTools"""
        return [
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
            ]

    @property
    def __time__(self):
        """Overwrite the property of TRBTools"""
        return self.file_handler.counts_time

    # ---- Pandas DataFrames ----
    def get_pandas_dcounts(self):
        """Returns a pandas dataframe with the dcounts, and an absolute timestamp"""
        if self.file_handler.file_version >= 1:
            df = pandas.DataFrame(
                dict(
                    time=self.time_middle,
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
            df.set_index('time', drop=False, inplace=True)
            return df

    def get_pandas_rate(self):
        """Returns a pandas dataframe with the rates, the rate_delta_t, and an absolute timestamp"""
        if self.file_handler.file_version >= 1:
            df = pandas.DataFrame(
                dict(
                    time=self.time_middle,
                    rate_time=self.rate_time_middle,
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
            df.set_index('time', drop=False, inplace=True)
            return df
