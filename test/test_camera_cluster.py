import os
import random
import time
from unittest import TestCase
import numpy as np

from src.strawb import SyncDBHandler
from strawb.sensors.camera import FindCluster
from strawb.sensors.camera import Camera


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


class TestCameraClusterBase(TestCase):

    def test_get_cluster(self):
        # shape = (10, 10); images = np.zeros((1, *shape))
        # pixel in the image are set who get_cluster labels the clusters
        image = np.array([[[1, 0, 0, 2, 2, 2, 0, 0],
                           [1, 0, 0, 0, 0, 0, 0, 0],
                           [1, 0, 0, 0, 0, 0, 3, 0],
                           [1, 0, 0, 4, 0, 0, 0, 3]]])

        pixel_mean = np.ones_like(image[0])
        pixel_std = np.ones_like(image[0]) * .1

        cam = Camera()
        find_cluster = FindCluster(cam,
                                   pixel_mean=pixel_mean, pixel_std=pixel_std,
                                   images=image * 4., eff_margin=False)

        labels = find_cluster.get_cluster(0, max_gaps=0, min_size_cluster=1)
        self.assertFalse(np.any(image[0] - labels))

        labels = find_cluster.get_cluster(0, max_gaps=1, min_size_cluster=1)
        image_i = image[0].copy()
        image_i[image_i > 2] -= 1  # 3 merge with 2 -> 3 gets to 2 and 4 gets to 3
        self.assertFalse(np.any(image_i - labels))

        labels = find_cluster.get_cluster(0, max_gaps=0, min_size_cluster=3)
        image_i = image[0].copy()
        image_i[image_i > 2] = 0  # no 3 & 4
        self.assertFalse(np.any(image_i - labels))

        image_i = image[0].copy()
        mask_mounting = image_i < 3  # exclude 3 and 4
        labels = find_cluster.get_cluster(0, max_gaps=0, min_size_cluster=1, mask_mounting=mask_mounting)
        image_i[image_i > 2] = 0  # no 3 & 4
        self.assertFalse(np.any(image_i - labels))

    def test_get_cluster_specs(self):
        # x.1 = red, x.2 = green, x.3 = blue
        # red is in [1, 2, 3], green in [1, 2], blue in [3, 4] + all have label 0 (background), too
        image = np.array([[[1.1, 0, 0, 2.2, 2.1, 2.2, 0, 0],
                           [1.2, 0, 0, 0, 0, 0, 0, 0],
                           [1.1, 0, 0, 0, 0, 0, 3.1, 0],
                           [1.2, 0, 0, 4.3, 0, 0, 0, 3.3]]])
        # must match with image
        label_unique_probe = {'red': [1, 2, 3],
                              'green': [1, 2],
                              'blue': [3, 4]}

        pixel_mean = np.ones_like(image[0]) * .001
        pixel_std = np.ones_like(image[0]) * .001

        find_cluster = FindCluster(Camera(),
                                   pixel_mean=pixel_mean, pixel_std=pixel_std,
                                   images=image, eff_margin=False)

        labels = find_cluster.get_cluster(0, max_gaps=0, min_size_cluster=1)
        specs = find_cluster.get_cluster_specs(0, labels, np.unique(labels))

        # probe all colors here
        for color in label_unique_probe:
            specs = find_cluster.get_cluster_specs(0, labels, np.unique(labels), color=color)

            bool_probe = np.zeros_like(np.unique(labels), dtype=bool)
            bool_probe[0] = True  # label 0 is always included
            bool_probe[label_unique_probe[color]] = True  # include as set manually

            # labels not present in the color should 0 -> `!=` -> False
            self.assertListEqual(list(~np.isnan(specs[f'charge_with_noise_{color}'])), list(bool_probe))
            # labels not present in the color should 0 -> `!=` -> False, label=0
            self.assertListEqual(list(specs[f'noise_{color}'] != 0), list(bool_probe))
            # labels not present in the color should report np.nan
            self.assertListEqual(
                list(np.argwhere(~np.isnan(specs[f'sn_mean_deviation_sigma_{color}'])).flatten()),
                [0, *label_unique_probe[color]])
            self.assertListEqual(
                list(np.argwhere(~np.isnan(specs[f'sn_mean_deviation_{color}'])).flatten()),
                [0, *label_unique_probe[color]])

    def test_df_picture(self):
        class Dummy:
            def __init__(self):
                pass

        # x.1 = red, x.2 = green, x.3 = blue
        image = np.array([[[1.1, 0, 0, 2.2, 2.1, 2.2, 0, 0],
                           [1.2, 0, 0, 0, 0, 0, 0, 0],
                           [1.1, 0, 0, 0, 0, 0, 3.1, 0],
                           [1.2, 0, 0, 4.3, 0, 0, 0, 3.3]]])

        pixel_mean = np.ones_like(image[0]) * .1
        pixel_std = np.ones_like(image[0]) * .1

        dummy = Dummy()
        dummy.time = time.time() + np.arange(len(image))

        cam = Camera()
        cam.file_handler = dummy

        find_cluster = FindCluster(cam,
                                   pixel_mean=pixel_mean, pixel_std=pixel_std,
                                   images=image, eff_margin=False)

        df = find_cluster.df_picture(0)
        n_rgb = np.sum([df.n_pixel_blue, df.n_pixel_red, df.n_pixel_green], axis=0)
        self.assertFalse(np.sum(df.n_pixel - n_rgb))

    def test_df_all(self):
        class Dummy:
            def __init__(self):
                pass

        # x.1 = red, x.2 = green, x.3 = blue
        image = np.array([[[1.1, 0, 0, 2.2, 2.1, 2.2, 0, 0],
                           [1.2, 0, 0, 0, 0, 0, 0, 0],
                           [1.1, 0, 0, 0, 0, 0, 3.1, 0],
                           [1.2, 0, 0, 4.3, 0, 0, 0, 3.3]]])

        pixel_mean = np.ones_like(image[0]) * .1
        pixel_std = np.ones_like(image[0]) * .1

        dummy = Dummy()
        dummy.time = time.time() + np.arange(len(image))

        cam = Camera()
        cam.file_handler = dummy

        find_cluster = FindCluster(cam,
                                   pixel_mean=pixel_mean, pixel_std=pixel_std,
                                   images=image, eff_margin=False)

        df = find_cluster.df_all()
        n_rgb = np.sum([df.n_pixel_blue, df.n_pixel_red, df.n_pixel_green], axis=0)
        self.assertFalse(np.sum(df.n_pixel - n_rgb))
