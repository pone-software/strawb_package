from strawb.sensors.sdom.file_handler import FileHandler
from strawb.trb_tools import TRBTools


class SDOMTRBRates(TRBTools):
    def __init__(self, file_handler: FileHandler, *args, **kwargs):
        """
        TRBTools Docstring: -> the following properties must be set in the child class which inherits from
        TRBTools and they should set the link to the data source:
        - raw_counts_arr; __daq_frequency_readout__; __time__"""
        TRBTools.__init__(self, *args, **kwargs)

        if isinstance(file_handler, FileHandler):
            self.file_handler = file_handler
        else:
            raise TypeError(f"Expected `strawb.sensors.sdom.FileHandler` got: {type(file_handler)}")

    @property
    def __daq_frequency_readout__(self):
        """Overwrite the property of TRBTools"""
        # TODO: adopt to SDOM file
        return self.file_handler.daq_frequency_readout

    @property
    def raw_counts_arr(self):
        """Overwrite the property of TRBTools"""
        # TODO: adopt to SDOM file
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
        # TODO: adopt to SDOM file
        return self.file_handler.counts_time
