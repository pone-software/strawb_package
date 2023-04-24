import os
import random
from unittest import TestCase
import numpy as np

from src.strawb.calibration import CameraRGB


class TestCameraRGB(TestCase):
    def test_init_full_path(self):
        # test the initialization
        filter_dict = {c_i: CameraRGB(color=c_i) for c_i in ['blue', 'green', 'red']}

        wavelength = np.linspace(200, 700, 100)
        for i in filter_dict:
            filter_dict[i].transmittance(wavelength, fill_value=np.nan,  # "extrapolate", \
                                         bounds_error=False)
