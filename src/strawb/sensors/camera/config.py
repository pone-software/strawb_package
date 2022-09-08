import os

import numpy as np


class Config:
    position_dict = {'TUMPMTSPECTROMETER001': {'module': np.array([355.20968475,
                                                                   690.49202575]),
                                               'data_cable': np.array([625, 300]),
                                               'steel_cable': np.array([678, 320])},
                     'TUMPMTSPECTROMETER002': {'module': None,
                                               'data_cable': None,
                                               'steel_cable': None},
                     'TUMMINISPECTROMETER001': {'module': None,
                                                'data_cable': None,
                                                'steel_cable': None}
                     }

    def __init__(self, device_code):
        # [x, y] coordinate of the module above the camera
        self.position_module = None

        # [x, y] coordinates of the data cable close to the camera
        # and it goes to self.position_module
        self.position_data_cable = None

        # [x, y] coordinates of the steel cable close to the camera
        # and it goes to self.position_module
        self.position_steel_cable = None

        # load data and set parameters
        self.mask_mounting = None
        camera_home = os.path.abspath(os.path.join(os.path.dirname(__file__)))
        with np.load(os.path.join(camera_home, 'mounting_mask.npz')) as f:
            if device_code in f:
                self.mask_mounting = f[device_code]

        if device_code in self.position_dict:
            self.position_module = self.position_dict[device_code]['module']
            self.position_data_cable = self.position_dict[device_code]['data_cable']
            self.position_steel_cable = self.position_dict[device_code]['steel_cable']

        else:
            print(f'device_code must be one of {self.position_dict.keys()}. Got: {device_code}')

    @staticmethod
    def get_line(p_0, p_1):
        """Combine two points into a line. p_i = [x, y]; line = [[x_0, x_1], [y_0, y_1]]"""
        return np.array([p_0, p_1]).T

    @property
    def data_cable(self):
        """Start and stop coordinates of the data cable."""
        if self.position_module is not None and self.position_data_cable is not None:
            return np.array([self.position_module, self.position_data_cable]).T
        else:
            return None

    @property
    def steel_cable(self):
        """Start and stop coordinates of the steel cable."""
        if self.position_module is not None and self.position_steel_cable is not None:
            return np.array([self.position_module, self.position_steel_cable]).T
        else:
            return None
