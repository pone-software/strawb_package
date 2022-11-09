# Author: Kilian Holzapfel <kilian.holzapfel@tum.de>

from typing import Union

from strawb.sensors.sdom.file_handler import FileHandler
from strawb.sensors.sdom.sdom_trb_rates import SDOMTRBRates


class PMTSpec:
    # FileHandler = FileHandler

    def __init__(self, file: Union[str, FileHandler] = None, name=''):
        """The PMTSpec class.
        PARAMETER
        ---------
        file: Union[str, FileHandler], optional
            The filename as string or a instance of the sdom.FileHandler
        name: str, optional
            to give the class a name
        """
        self.name = name

        if isinstance(file, str):
            self.file_handler = FileHandler(file_name=file)
        else:
            self.file_handler = file

        self.trb_rates = SDOMTRBRates(file_handler=self.file_handler)

    def __del__(self):
        del self.trb_rates
        del self.file_handler
