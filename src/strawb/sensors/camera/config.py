import os
import numpy as np


class Config:
    """Camera Configuration
    Config.position_dict stores positions for the
    x and y represent the pixel coordinates of an image of the camera. The axes of the RGB image array are:
    [y-axis, x-axis, 3].
    """
    # STRAWb: r_position=.063, r_sphere=.1531, thickness_sphere=.012, n_a=1., n_g=1.52, n_w=1.35
    module_parameter = {
        'radius_sphere': 153.1e-3,  # meter, radius of the sphere
        'thickness_sphere': 12e-3,  # meter, thickness of the sphere
        'n_glass': 1.52,  # refractive index glass
        'n_air': 1.,  # refractive index air
        'n_water': 1.35,  # refractive index water
        'focal_length': 1.8e-3,  # focal length of the lens [meter]
        'pixel_size': 3.75 * 1e-6,  # pixel size on the image sensor [meter]
    }
    position_dict = {'TUMPMTSPECTROMETER001': {'module': np.array([355.20968475,
                                                                   690.49202575]),
                                               'data_cable': np.array([625, 300]),
                                               'steel_cable': np.array([678, 320]),
                                               'lenses_center': np.array([356, 711]),
                                               'camera_position': .063,  # meter, position in sphere form center
                                               **module_parameter},
                     'TUMPMTSPECTROMETER002': {'module': np.array([327.7, 682.6]),
                                               'data_cable': np.array([747, 952]),
                                               'steel_cable': np.array([723, 995]),
                                               'lenses_center': np.array([329, 688]),
                                               'camera_position': .063,  # meter, position in sphere form center
                                               **module_parameter},
                     'TUMMINISPECTROMETER001': {'module': [354., 708.],
                                                'data_cable': [0., 708.],  # more a guess - no proper image
                                                'steel_cable': [0., 728.],  # more a guess - no proper image
                                                'lenses_center': [379, 568],  # more a guess - no proper image
                                                # TODO: set camera_position, .1 is a guess
                                                'camera_position': .1,  # meter, position in sphere form center;
                                                **module_parameter,
                                                }
                     }

    def __init__(self, device_code=None):
        """Camera Config class which stores individual information of each camera.
        Locations represent the pixel coordinates of the un-rotated image of the camera where x is the shorter axis
        and y the longer.

        PARAMETER
        ---------
        device_code: None or str, optional
            the device_code of the module where the camera is located, i.e.
            'TUMPMTSPECTROMETER001', 'TUMPMTSPECTROMETER002', or 'TUMMINISPECTROMETER001'.
        """
        # store device_code
        self.device_code = device_code

        # [x, y] pixel coordinate of the module above the camera
        self._position_module_ = None

        # [x, y] pixel coordinates of the data cable close to the camera
        self._position_data_cable_ = None

        # [x, y] pixel coordinates of the steel cable close to the camera
        self._position_steel_cable_ = None

        # load data and set parameters later
        self._mask_mounting_ = np.ones((1280, 960), dtype=bool)  # default

        # distance to the line for each pixel. Default is set to 2000 [pixel] ~ 1500[pixel]*np.sqrt(2)
        self._pixel_distances_line_ = 2000  # default

        # [x, y] pixel coordinates center of the camera's lenses [pixel]
        self._position_lenses_center_ = None

        # Other geometrical parameters
        self._camera_position_ = None  # position of the camera in the module form the sphere center [meter]
        self._radius_sphere_ = None,  # [meter] radius of the sphere
        self._thickness_sphere_ = None  # [meter] thickness of the sphere

        # optical parameters
        self._n_glass_ = None  # refractive index glass
        self._n_air_ = None  # refractive index air
        self._n_water_ = None  # refractive index water

        # camera parameter
        self._focal_length_ = None  # focal length of the lens [meter]
        self._pixel_size_ = None  # pixel size on the image sensor [meter]

        # load data from config file and dict
        camera_home = os.path.abspath(os.path.join(os.path.dirname(__file__)))
        if device_code is not None:
            with np.load(os.path.join(camera_home, 'mounting_mask.npz')) as f:
                if device_code in f:
                    self._mask_mounting_ = f[device_code]

            with np.load(os.path.join(camera_home, 'pixel_distances_line.npz')) as f:
                if device_code in f:
                    self._pixel_distances_line_ = f[device_code]

            if device_code in self.position_dict:
                # copy all, otherwise it's a pointer on position_dict
                dictionary = self.position_dict[device_code]
                self._position_module_ = self.__get_copy__(dictionary, 'module')
                self._position_data_cable_ = self.__get_copy__(dictionary, 'data_cable')
                self._position_steel_cable_ = self.__get_copy__(dictionary, 'steel_cable')
                self._position_lenses_center_ = self.__get_copy__(dictionary, 'lenses_center')

                self._camera_position_ = self.__get_copy__(dictionary, 'camera_position')
                self._radius_sphere_ = self.__get_copy__(dictionary, 'radius_sphere')
                self._thickness_sphere_ = self.__get_copy__(dictionary, 'thickness_sphere')
                self._n_glass_ = self.__get_copy__(dictionary, 'n_glass')
                self._n_air_ = self.__get_copy__(dictionary, 'n_air')
                self._n_water_ = self.__get_copy__(dictionary, 'n_water')
                self._focal_length_ = self.__get_copy__(dictionary, 'focal_length')
                self._pixel_size_ = self.__get_copy__(dictionary, 'pixel_size')

            else:
                print(f'device_code must be one of {self.position_dict.keys()}. Got: {device_code}')

    @property
    def mask_mounting(self):
        """A pixel mask which masks the mounting."""
        return self._mask_mounting_

    @property
    def pixel_distances_line(self):
        """Distance to the line for each pixel as 2d array. Distances are only calculated in the module's FoV,
        i.e. where mask_mounting is True. Outside, the values is set to 2000 [pixel] ~ 1500[pixel]*np.sqrt(2)

        Generator code
        --------------
        >>> import strawb.camera
        >>> import numpy
        >>>
        >>> pixel_distances_line_dict = {}
        >>> for i in range(1,2):
        >>>     cam_conf = strawb.camera.Config(f'TUMPMTSPECTROMETER00{i}')  # camera config class
        >>>
        >>>     # get the pixel coordinates to calculate the distance to the line
        >>>     pixel_coordinates = numpy.argwhere(cam_conf.mask_mounting)[:,::-1].T
        >>>
        >>>     line = numpy.array([cam_conf.position_data_cable,
        >>>                      cam_conf.position_module,
        >>>                      cam_conf.position_steel_cable])
        >>>
        >>>     # calculate the distances - not very fast, needs some time
        >>>     distances_line = strawb.camera.tools.get_distances_line(*pixel_coordinates, line)
        >>>
        >>>     pixel_distances_line = cam_conf.mask_mounting.copy().astype(float)
        >>>     # all mounting pixels are set to 2000 [pixel] ~ 1500[pixel]*np.sqrt(2)
        >>>     pixel_distances_line[pixel_distances_line==0] = 2000
        >>>     pixel_distances_line[pixel_distances_line==1] = distances_line
        >>>
        >>>     pixel_distances_line_dict.update({cam_conf.device_code: pixel_distances_line})
        >>>
        >>> numpy.savez_compressed('pixel_distances_line.npz', **pixel_distances_line_dict)
        """
        return self._pixel_distances_line_

    @property
    def position_module(self):
        """[x, y] pixel coordinates of the module above the camera."""
        return self._position_module_

    @property
    def position_data_cable(self):
        """[x, y] pixel coordinates of the data cable close to the camera. The cables go from there to
        self.position_module. Use self.data_cable to get [position_module, position_data_cable].T"""
        return self._position_data_cable_

    @property
    def position_steel_cable(self):
        """[x, y] pixel coordinates of the steel cable close to the camera. The cables go from there to
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
            if isinstance(item, (np.ndarray, list)):
                item = item.copy()
        return item

    @property
    def camera_position(self):
        """position of the camera in the module form the sphere center [meter]"""
        return self._camera_position_

    @property
    def radius_sphere(self):
        """[meter] radius of the sphere"""
        return self._radius_sphere_

    @property
    def thickness_sphere(self):
        """[meter] thickness of the sphere"""
        return self._thickness_sphere_

    @property
    def n_glass(self):
        """refractive index glass"""
        return self._n_glass_

    @property
    def n_air(self):
        """refractive index air"""
        return self._n_air_

    @property
    def n_water(self):
        """refractive index water"""
        return self._n_water_

    @property
    def focal_length(self):
        """focal length of the lens [meter]"""
        return self._focal_length_

    @property
    def pixel_size(self):
        """pixel size on the image sensor [meter]"""
        return self._pixel_size_
