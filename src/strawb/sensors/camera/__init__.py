# Author: Kilian Holzapfel <kilian.holzapfel@tum.de>
import os.path
from typing import Union

from .file_handler import FileHandler
from .images import Images
from .find_cluster import FindCluster
from .tools import *


class Camera:
    def __init__(self, file: Union[str, FileHandler] = None, name=''):
        self.name = name

        if isinstance(file, str):
            self.file_handler = FileHandler(file_name=file)
        else:
            self.file_handler = file

        self.images = Images(file_handler=self.file_handler)

        self.find_cluster = FindCluster(camera=self)
