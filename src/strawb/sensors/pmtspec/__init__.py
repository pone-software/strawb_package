# Author: Kilian Holzapfel <kilian.holzapfel@tum.de>

from typing import Union

from src.strawb.sensors.pmtspec.meta_data import PMTMetaData
from src.strawb.sensors.pmtspec.pmtspec_trb_rates import PMTSpecTRBRates
from src.strawb.sensors.pmtspec.file_handler import FileHandler
from src.strawb.trb_tools import TRBTools


class PMTSpec(TRBTools):
    # FileHandler = FileHandler

    def __init__(self, file: Union[str, FileHandler] = None, name=''):
        self.name = name

        if isinstance(file, str):
            self.file_handler = FileHandler(file_name=file)
        else:
            self.file_handler = file

        self.trb_rates = PMTSpecTRBRates(file_handler=self.file_handler)

        self.pmt_meta_data = PMTMetaData()
