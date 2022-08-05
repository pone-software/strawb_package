import numpy as np
import pandas as pd


class Config:
    def __init__(self) -> None:
        self.mask_mounting = np.load('TUMPMTSPECTROMETER001_cam_mask.npy')
        
        with pd.read_csv('LEDs.csv') as led:
            self.module_x = np.sum(led.center_of_mass_x[:4])/4  # x coordinate of the module above the camera
            self.module_y = np.sum(led.center_of_mass_y[:4])/4  # y coordinate of the module above the camera

            self.data_cable_x = [625, self.module_x]  # x coordinates of the start and end point of the data cable
            self.data_cable_y = [300, self.module_y]  # y coordinates of the start and end point of the data cable

            self.steel_cable_x = [678, self.module_x]  # x coordinates of the start and end point of the steel cable
            self.steel_cable_y = [320, self.module_y]  # y coordinates of the start and end point of the steel cable