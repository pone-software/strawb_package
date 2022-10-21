import numpy as np
import pandas

import scipy.special
import scipy.interpolate


class Filter:
    # transmittance parameters of the files:
    # filter_para = {central_wavelength [nm]: (fwhm [nm], transmittance_max [0<=..<=1)}
    # transmittance_max is the max transmittance of the filter -> 0<=..<=1
    filter_para_0 = {-1: (np.nan, 1.),  # no Filter
                     350: (50., .95), 400: (25., .90), 425: (25., .90), 450: (10., .80),
                     460: (10., .80), 470: (10., .80), 480: (10., .80), 492: (10., .80),
                     500: (10., .80), 525: (25., .90), 550: (25., .90), 575: (25., .90)}

    def __init__(self, central_wavelength, filter_para=None):
        """Class to simulate the filter.
        PARAMETERS
        ----------
        central_wavelength: int
            the central wavelength of the filter to simulate.
            The value must be listed in filter_para_0 or filter_para as key.
        filter_para: dict, optional
            parameters which define the filters as a dict. If None (default) it takes
            the internal parameters stored in filter_para_0. Otherwise the dict must
            match the pattern:
            {central_wavelength [nm]: (fwhm [nm], transmittance_max [0<=..<=1), ...}
            transmittance_max: is the max transmittance of the filter
            FWHM: full width half maximum of the filter
            i.e. {350:(50., .95)} -> for central_wavelength=530nm; fwhm=50nm; transmittance_max=.95
        """
        if int(central_wavelength) in self.filter_para_0:
            self.central_wavelength = int(central_wavelength)
        else:
            raise KeyError(f'central_wavelength={central_wavelength} not in {self.filter_para_0.keys()}')

        if filter_para is None:
            self.filter_para = self.filter_para_0
        else:
            self.filter_para = filter_para

        self.fwhm = self.filter_para[self.central_wavelength][0]
        self.transmittance_max = self.filter_para[self.central_wavelength][1]

    def transmittance_erfc(self, wavelength=None, *args, **kwargs):
        """Calculate the transmittance (old version) of the filter which use
        the error function: scipy.special.erfc to calculate the curfe."""
        if wavelength is None:
            wavelength = self.get_linspace_wavelength(*args, **kwargs)

        if self.central_wavelength == -1:
            return np.ones_like(wavelength) * self.transmittance_max

        scale = .25 * self.transmittance_max  # .25 as 0<=erfc<=2 -> 0<=erfc**2*.25<=1
        left = scipy.special.erfc(self.central_wavelength - self.fwhm - wavelength)
        right = scipy.special.erfc(-self.central_wavelength - self.fwhm + wavelength)
        return scale * right * left

    def transmittance(self, wavelength=None, *args, **kwargs):
        """Calculate the transmittance of the filter which use a gaussian
        to calculate the curfe. This describes the lab measurements very well
        and replace the transmittance_erfc function."""
        if wavelength is None:
            wavelength = self.get_linspace_wavelength(*args, **kwargs)

        if self.central_wavelength == -1:
            return np.ones_like(wavelength) * self.transmittance_max

        # https://en.wikipedia.org/wiki/Full_width_at_half_maximum
        sigma = self.fwhm / (2. * np.sqrt(2 * np.log(2)))
        return self.transmittance_max * np.exp(-(wavelength - self.central_wavelength) ** 2 / (2 * sigma ** 2))

    def get_linspace_wavelength(self, fwhm_scale=2, *args, **kwargs):
        """Returns a array of wavelengths around the filter central wavelength.
        central_wavelength +- fwhm*fwhm_scale
        PARAMETER
        ---------
        fwhm_scale: float, optional
            scales the range, i.e. central_wavelength +- fwhm*fwhm_scale
        *args, **kwargs: list, dict, optional
            parsed to np.linspace
        """
        if self.central_wavelength == -1:
            keys_sort = np.sort(list(self.filter_para.keys()))
            start = keys_sort[1] - self.filter_para[keys_sort[1]][0] * fwhm_scale
            stop = keys_sort[-1] + self.filter_para[keys_sort[-1]][0] * fwhm_scale
        else:
            start = self.central_wavelength - self.fwhm * fwhm_scale
            stop = self.central_wavelength + self.fwhm * fwhm_scale
        return np.linspace(start, stop, *args, **kwargs)


