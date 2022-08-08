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
        elif file_handler is None or isinstance(file_handler, FileHandler):
            self.file_handler = file
        else:
            raise ValueError(f'file_handler is no instance of strawb.sensors.camera.FileHandler, a path, nor None. Got:'
                             f'{type(file_handler)}')

        self.images = Images(file_handler=self.file_handler)

        self.find_cluster = FindCluster(camera=self)

        if self.file_handler is None:
            self.config = None
        else:
            self.config = Config(device_code=self.file_handler.deviceCode)

    def __del__(self):
        del self.find_cluster
        del self.images
        del self.file_handler
