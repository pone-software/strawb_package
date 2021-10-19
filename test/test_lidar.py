import os
import random
from unittest import TestCase
import numpy as np

from src.strawb.config_parser import Config
from src.strawb.sensors.lidar.file_handler import FileHandler


class TestLidarFileHandlerInit(TestCase):
    def setUp(self):
        file_list = FileHandler.find_files_glob('*202109*-SDAQ-LIDAR.hdf5',
                                                directory=Config.raw_data_dir,
                                                recursive=True,
                                                raise_nothing_found=True)

        self.full_path = random.choice(file_list)  # select a random file
        self.file_name = os.path.split(self.full_path)[-1]

    def test_init_full_path(self):
        lidar = FileHandler(self.full_path)
        # check here only the time
        self.assertIsInstance(lidar.daq_time[:],
                              np.ndarray,
                              f'lidar.time[:] has to be a np.ndarray, got: {type(lidar.daq_time)}')

    def test_init_default_path(self):
        lidar = FileHandler(self.file_name)
        # check here only the time
        self.assertIsInstance(lidar.daq_time[:],
                              np.ndarray,
                              f'lidar.time[:] has to be a np.ndarray, got: {type(lidar.daq_time)}')

    def tearDown(self):
        print(self.full_path)


class TestLidarHandler(TestCase):
    def setUp(self):
        file_list = FileHandler.find_files_glob('*202109*-SDAQ-LIDAR.hdf5',
                                                directory=Config.raw_data_dir,
                                                recursive=True,
                                                raise_nothing_found=True)

        self.full_path = random.choice(file_list)  # select a random file

        lidar_run = FileHandler(self.full_path)

    def test_lidar(self):
        pass
