import pandas
import os

from strawb.calibration.absorption import Absorption


class Water(Absorption):
    local_path = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    config_parameters_pool = pandas.read_csv(os.path.join(local_path, 'water_data.csv'))
    publications = pandas.read_csv(os.path.join(local_path, 'water_publication.csv'), index_col='publication')

    def __init__(self, thickness=None, publication='hale73', config_parameters=None):
        """Class to calculate the water absorption based on data (wavelength vs. absorption).
        Several publications are combined into a single dataset (pandas.DataFrame).
        See 'config_parameters_pool' for available publication strings.
        PARAMETER
        ---------
        publication: str, optional
            defines which dataset is selected from the `config_parameters_pool`.
            If a dataset is provided, with the `config_parameters` parameter, `publication` is ignored.
            See all valid publications with: `Water.publications`
        thickness: float, optional
            the thickness of the glass in meter [m].
        config_parameters: pandas.DataFrame, optional
            to define the absorption length of the glass.
            The DataFrame must have the columns 'wavelength'(in nm) and 'absorption'(in [1/m]).
            The 'absorption' is the absorption coefficient or 1./'absorption_length'.
        """
        if config_parameters is None:
            if 0 < (self.config_parameters_pool.publication == publication).sum():
                df_i = self.config_parameters_pool
                config_parameters = df_i[df_i.publication == publication].copy()
            else:
                raise KeyError(f'publication not in config_parameters_pool. Got: {publication}')

        Absorption.__init__(self, thickness=thickness, config_parameters=config_parameters)


