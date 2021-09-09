import os
import random
from unittest import TestCase
import numpy as np

from src.strawb.config_parser import Config
from src.strawb.sensors.camera.file_handler import FileHandler
from src.strawb.sensors.camera import PictureHandler


class TestCameraFileHandlerInit(TestCase):
    def setUp(self):
        file_list = FileHandler.find_files('*-SDAQ-CAMERA.hdf5',
                                           directory=Config.raw_data_dir,
                                           recursive=True,
                                           raise_nothing_found=True)

        self.full_path = random.choice(file_list)  # select a random file
        self.file_name = os.path.split(self.full_path)[-1]

    def test_init_full_path(self):
        camera = FileHandler(self.full_path)
        # check here only the time
        self.assertIsInstance(camera.time[:],
                              np.ndarray,
                              f'camera.time[:] has to be a np.ndarray, got: {type(camera.time)}')

    def test_init_default_path(self):
        camera = FileHandler(self.file_name)
        # check here only the time
        self.assertIsInstance(camera.time[:],
                              np.ndarray,
                              f'camera.time[:] has to be a np.ndarray, got: {type(camera.time)}')

    def tearDown(self):
        print(self.full_path)


class TestPictureHandler(TestCase):
    def setUp(self):
        file_list = FileHandler.find_files('*-SDAQ-CAMERA.hdf5',
                                           directory=Config.raw_data_dir,
                                           recursive=True,
                                           raise_nothing_found=True)

        self.full_path = random.choice(file_list)  # select a random file

        cam_run = FileHandler(self.full_path)
        self.picture_handler = PictureHandler(cam_run)

    def test_image2png_lucifer(self):
        self.picture_handler.image2png_lucifer()

    def test_image2png_all(self):
        self.picture_handler.image2png(exclude_invalid=False)

    def test_images_most_charge(self):
        mode_list, mask_list = self.picture_handler.get_lucifer_mask()
        mask_lucifer = np.any(mask_list, axis=0)

        mask = (self.picture_handler.integrated_minus_dark > 5e3) & self.picture_handler.invalid_mask & ~mask_lucifer
        index = np.argsort(self.picture_handler.integrated_minus_dark)
        index = index[mask[index]]  # remove invalid items  & cam_module.invalid_mask
        index = index[::-1]  # revers the order
        self.picture_handler.image2png(index=index, f_name_formatter='{i}_{datetime}.png')
