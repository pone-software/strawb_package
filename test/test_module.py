import os
from unittest import TestCase
import numpy as np

from src.strawb.config_parser.__init__ import Config
from strawb.sensors.module.file_handler import FileHandler


class TestModuleFileHandlerInit(TestCase):
    def setUp(self):
        self.file_name = 'TUMMINISPECTROMETER001_20210613T000000.000Z-SDAQ-MODULE.hdf5'
        self.module = 'MINISPECTROMETER001'

    def test_init_full_path(self):
        module = FileHandler(os.path.join(Config.raw_data_dir, self.file_name))
        self.assertEqual(self.module, module.module)
        # check here only the time
        self.assertIsInstance(module.temperatures_time[:],
                              np.ndarray,
                              f'module.temperatures_time[:] has to be a np.ndarray, '
                              f'got: {type(module.temperatures_time)}')

    def test_init_default_path(self):
        module = FileHandler(self.file_name)
        self.assertEqual(self.module, module.module)
        # check here only the time
        self.assertIsInstance(module.temperatures_time[:],
                              np.ndarray,
                              f'module.temperatures_time[:] has to be a np.ndarray, '
                              f'got: {type(module.temperatures_time)}')

    def test_init_non_exiting_file(self):
        file_name = 'TUMPMTSPECTROMETER002_20210510T250000.000Z-SDAQ-CAMERA.hdf5'
        self.assertRaises(FileNotFoundError, FileHandler, file_name=file_name)


class TestModuleFileHandlerInit(TestCase):
    def setUp(self):
        file_name = 'TUMMINISPECTROMETER001_20210613T000000.000Z-SDAQ-MODULE.hdf5'
        self.cam_run = FileHandler(file_name)