class Chlorophyll(Absorption):
    """A. Bricaud and M. Babin and A. Morel and H. Claustre, "Variability in
    the chlorophyll-specific absorption coefficients of natural
    phytoplankton: analysis and parameterization," Journal of Geophysical
    Research, 100, 13321-13332, (1995)."""

    # [nm],     A,     B, r**2
    config_parameters = pandas.DataFrame(
        columns=['wavelength', 'A', 'B', 'r**2'],
        data=[[400, 0.0263, 0.282, 0.702], [404, 0.0280, 0.282, 0.706], [408, 0.0301, 0.282, 0.710],
              [412, 0.0323, 0.286, 0.718], [416, 0.0342, 0.293, 0.725], [420, 0.0356, 0.299, 0.733],
              [424, 0.0362, 0.313, 0.746], [428, 0.0376, 0.317, 0.749], [432, 0.0391, 0.318, 0.750],
              [436, 0.0399, 0.328, 0.757], [440, 0.0403, 0.332, 0.762], [444, 0.0390, 0.348, 0.774],
              [448, 0.0375, 0.360, 0.783], [452, 0.0365, 0.362, 0.783], [456, 0.0354, 0.367, 0.789],
              [460, 0.0350, 0.365, 0.789], [464, 0.0343, 0.368, 0.792], [468, 0.0335, 0.369, 0.793],
              [472, 0.0325, 0.371, 0.792], [476, 0.0312, 0.378, 0.793], [480, 0.0301, 0.377, 0.791],
              [484, 0.0290, 0.376, 0.788], [488, 0.0279, 0.369, 0.783], [492, 0.0267, 0.356, 0.774],
              [496, 0.0249, 0.341, 0.763], [500, 0.0230, 0.321, 0.747], [504, 0.0209, 0.300, 0.722],
              [508, 0.0189, 0.275, 0.686], [512, 0.0171, 0.249, 0.641], [516, 0.0156, 0.224, 0.578],
              [520, 0.0143, 0.196, 0.498], [524, 0.0131, 0.173, 0.417], [528, 0.0121, 0.151, 0.332],
              [532, 0.0113, 0.129, 0.248], [536, 0.0104, 0.109, 0.176], [540, 0.0097, 0.090, 0.116],
              [544, 0.0090, 0.073, 0.074], [548, 0.0083, 0.059, 0.044], [552, 0.0076, 0.044, 0.023],
              [556, 0.0068, 0.027, 0.007], [560, 0.0062, 0.016, 0.002], [564, 0.0057, 0.010, 0.001],
              [568, 0.0054, 0.007, 0.000], [572, 0.0053, 0.011, 0.001], [576, 0.0052, 0.022, 0.004],
              [580, 0.0053, 0.035, 0.013], [584, 0.0055, 0.050, 0.028], [588, 0.0056, 0.065, 0.043],
              [592, 0.0057, 0.081, 0.072], [596, 0.0056, 0.093, 0.097], [600, 0.0054, 0.092, 0.086],
              [604, 0.0055, 0.086, 0.083], [608, 0.0056, 0.076, 0.067], [612, 0.0059, 0.069, 0.063],
              [616, 0.0062, 0.063, 0.056], [620, 0.0065, 0.064, 0.063], [624, 0.0067, 0.071, 0.083],
              [628, 0.0069, 0.076, 0.099], [632, 0.0073, 0.080, 0.109], [636, 0.0075, 0.088, 0.128],
              [640, 0.0077, 0.098, 0.149], [644, 0.0079, 0.113, 0.177], [648, 0.0081, 0.123, 0.195],
              [652, 0.0085, 0.125, 0.200], [656, 0.0095, 0.122, 0.206], [660, 0.0115, 0.121, 0.235],
              [664, 0.0144, 0.131, 0.308], [668, 0.0176, 0.143, 0.377], [672, 0.0197, 0.153, 0.424],
              [675, 0.0201, 0.158, 0.445], [402, 0.0271, 0.281, 0.702], [406, 0.0290, 0.281, 0.701],
              [410, 0.0313, 0.283, 0.713], [414, 0.0333, 0.291, 0.723], [418, 0.0349, 0.296, 0.729],
              [422, 0.0359, 0.306, 0.739], [426, 0.0369, 0.316, 0.747], [430, 0.0386, 0.314, 0.746],
              [434, 0.0395, 0.324, 0.754], [438, 0.0401, 0.332, 0.761], [442, 0.0398, 0.339, 0.767],
              [446, 0.0383, 0.355, 0.779], [450, 0.0371, 0.359, 0.781], [454, 0.0358, 0.366, 0.788],
              [458, 0.0351, 0.368, 0.791], [462, 0.0347, 0.366, 0.791], [466, 0.0339, 0.369, 0.793],
              [470, 0.0332, 0.368, 0.792], [474, 0.0318, 0.375, 0.793], [478, 0.0306, 0.379, 0.793],
              [482, 0.0296, 0.377, 0.790], [486, 0.0285, 0.373, 0.786], [490, 0.0274, 0.361, 0.779],
              [494, 0.0258, 0.349, 0.770], [498, 0.0240, 0.332, 0.756], [502, 0.0220, 0.311, 0.735],
              [506, 0.0199, 0.288, 0.706], [510, 0.0180, 0.260, 0.664], [514, 0.0163, 0.237, 0.615],
              [518, 0.0149, 0.211, 0.541], [522, 0.0137, 0.184, 0.459], [526, 0.0126, 0.162, 0.374],
              [530, 0.0117, 0.139, 0.287], [534, 0.0108, 0.119, 0.211], [538, 0.0100, 0.100, 0.147],
              [542, 0.0093, 0.081, 0.092], [546, 0.0086, 0.066, 0.057], [550, 0.0080, 0.052, 0.033],
              [554, 0.0072, 0.036, 0.014], [558, 0.0065, 0.016, 0.002], [562, 0.0059, 0.013, 0.001],
              [566, 0.0055, 0.007, 0.000], [570, 0.0053, 0.005, 0.000], [574, 0.0052, 0.018, 0.003],
              [578, 0.0052, 0.028, 0.007], [582, 0.0054, 0.040, 0.016], [586, 0.0055, 0.056, 0.033],
              [590, 0.0056, 0.073, 0.058], [594, 0.0056, 0.088, 0.084], [598, 0.0055, 0.095, 0.098],
              [602, 0.0054, 0.088, 0.078], [606, 0.0055, 0.082, 0.078], [610, 0.0057, 0.071, 0.060],
              [614, 0.0060, 0.066, 0.062], [618, 0.0063, 0.064, 0.061], [622, 0.0066, 0.068, 0.073],
              [626, 0.0068, 0.074, 0.092], [630, 0.0071, 0.078, 0.104], [634, 0.0074, 0.084, 0.119],
              [638, 0.0076, 0.093, 0.138], [642, 0.0078, 0.105, 0.164], [646, 0.0080, 0.119, 0.189],
              [650, 0.0083, 0.124, 0.197], [654, 0.0089, 0.124, 0.203], [658, 0.0104, 0.120, 0.218],
              [662, 0.0129, 0.125, 0.269], [666, 0.0161, 0.137, 0.345], [670, 0.0189, 0.149, 0.404],
              [674, 0.0201, 0.157, 0.439], [676, 0.0200, 0.159, 0.445], [678, 0.0193, 0.158, 0.444],
              [682, 0.0166, 0.148, 0.406], [686, 0.0124, 0.124, 0.315], [690, 0.0083, 0.086, 0.164],
              [694, 0.0054, 0.042, 0.036], [698, 0.0036, -0.016, 0.003], [680, 0.0182, 0.155, 0.433],
              [684, 0.0145, 0.138, 0.368], [688, 0.0102, 0.107, 0.247], [692, 0.0067, 0.065, 0.094],
              [696, 0.0044, 0.015, 0.004], [700, 0.0030, -0.034, 0.012],
              ])

    config_parameters.sort_values('wavelength', inplace=True)

    def __init__(self, c_chl=1., config_parameters=None, thickness=1):
        """Class to calculate the absorption of based on:
        A. Bricaud and M. Babin and A. Morel and H. Claustre
        "Variability in the chlorophyll-specific absorption coefficients of natural
        phytoplankton: analysis and parameterization" (1995)

        The absorption coefficient (𝑎_𝑝ℎ) and chl a-specific absorption coefficient (𝑎^∗_𝑝ℎ)
        are calculated with:
        𝑎^∗_𝑝ℎ(𝜆)=𝐴(𝜆) * 𝑐ℎ𝑙^(−𝐵(𝜆))
        𝑎_𝑝ℎ(𝜆)=𝐴(𝜆) * 𝑐ℎ𝑙^(−𝐵(𝜆)+1)

        with the parameters:
        𝑐ℎ𝑙 or 𝑐ℎ𝑙 𝑎 : chlorophyll-a concentration [𝑚𝑔/𝑚^3]
        𝑎_𝑝ℎ : absorption coefficient of phytoplankton [1/𝑚]
        𝑎^∗_𝑝ℎ(𝜆) : chl a-specific absorption coefficient of phytoplankton [𝑚^2/𝑚𝑔]
        - 𝑎^∗_𝑝ℎ(𝜆)=𝑎_𝑝ℎ(𝜆) * 𝑐ℎ𝑙
        - alter ver. from text: absorption cross section of algae per mass unit of chl [1/𝑚*𝑐ℎ𝑙]
        𝐴(𝜆), 𝐵(𝜆): wavelength dependent parameters
        𝑟2: determination coefficient on the log-transformed data

        PARAMETER
        ---------
        c_chl: float, optional
            chlorophyll-a concentration in [mg/m^3]
        config_parameters: pandas.DataFrame, optional
            defines the parameters to calculate the absorption length of the phytoplankton (chlorophyll).
            With the columns: ['wavelength', 'A', 'B', 'r**2']
        """
        Absorption.__init__(self, config_parameters=config_parameters, thickness=thickness)

        self.__c_chl__ = None
        self.c_chl = float(c_chl)

    @property
    def c_chl(self):
        return self.__c_chl__

    @c_chl.setter
    def c_chl(self, value):
        if value != self.__c_chl__:
            self.__c_chl__ = float(value)
            self.config_parameters['absorption'] = self.cal_absorption(self.__c_chl__)

    def cal_absorption(self, c_chl):
        """Absorption coefficient [1/m] for the defined wavelengths (config_parameters) and a concentration chl
        PARAMETERS
        ----------
        c_chl: chlorophyll a concentration in [mg/m^3]
        """
        return self.absorption_polynomial(self.config_parameters.A.to_numpy(),
                                          self.config_parameters.B.to_numpy(),
                                          c_chl)

    def cal_absorption_chl(self, c_chl):
        """Chl a-specific absorption coefficient of phytoplankton [m^2/mg] for the defined wavelengths
        (config_parameters) and a concentration chl.
        PARAMETERS
        ----------
        c_chl: chlorophyll a concentration in [mg/m^3]
        """
        return self.absorption_chl_polynomial(self.config_parameters.A.to_numpy(),
                                              self.config_parameters.B.to_numpy(),
                                              c_chl)

    @staticmethod
    def absorption_polynomial(a, b, c_chl):
        """Polynomial to calculate the absorption coefficient [1/m]
        PARAMETERS
        ----------
        a, b: wavelength dependent parameters
        c_chl: chlorophyll a concentration in [mg/m^3]
        """

        return a * c_chl ** (-b + 1)

    @staticmethod
    def absorption_chl_polynomial(a, b, c_chl):
        """Polynomial to calculate the c_chl a-specific absorption coefficient of phytoplankton [m^2/mg].
        PARAMETERS
        ----------
        a, b: wavelength dependent parameters
        c_chl: chlorophyll a concentration in [mg/m^3]
        """
        return a * c_chl ** (-b)

    def absorption_interp(self, wavelength=None, c_chl=None, *args, **kwargs):
        """Interpolated absorption.
        PARAMETERS
        ----------
        wavelength: float, ndarray, optional
            the wavelength(s) where the transmittance is calculated. If None (default) it takes the
            np.linspace(self.wavelength.min(), self.wavelength.max(), 1000).
        c_chl: float, optional
            chlorophyll a concentration in [mg/m^3]
        *args, **kwargs: optional
            parsed to scipy.interpolate.interp1d(wavelength, transmittance, *args, **kwargs).
            E.g. to change the of interpolation order: kind='linear', kind='quadratic',or kind='cubic', respectively,
            for first-, second-, and third-order interpolation.

        RETURNS
        -------
        absorption: ndarray
            the absorption for the given wavelength of the material in [1/m].
        """
        self.c_chl = c_chl

        return Absorption.absorption_interp(self, wavelength=wavelength, *args, **kwargs)
