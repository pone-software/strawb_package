from typing import Union

from .file_handler import FileHandler
from .power import Power


class Module:
    # FileHandler = FileHandler

    def __init__(self, file: Union[str, FileHandler] = None, name=''):
        """The Module class.
        PARAMETER
        ---------
        file: Union[str, FileHandler], optional
            The filename as string or a instance of the module.FileHandler
        name: str, optional
            to give the class a name
        """

        self.name = name

        if isinstance(file, str):
            self.file_handler = FileHandler(file_name=file)
        else:
            self.file_handler = file

        self.power = Power(self.file_handler)

    def __del__(self):
        del self.power
        del self.file_handler
