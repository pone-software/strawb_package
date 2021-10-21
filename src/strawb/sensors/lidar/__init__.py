from typing import Union

from strawb.sensors.lidar.lidar_processed_data_store import LidarProcessedDataStore
from strawb.sensors.lidar.file_handler import FileHandler


class Lidar:
    # FileHandler = FileHandler

    def __init__(self, name='', file: Union[str, FileHandler] = None):
        self.name = name

        if isinstance(file, str):
            self.file_handler = FileHandler(file_name=file)
        else:
            self.file_handler = file

        self.pds = LidarProcessedDataStore(file_handler=self.file_handler)
