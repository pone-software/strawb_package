import os
import random
from unittest import TestCase
import numpy as np

from src.strawb.sensors.camera.file_handler import FileHandler
from src.strawb.sensors.camera import Images
from src.strawb import SyncDBHandler


def get_files():
    db = SyncDBHandler(file_name='Default')  # loads the db

    # mask by device
    mask = db.dataframe['deviceCode'] == 'TUMPMTSPECTROMETER001'
    mask |= db.dataframe['deviceCode'] == 'TUMPMTSPECTROMETER002'
    mask |= db.dataframe['deviceCode'] == 'TUMMINISPECTROMETER001'

    mask &= db.dataframe.dataProductCode == 'MSSCD'
    mask &= db.dataframe.synced  # only downloaded files
    mask &= db.dataframe.file_version > 0  # only valid files

    file_list = db.dataframe.fullPath[mask].to_list()

    return file_list, mask, db


class TestCameraFileHandlerInit(TestCase):
    def setUp(self):
        file_list, mask, db = get_files()

        # and take one file randomly
        self.full_path = random.choice(file_list)
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

    # def tearDown(self):
    #     print(self.full_path)


class TestCameraImages(TestCase):
    def setUp(self):
        file_list, mask, db = get_files()

        # and take one file randomly
        self.full_path = random.choice(db.dataframe.fullPath[mask])
        cam_run = FileHandler(self.full_path)
        self.picture_handler = Images(cam_run)
        print(self.full_path)  # TODO: fix error, first detect teh file name

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

    def test_normalize(self,):
        arr = np.linspace(0, 2**16-1, 10, dtype=np.uint16)

        self.assertEqual(self.picture_handler.normalize_rgb(arr, bit_out=8)[-1], 255)
        self.assertEqual(self.picture_handler.normalize_rgb(arr, bit_out=16)[-1], int(2**16-1))
        self.assertEqual(self.picture_handler.normalize_rgb(arr, bit_out=0)[-1], 1)
                
        arr = np.linspace(0, 2**8-1, 10, dtype=np.uint8)

        self.assertEqual(self.picture_handler.normalize_rgb(arr, bit_out=8)[-1], 255)
        self.assertEqual(self.picture_handler.normalize_rgb(arr, bit_out=16)[-1], int(2**16-1))
        self.assertEqual(self.picture_handler.normalize_rgb(arr, bit_out=0)[-1], 1)

        arr = np.linspace(0, 1, 10, dtype=np.float64)

        self.assertEqual(self.picture_handler.normalize_rgb(arr, bit_out=8)[-1], 255)
        self.assertEqual(self.picture_handler.normalize_rgb(arr, bit_out=16)[-1], int(2**16-1))
        self.assertEqual(self.picture_handler.normalize_rgb(arr, bit_out=0)[-1], 1)

