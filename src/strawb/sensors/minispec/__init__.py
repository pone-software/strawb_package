from .file_handler import FileHandler

from typing import Union


class MiniSpectrometer:

    def __init__(self, file: Union[str, FileHandler] = None, name=''):
        self.name = name

        if isinstance(file, str):
            self.file_handler = FileHandler(file_name=file)
        else:
            self.file_handler = file

    def __del__(self):
        del self.file_handler
