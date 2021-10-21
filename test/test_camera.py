import os
import random
from unittest import TestCase
import numpy as np

from src.strawb.config_parser import Config
from src.strawb.sensors.camera.file_handler import FileHandler
from src.strawb.sensors.camera import CameraProcessedDataStore
from strawb import SyncDBHandler


class TestCameraFileHandlerInit(TestCase):
    def setUp(self):
        # Load DB, in case execute db.load_entire_db_from_ONC() to load the entire db, but this takes a bit.
        self.db = SyncDBHandler(file_name='Default')  # loads the db

        # filter the camera files
        mask = self.db.dataframe.fullPath.str.endswith('CAMERA.hdf5')  # filter by filename
        mask &= self.db.dataframe.synced  # mask un-synced hdf5 files
        mask &= self.db.dataframe.fileSize > 11000  # mask empty hdf5 files

        # and take one file randomly
        self.full_path = random.choice(self.db.dataframe.fullPath[mask])
        self.file_name = os.path.basename(self.full_path)

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

    def test_init_empty_file(self):
        camera = FileHandler(self.file_name)
        # check here only the time
        self.assertFalse(camera.is_empty,
                         f'camera.is_empty should be False for {camera.file_name}')

        # filter the camera files
        mask = self.db.dataframe.fullPath.str.endswith('CAMERA.hdf5')  # filter by filename
        mask &= self.db.dataframe.synced  # mask un-synced hdf5 files
        mask &= self.db.dataframe.fileSize > 11000  # mask empty hdf5 files

        # and take one file randomly
        full_path = random.choice(self.db.dataframe.fullPath[mask])
        camera = FileHandler(full_path)
        # check here only the time
        self.assertFalse(camera.is_empty,
                         f'camera.is_empty should be False for {camera.file_name}')

    def tearDown(self):
        print(self.full_path)


class TestCameraProcessedDataStore(TestCase):
    def setUp(self):
        # Load DB, in case execute db.load_entire_db_from_ONC() to load the entire db, but this takes a bit.
        db = SyncDBHandler(file_name='Default')  # loads the db

        # filter the camera files
        mask = db.dataframe.fullPath.str.endswith('CAMERA.hdf5')  # filter by filename
        mask &= db.dataframe.synced  # mask un-synced hdf5 files
        mask &= db.dataframe.fileSize > 11000  # mask empty hdf5 files

        # and take one file randomly
        self.full_path = random.choice(db.dataframe.fullPath[mask])
        cam_run = FileHandler(self.full_path)
        self.picture_handler = CameraProcessedDataStore(cam_run)

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
