# Author: Kilian Holzapfel <kilian.holzapfel@tum.de>

from typing import Union

from strawb.sensors.adcp.current import CurrentFile
from strawb.sensors.adcp.file_handler import FileHandler


class ADCP:
    # FileHandler = FileHandler

    def __init__(self, file: Union[str, FileHandler] = None, name=''):
        """The ADCP class.
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

        self.current = CurrentFile(file_handler=self.file_handler)

    def __del__(self):
        del self.current
        del self.file_handler

