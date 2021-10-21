# Author: Kilian Holzapfel <kilian.holzapfel@tum.de>
from typing import Union

from .file_handler import FileHandler
from .camera_processed_data_store import CameraProcessedDataStore


class Camera:
    def __init__(self, file: Union[str, FileHandler] = None, name=''):
        self.name = name

        if isinstance(file, str):
            self.file_handler = FileHandler(file_name=file)
        else:
            self.file_handler = file

        self.pds = CameraProcessedDataStore(file_handler=self.file_handler)
