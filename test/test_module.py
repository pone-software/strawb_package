import os
import random
from unittest import TestCase
import numpy as np

from src.strawb.config_parser import Config
from src.strawb.sensors.module.file_handler import FileHandler


class TestModuleFileHandler(TestCase):
    def setUp(self):
        file_list = FileHandler.find_files('*-SDAQ-MODULE.hdf5',
                                           directory=Config.raw_data_dir,
                                           recursive=True,
                                           raise_nothing_found=True)

        self.full_path = random.choice(file_list)  # select a random file
        self.file_name = os.path.split(self.full_path)[-1]

    def test_init_full_path(self):
        module = FileHandler(self.full_path)
        # self.assertEqual(self.module, module.module)
        # check here only the time
        self.assertIsInstance(module.temperatures_time[:],
                              np.ndarray,
                              f'module.temperatures_time[:] has to be a np.ndarray, '
                              f'got: {type(module.temperatures_time)}; file: {self.file_name}')

    def test_init_default_path(self):
        module = FileHandler(self.file_name)
        # self.assertEqual(self.module, module.module)
        # check here only the time
        self.assertIsInstance(module.temperatures_time[:],
                              np.ndarray,
                              f'module.temperatures_time[:] has to be a np.ndarray, '
                              f'got: {type(module.temperatures_time)}; file: {self.file_name}')
