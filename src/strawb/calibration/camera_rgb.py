import os

import pandas

from strawb.calibration.absorption import Absorption


class CameraRGB(Absorption):
    # default thickness in meter of the camera filter
    thickness = 1e-5  # [m] - !!!don't change this parameter!!!

    # set default - from the IMX225LQR datasheet
    local_path = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    config_parameters_all = pandas.read_csv(os.path.join(local_path, 'IMX225LQR-spectra.csv'))
    config_parameters = config_parameters_all[config_parameters_all['color'] == 'red'].copy()

    def __init__(self, color='red', config_parameters=None):
        """Base class to calculate the absorption of a material with a thickness.
        It is based on absorption length (a_l) to transmittance (t) for a given thickness (d):
        t = e^(-d/a_l) -> a_l = -d / ln(t)
        or similar for the absorption coefficient (a) (a = 1/a_l)
        t = e^(-d*a) -> a = - ln(t) / d
        PARAMETER
        ---------
        color: str, optional
            defines the color, either 'red', 'green', or 'blue

        config_parameters: pandas.DataFrame, optional
            to define the absorption length of the glass.
            The DataFrame must have the columns 'wavelength'(in nm) and 'absorption'(in [1/m]).
            The 'absorption' is the absorption coefficient or 1./'absorption_length'.
        """
        self.color = color
        if config_parameters is None:
            config_parameters = self.config_parameters_all[self.config_parameters_all['color'] == color].copy()

        Absorption.__init__(self, thickness=None, config_parameters=config_parameters)