class Absorption:
    config_parameters = None  # DataFrame with columns 'wavelength'(in nm) and 'absorption'(in [1/m]).
    thickness = 1.  # default thickness in meter

    def __init__(self, thickness=None, config_parameters=None):
        """Optical properties of BK7 glass.
        It is based on absorption length (a_l) to transmittance (t) for a given thickness (d):
        t = e^(-d/a_l) -> a_l = -d / ln(t)
        or similar for the absorption coefficient (a) (a = 1/a_l)
        t = e^(-d*a) -> a = - ln(t) / d
        PARAMETER
        ---------
        thickness: float, optional
            the thickness of the glass in meter.

        config_parameters: pandas.DataFrame, optional
            to define the absorption length of the glass.
            The DataFrame must have the columns 'wavelength'(in nm) and 'absorption'(in [1/m]).
            The 'absorption' is the absorption coefficient or 1./'absorption_length'.
        """
        if thickness is not None:
            self.thickness = float(thickness)
        if config_parameters is not None:
            self.config_parameters = config_parameters
        self.config_parameters.sort_values('wavelength', inplace=True)

    @property
    def wavelength(self, ):
        """Wavelength in nm (nano-meter)"""
        return self.config_parameters.wavelength.to_numpy()

    @property
    def absorption(self, ):
        """Absorption coefficient in [1/m] (1/meter)"""
        return self.config_parameters.absorption.to_numpy()

    @property
    def absorption_length(self, ):
        """Absorption length in m (meter)"""
        return 1. / self.absorption

    def transmittance(self, wavelength=None, thickness=None, *args, **kwargs):
        """Transmittance of the glass for a glass thickness.
        PARAMETERS
        ----------
        wavelength: float, ndarray, optional
            the wavelength(s) where the transmittance is calculated. If None (default) it takes the
            np.linspace(self.wavelength.min(), self.wavelength.max(), 1000).
        thickness: float, optional
            the thickness of the material to calculate the transmittance. If None (default) it takes the thickness of
            the init.
        *args, **kwargs: optional
            parsed to scipy.interpolate.interp1d(wavelength, transmittance, *args, **kwargs).
            E.g. to change the of interpolation order: kind='linear', kind='quadratic',or kind='cubic', respectively,
            for first-, second-, and third-order interpolation.

        RETURNS
        -------
        transmittance: ndarray
            the transmittance for the given wavelength and thickness of the material.
        """
        if thickness is None:
            thickness = self.thickness
        if wavelength is None:
            wavelength = np.linspace(self.wavelength.min(), self.wavelength.max(), 1000)

        interpolation = scipy.interpolate.interp1d(self.wavelength,
                                                   self.absorption2transmittance(thickness,
                                                                                 self.absorption),
                                                   *args, **kwargs
                                                   )
        return interpolation(wavelength)

    @staticmethod
    def absorption2transmittance(thickness, absorption):
        """Absorption coefficient to transmittance for the given thickness.
        PARAMETER
        ---------
        thickness: float
        absorption: float or ndarray
        """
        return np.exp(-thickness * absorption)

    @staticmethod
    def transmittance2absorption(thickness, transmittance):
        """Transmittance to absorption coefficient for the given thickness.
        PARAMETER
        ---------
        thickness: float
        transmittance: float or ndarray
        """
        return -np.log(transmittance) / thickness

    @staticmethod
    def absorption_length2transmittance(thickness, absorption_length):
        """Absorption length to transmittance for the given thickness.
        PARAMETER
        ---------
        thickness: float
        absorption: float or ndarray
        """
        return np.exp(-thickness / absorption_length)

    @staticmethod
    def transmittance2absorption_length(thickness, transmittance):
        """Transmittance to absorption length for the given thickness.
        PARAMETER
        ---------
        thickness: float
        transmittance: float or ndarray
        """
        return -thickness / np.log(transmittance)


