# Author: Kilian Holzapfel <kilian.holzapfel@tum.de>
from typing import Union

from .file_handler import FileHandler
from .images import Images
from .find_cluster import FindCluster
from .tools import *
from .config import Config
from .distortion import SphereDistortion
from .projection import EquisolidProjection


class Camera:
    def __init__(self, file: Union[str, FileHandler] = None, name='', invert_dir=None, device_code=None):
        """
        PARAMETER
        ---------
        file: str or FileHandler
            path or file for the data
        name: str, optional
            to set  a name
        invert_dir: bool, optional
            if the image should be rotated by 180deg. Used in the projection.
        device_code: str, optional
            to specify the device_code if no file is provided, e.g. to access the projection and config parameters.
            If a file is specified, device_code is ignored.
        """
        self.name = name

        if isinstance(file, str):
            self.file_handler = FileHandler(file_name=file)
        elif file is None or isinstance(file, FileHandler):
            self.file_handler = file
        else:
            raise ValueError(f'file_handler is no instance of strawb.sensors.camera.FileHandler, a path, nor None. Got:'
                             f'{type(file)}')

        if self.file_handler is not None:
            device_code = self.file_handler.deviceCode

        self.config = Config(device_code=device_code)

        self.images = Images(file_handler=self.file_handler)
        self.find_cluster = FindCluster(camera=self)

        self.projection = None
        if device_code is not None:
            sphere_distortion = SphereDistortion(r_position=self.config.camera_position,
                                                 r_sphere=self.config.radius_sphere,
                                                 thickness_sphere=self.config.thickness_sphere)
            self.projection = EquisolidProjection(focal_length=self.config.focal_length,
                                                  pixel_size=self.config.pixel_size,
                                                  pixel_center_index=self.config.position_lenses_center,
                                                  invert_dir=invert_dir,
                                                  distortion=sphere_distortion)

    def __del__(self):
        del self.find_cluster
        del self.images
        del self.file_handler
