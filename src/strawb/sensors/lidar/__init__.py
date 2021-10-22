from typing import Union

from strawb.sensors.lidar.lidar_trb_rates import LidarTRBRates
from strawb.sensors.lidar.file_handler import FileHandler


class Lidar:
    # FileHandler = FileHandler

    def __init__(self, name='', file: Union[str, FileHandler] = None):
        self.name = name

        if isinstance(file, str):
            self.file_handler = FileHandler(file_name=file)
        else:
            self.file_handler = file

        self.trb_rates = LidarTRBRates(file_handler=self.file_handler)