class BK7(Absorption):
    """Class to calculate the absorption of a BK7 glass. Based on Values from the Data Sheet SCHOTT N-BK 7® 517642.251
    https://www.schott.com/shop/medias/schott-datasheet-n-bk7-eng.pdf?context=bWFzdGVyfHJvb3R8NjkxODAwfGFwcGxpY2F0aW9uL3BkZnxoZTUvaDM4Lzg4MTAzMTYxMDM3MTAucGRmfGJjNmI4ZjFmY2Q1NjMxMTE0MjkzMTUwOGRmMTUzOTg2NWJjZTgzMjA0OTc2NTNiMThjN2RhMjI4NGZmMWM4MWU
    and the code:
    converted Values from Data Sheet SCHOTT N-BK 7® 517642.251 for the BK7 glass
    >>> # Internal Transmittance τ_i:         λ [nm],τ_i (10mm), τ_i (25mm); (glass thickness)
    >>> bk7_wavelength, t_10, t_25 = np.array([[2500, 0.665, 0.360],
    >>>    [2325, 0.793, 0.560], [1970, 0.933, 0.840], [1530, 0.992, 0.980], [1060, 0.999, 0.997], [700 , 0.998, 0.996],
    >>>    [660 , 0.998, 0.994], [620 , 0.998, 0.994], [580 , 0.998, 0.995], [546 , 0.998, 0.996], [500 , 0.998, 0.994],
    >>>    [460 , 0.997, 0.993], [436 , 0.997, 0.992], [420 , 0.997, 0.993], [405 , 0.997, 0.993], [400 , 0.997, 0.992],
    >>>    [390 , 0.996, 0.989], [380 , 0.993, 0.983], [370 , 0.991, 0.977], [365 , 0.988, 0.971], [350 , 0.967, 0.920],
    >>>    [334 , 0.905, 0.780], [320 , 0.770, 0.520], [310 , 0.574, 0.250], [300 , 0.292, 0.050], [290 , 0.063, 1e-30],
    >>>    [289 , 1e-30, 1e-30],  # added to get interpolation right
    >>>    [288.9, 1e-30, 1e-30],  # added to get interpolation right
    >>>    [200 , 1e-30, 1e-30]]).T  # added to get interpolation right

    absorption coefficient (a) to transmittance (t) for thickness (d): t = e^(-d*a) -> a = -ln(t) / d
    calculate the absorption length as the mean of both thicknesses
    >>> bk7_absorption = np.mean([BK7.transmittance2absorption(0.010, t_10),  # 0.010 = 10mm
    >>>                           BK7.transmittance2absorption(0.025, t_25)], axis=0)  # absorption length [m]

    and generate the BK7 module with the default config_parameters (config_parameters can also be None and its the same)
    >>> bk7 = BK7(config_parameters=pandas.DataFrame(
    >>>           data={'wavelength': bk7_wavelength,
    >>>                 'absorption': bk7_absorption})

    #### OTHER Values for Transmittance ####
    Transmittance from L. Ruohan (source?) absorption of BK7 with 10mm thickness
    >>> bk7_wavelength_2 = np.array([300, 325, 350, 375, 450, 600])
    >>> bk7_transmittance_2 = np.array([.10, .66, .85, .90, .92, .93])
    >>> bk7_absorption_2 = BK7.transmittance2absorption(0.010, bk7_transmittance_2)  # 0.010 = 10mm

    Absorption from F.Henningsen (source?) - matches very well with SCHOTT N-BK 7®
    >>> e, c, h = 1.602176634e-19, 2.9979e8,6.6261e-34  # [J/eV], [m/s], [Js]
    >>> bk7_energy_3 = np.array([ 4.13,  3.54,  3.10,  2.76,  2.48,  2.25]) # eV
    >>> bk7_wavelength_3 = c*h/e / bk7_energy_3
    >>> bk7_absorption_3 = np.array([.00812, .298, 3.328, 3.328, 4.995, 4.995])  # [cm]
    >>> bk7_refraction_3 = np.array([1.550, 1.536, 1.530, 1.524, 1.520, 1.515])

    And generate the module with specified parameters, e.g. bk7_wavelength_3 and bk7_absorption_3
    >>> bk7 = BK7(config_parameters=pandas.DataFrame(
    >>>           data={'wavelength': bk7_wavelength_3,
    >>>                 'absorption': bk7_absorption_3})
    """
    # default thickness in meter for the 13" sphere
    thickness = .012

    # converted values from Data Sheet SCHOTT N-BK 7® 517642.251
    # 'absorption' is the mean of 'absorption_10mm', 'absorption_25mm' and the two are from the datasheet
    # i.e. bk7.transmittance2absorption(0.025, t_25).tolist()[::-1]
    config_parameters = pandas.DataFrame(
        columns=['wavelength', 'absorption', 'absorption_10mm', 'absorption_25mm'],
        data=[[200.0, 4835.428695287495, 6907.755278982137, 2763.1021115928547],
              [288.9, 4835.428695287495, 6907.755278982137, 2763.1021115928547],
              [289.0, 4835.428695287495, 6907.755278982137, 2763.1021115928547],
              [290.0, 1519.7820834259576, 276.46205525906043, 2763.1021115928547],
              [300.0, 121.46471930677258, 123.10014767138553, 119.82929094215963],
              [310.0, 55.48218135552634, 55.51258826625707, 55.45177444479562],
              [320.0, 26.146767554853653, 26.13647641344075, 26.157058696266557],
              [334.0, 9.960243950080535, 9.98203352822109, 9.938454371939983],
              [350.0, 3.345471355223158, 3.3556783528842753, 3.3352643575620404],
              [365.0, 1.1922052755297057, 1.2072581234269248, 1.1771524276324867],
              [370.0, 0.9174097713945402, 0.9040744652149071, 0.9307450775741732],
              [380.0, 0.6941539235476335, 0.7024614936964466, 0.6858463533988205],
              [390.0, 0.42162001706544006, 0.4008021397538822, 0.4424378943769979],
              [400.0, 0.3108688849602215, 0.3004509020298724, 0.32128686789057065],
              [405.0, 0.2907177497542255, 0.3004509020298724, 0.2809845974785786],
              [420.0, 0.2907177497542255, 0.3004509020298724, 0.2809845974785786],
              [436.0, 0.3108688849602215, 0.3004509020298724, 0.32128686789057065],
              [460.0, 0.2907177497542255, 0.3004509020298724, 0.2809845974785786],
              [500.0, 0.2204615800449144, 0.20020026706730792, 0.24072289302252084],
              [546.0, 0.1802605614844304, 0.20020026706730792, 0.16032085590155287],
              [580.0, 0.20035097000453966, 0.20020026706730792, 0.20050167294177143],
              [620.0, 0.2204615800449144, 0.20020026706730792, 0.24072289302252084],
              [660.0, 0.2204615800449144, 0.20020026706730792, 0.24072289302252084],
              [700.0, 0.1802605614844304, 0.20020026706730792, 0.16032085590155287],
              [1060.0, 0.1101151970851512, 0.10005003335835344, 0.12018036081194897],
              [1530.0, 0.8056627312136027, 0.8032171697264266, 0.8081082927007786],
              [1970.0, 6.954571649635215, 6.935007813479317, 6.974135485791112],
              [2325.0, 23.19297277242329, 23.193205734728902, 23.19273981011768],
              [2500.0, 40.831436866953766, 40.796823832628284, 40.866049901279254]])