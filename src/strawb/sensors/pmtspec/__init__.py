# Author: Kilian Holzapfel <kilian.holzapfel@tum.de>

from typing import Union

from strawb.sensors.pmtspec.meta_data import PMTMetaData
from strawb.sensors.pmtspec.pmtspec_trb_rates import PMTSpecTRBRates
from strawb.sensors.pmtspec.file_handler import FileHandler
from strawb.sensors.pmtspec.rate_scan import RateScan


class PMTSpec:
    # FileHandler = FileHandler

    def __init__(self, file: Union[str, FileHandler] = None, name=''):
        """The PMTSpec class.
        PARAMETER
        ---------
        file: Union[str, FileHandler], optional
            The filename as string or a instance of the pmtspec.FileHandler
        name: str, optional
            to give the class a name
        """
        self.name = name

        if isinstance(file, str):
            self.file_handler = FileHandler(file_name=file)
        else:
            self.file_handler = file

        self.trb_rates = PMTSpecTRBRates(file_handler=self.file_handler)

        self.pmt_meta_data = PMTMetaData()

        self.rate_scan = RateScan(self.trb_rates, self.pmt_meta_data)

    def __del__(self):
        del self.rate_scan
        del self.trb_rates
        del self.file_handler
        del self.pmt_meta_data

