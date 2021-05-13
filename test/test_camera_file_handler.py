import os
from unittest import TestCase
import numpy as np

from config_parser import Config
from src.strawb.sensors.camera.file_handler import FileHandler

class TestCameraFileHandlerInit(TestCase):
    def test_init_full_path(self):
        file_name = os.path.join(Config.raw_data_dir,
                                 'TUMPMTSPECTROMETER002_20210510T190000.000Z-SDAQ-CAMERA.hdf5')
        cam_run = FileHandler(file_name)
        self.assertEqual('PMTSPECTROMETER002', cam_run.module)
        # check here only the time
        self.assertIsInstance(cam_run.time,
                              np.ndarray,
                              f'cam_run.time has to be a np.ndarray, got: {type(cam_run.time)}')

    def test_init_default_path(self):
        file_name = 'TUMPMTSPECTROMETER002_20210510T190000.000Z-SDAQ-CAMERA.hdf5'
        cam_run = FileHandler(file_name)
        self.assertEqual('PMTSPECTROMETER002', cam_run.module)
        # check here only the time
        self.assertIsInstance(cam_run.time,
                              np.ndarray,
                              f'cam_run.time has to be a np.ndarray, got: {type(cam_run.time)}')

    def test_init_non_exiting_file(self):
        file_name = 'TUMPMTSPECTROMETER002_20210510T250000.000Z-SDAQ-CAMERA.hdf5'
        self.assertRaises(FileNotFoundError, FileHandler, file_name=file_name)

class TestCameraFileHandler(TestCase):
    def setUp(self):
        file_name = 'TUMPMTSPECTROMETER002_20210510T210000.000Z-SDAQ-CAMERA.hdf5'
        self.cam_run = FileHandler(file_name)

    def test_image2png_lucifer(self):
        self.cam_run.image2png_lucifer()

    def test_images_most_charge(self):
        mode_list, mask_list = self.cam_run.get_lucifer_mask()
        mask_lucifer = np.any(mask_list, axis=0)

        mask = (self.cam_run.integrated_minus_dark > 5e3) & self.cam_run.invalid_mask & ~mask_lucifer
        index = np.argsort(self.cam_run.integrated_minus_dark)
        index = index[mask[index]]  # remove invalid items  & cam_module.invalid_mask
        index = index[::-1]  # revers the order
        self.cam_run.image2png(index=index, f_name_formatter='{i}_{datetime}.png')
