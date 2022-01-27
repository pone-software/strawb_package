from .file_handler import FileHandler

from typing import Union

from strawb.sensors.minispec.file_handler import FileHandler


class MiniSpectrometer:

    def __init__(self, file: Union[str, FileHandler] = None, name=''):
        self.name = name

        if isinstance(file, str):
            self.file_handler = FileHandler(file_name=file)
        else:
            self.file_handler = file
