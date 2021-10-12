from typing import Union

from strawb.sensors.lidar.LidarProcessedDataStore import LidarProcessedDataStore
from strawb.sensors.lidar.file_handler import FileHandler
from strawb.tools import TRBTools


class Lidar(TRBTools):
    # FileHandler = FileHandler

    def __init__(self, name='', file: Union[str, FileHandler] = None):
        self.name = name

        if isinstance(file, str):
            self.file_handler = FileHandler(file_name=file)
        else:
            self.file_handler = file

        self.pds = LidarProcessedDataStore(file_handler=self.file_handler)
