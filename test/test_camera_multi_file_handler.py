import os
from unittest import TestCase
import numpy as np

from src.strawb.config_parser.config_parser import Config
from src.strawb.sensors.camera.file_handler import FileHandler
from src.strawb.sensors.camera import MultiFileHandler


class TestCameraMultiFileHandlerInit(TestCase):
    def setUp(self):
        self.date = '20210609'
        self.module = 'PMTSPECTROMETER001'

    def test_init_full_path(self):
        cam_run = MultiFileHandler(date=self.date, module=self.module)
        self.assertEqual(self.module, cam_run.module)
        # check here only the time
        self.assertIsInstance(cam_run.time,
                              np.ndarray,
                              f'cam_run.time has to be a np.ndarray, got: {type(cam_run.time)}')


class TestCameraMultiFileHandler(TestCase):
    def setUp(self):
        self.date = '20210609'
        # self.module = 'MINISPECTROMETER001'
        self.module = 'PMTSPECTROMETER002'
        self.cam_run = MultiFileHandler(date=self.date, module=self.module)

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
