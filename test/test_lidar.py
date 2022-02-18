import os
import random
from unittest import TestCase
import numpy as np

from src.strawb.config_parser import Config
from src.strawb.sensors.lidar.file_handler import FileHandler
from strawb import SyncDBHandler


def get_files():
    db = SyncDBHandler(file_name='Default')  # loads the db

    # mask by device
    mask = db.dataframe['deviceCode'] == 'TUMLIDAR001'
    mask |= db.dataframe['deviceCode'] == 'TUMLIDAR002'
    mask &= db.dataframe.dataProductCode == 'LIDARSD'
    mask &= db.dataframe.synced  # only downloaded files
    mask &= db.dataframe.file_version > 0  # only valid files

    file_list = db.dataframe.fullPath[mask].to_list()

    return file_list, mask, db


class TestLidarFileHandlerInit(TestCase):
    def setUp(self):
        file_list, mask, db = get_files()

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
        file_list, mask, db = get_files()

        self.full_path = random.choice(file_list)  # select a random file

        lidar_run = FileHandler(self.full_path)

    def test_lidar(self):
        pass


class TestLidarTRBRates(TestCase):
    def test_init(self):
        # lidar.file_handler.counts_ch0[1000:1010],
        # lidar.file_handler.counts_ch17[1000:1010],
        # lidar.file_handler.counts_ch18[1000:1010],

        pass
