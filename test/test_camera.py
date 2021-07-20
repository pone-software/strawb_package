import os
from unittest import TestCase
import numpy as np

from src.strawb.config_parser.config_parser import Config
from src.strawb.sensors.camera.file_handler import FileHandler


class TestCameraFileHandlerInit(TestCase):
    def setUp(self):
        self.file_name = 'TUMPMTSPECTROMETER002_20210510T190000.000Z-SDAQ-CAMERA.hdf5'
        self.module = 'PMTSPECTROMETER002'

    def test_init_full_path(self):
        camera = FileHandler(os.path.join(Config.raw_data_dir, self.file_name))
        self.assertEqual(self.module, camera.module)
        # check here only the time
        self.assertIsInstance(camera.time[:],
                              np.ndarray,
                              f'camera.time[:] has to be a np.ndarray, got: {type(camera.time)}')

    def test_init_default_path(self):
        camera = FileHandler(self.file_name)
        self.assertEqual(self.module, camera.module)
        # check here only the time
        self.assertIsInstance(camera.time[:],
                              np.ndarray,
                              f'camera.time[:] has to be a np.ndarray, got: {type(camera.time)}')

    def test_init_non_exiting_file(self):
        file_name = 'TUMPMTSPECTROMETER002_20210510T250000.000Z-SDAQ-CAMERA.hdf5'
        self.assertRaises(FileNotFoundError, FileHandler, file_name=file_name)


# class TestCameraFileHandler(TestCase):
#     def setUp(self):
#         file_name = 'TUMPMTSPECTROMETER002_20210501T190000.000Z-SDAQ-CAMERA.hdf5'
#         self.cam_run = FileHandler(file_name)


class TestPictureHandler(TestCase):
    def test_image2png_lucifer(self):
        self.cam_run.image2png_lucifer()

    def test_image2png_all(self):
        self.cam_run.image2png(exclude_invalid=False)

    def test_images_most_charge(self):
        mode_list, mask_list = self.cam_run.get_lucifer_mask()
        mask_lucifer = np.any(mask_list, axis=0)

        mask = (self.cam_run.integrated_minus_dark > 5e3) & self.cam_run.invalid_mask & ~mask_lucifer
        index = np.argsort(self.cam_run.integrated_minus_dark)
        index = index[mask[index]]  # remove invalid items  & cam_module.invalid_mask
        index = index[::-1]  # revers the order
        self.cam_run.image2png(index=index, f_name_formatter='{i}_{datetime}.png')
