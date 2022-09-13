# Author: Kilian Holzapfel <kilian.holzapfel@tum.de>
from typing import Union

from .file_handler import FileHandler
from .images import Images
from .find_cluster import FindCluster
from .tools import *
from .config import Config


class Camera:
    def __init__(self, file: Union[str, FileHandler] = None, name=''):
        self.name = name

        if isinstance(file, str):
            self.file_handler = FileHandler(file_name=file)
        elif file is None or isinstance(file, FileHandler):
            self.file_handler = file
        else:
            raise ValueError(f'file_handler is no instance of strawb.sensors.camera.FileHandler, a path, nor None. Got:'
                             f'{type(file)}')

        self.images = Images(file_handler=self.file_handler)

        self.find_cluster = FindCluster(camera=self)

        if self.file_handler is not None:
            self.config = Config(device_code=self.file_handler.deviceCode)
        else:
            self.config = Config(device_code=None)

    def __del__(self):
        del self.find_cluster
        del self.images
        del self.file_handler
