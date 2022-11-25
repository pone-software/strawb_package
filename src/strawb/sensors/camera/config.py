import os
import numpy as np


class Config:
    """ Camera Config
    Config.position_dict stores positions for the
    x and y represent the pixel coordinates of an image of the camera. The axes of the RGB image array are:
    [y-axis, x-axis, 3].
    """
    position_dict = {'TUMPMTSPECTROMETER001': {'module': np.array([355.20968475,
                                                                   690.49202575]),
                                               'data_cable': np.array([625, 300]),
                                               'steel_cable': np.array([678, 320]),
                                               'lenses_center': np.array([356, 711])},
                     'TUMPMTSPECTROMETER002': {'module': np.array([327.7, 682.6]),
                                               'data_cable': np.array([747, 952]),
                                               'steel_cable': np.array([723, 995]),
                                               'lenses_center': np.array([329, 688])},
                     'TUMMINISPECTROMETER001': {'module': [354., 708.],
                                                'data_cable': [0., 708.],    # more a guess - no proper image
                                                'steel_cable': [0., 728.],   # more a guess - no proper image
                                                'lenses_center': [379, 568],  # more a guess - no proper image
                                                }
                     }

    def __init__(self, device_code=None, un_mirror=False):
        """Camera Config class which stores individual information of each camera.
        Locations represent the pixel coordinates of the un-rotated image of the camera where x is the shorter axis
        and y the longer.

        PARAMETER
        ---------
        device_code: None or str, optional
            the device_code of the module where the camera is located, i.e.
            'TUMPMTSPECTROMETER001', 'TUMPMTSPECTROMETER002', or 'TUMMINISPECTROMETER001'.
        un_mirror: bool, optional
            the images are stored with the first axis
        """
        # [x, y] pixel coordinate of the module above the camera
        self._position_module_ = None

        # [x, y] pixel coordinates of the data cable close to the camera
        self._position_data_cable_ = None

        # [x, y] pixel coordinates of the steel cable close to the camera
        self._position_steel_cable_ = None

        # load data and set parameters
        self._mask_mounting_ = np.ones((1280, 960), dtype=bool)  # default

        # [x, y] pixel coordinates center of the camera's lenses
        self._position_lenses_center_ = None

        # load data from config file and dict
        camera_home = os.path.abspath(os.path.join(os.path.dirname(__file__)))
        if device_code is not None:
            with np.load(os.path.join(camera_home, 'mounting_mask.npz')) as f:
                if device_code in f:
                    self._mask_mounting_ = f[device_code]

            if device_code in self.position_dict:
                # copy all, otherwise its a pointer on position_dict
                dictionary = self.position_dict[device_code]
                self._position_module_ = self.__get_copy__(dictionary, 'module')
                self._position_data_cable_ = self.__get_copy__(dictionary, 'data_cable')
                self._position_steel_cable_ = self.__get_copy__(dictionary, 'steel_cable')
                self._position_lenses_center_ = self.__get_copy__(dictionary, 'lenses_center')

            else:
                print(f'device_code must be one of {self.position_dict.keys()}. Got: {device_code}')

    @property
    def mask_mounting(self):
        """A pixel mask which masks the mounting."""
        return self._mask_mounting_

    @property
    def position_module(self):
        """[x, y] pixel coordinates of the module above the camera."""
        return self._position_module_

    @property
    def position_data_cable(self):
        """[x, y] pixel coordinates of the data cable close to the camera. The cables goes from there to
        self.position_module. Use self.data_cable to get [position_module, position_data_cable].T"""
        return self._position_data_cable_

    @property
    def position_steel_cable(self):
        """[x, y] pixel coordinates of the steel cable close to the camera. The cables goes from there to
        self.position_module. Use self.steel_cable to get [position_module, position_steel_cable].T"""
        return self._position_steel_cable_

    @property
    def position_lenses_center(self):
        """[x, y] pixel coordinates center of the camera's lenses."""
        return self._position_lenses_center_

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

    @staticmethod
    def __get_copy__(dictionary, key):
        item = None
        if key in dictionary:
            item = dictionary[key]
            if item is not None:
                item = item.copy()

        return item
