import numpy as np

import scipy.special
import scipy.interpolate


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
            the thickness of the glass in meter [m].

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
        """Absorption length in [m] (meter)"""
        return 1. / self.absorption

    def transmittance(self, wavelength=None, thickness=None, *args, **kwargs):
        """Transmittance of the glass for a glass thickness.
        PARAMETERS
        ----------
        wavelength: float, ndarray, optional
            the wavelength(s) where the transmittance is calculated. If None (default) it takes the
            np.linspace(self.wavelength.min(), self.wavelength.max(), 1000).
        thickness: float, optional
            the thickness in meter [m] of the material to calculate the transmittance.
            If None (default) it takes the thickness of the init.
        *args, **kwargs: optional
            parsed to scipy.interpolate.interp1d(wavelength, transmittance, *args, **kwargs).
            E.g. to change the of interpolation order: kind='linear', kind='quadratic',or kind='cubic', respectively,
            for first-, second-, and third-order interpolation.

        RETURNS
        -------
        transmittance: ndarray
            the transmittance for the given wavelength and thickness of the material in percentage.
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
        """Absorption coefficient to transmittance for the given thickness with the formula:
        np.exp(-thickness * absorption)
        See also `absorption_length2transmittance` for absorption length

        PARAMETER
        ---------
        thickness: float
            the thickness in meter [m]
        transmittance: float or ndarray
            transmittance in percentage

        RETURN
        ------
        absorption: float or ndarray
            absorption coefficient in[1/m] (1/meter)
        """
        return np.exp(-thickness * absorption)

    @staticmethod
    def transmittance2absorption(thickness, transmittance):
        """Transmittance to absorption coefficient for the given thickness with the formula:
        -np.log(transmittance) / thickness
        See also `transmittance2absorption_length` for absorption length

        PARAMETER
        ---------
        thickness: float
            thickness in meter [m]
        transmittance: float or ndarray
            transmittance in percentage

        RETURN
        ------
        absorption: float or ndarray
            absorption coefficient in[1/m] (1/meter)
        """
        return -np.log(transmittance) / thickness

    @staticmethod
    def absorption_length2transmittance(thickness, absorption_length):
        """Absorption length to transmittance for the given thickness with the formula:
        np.exp(-thickness / absorption_length)
        See also `absorption2transmittance` for absorption coefficient

        PARAMETER
        ---------
        thickness: float
            thickness in meter [m]
        absorption length: float or ndarray
            absorption length in [m] (meter)

        RETURN
        ------
        transmittance: float or ndarray
            transmittance in percentage
        """
        return np.exp(-thickness / absorption_length)

    @staticmethod
    def transmittance2absorption_length(thickness, transmittance):
        """Transmittance to absorption length for the given thickness with the formula:
        -thickness / np.log(transmittance)
        See also `transmittance2absorption` for absorption coefficient

        PARAMETER
        ---------
        thickness: float
            thickness in meter [m]
        transmittance: float or ndarray
            transmittance in percentage

        RETURN
        ------
        absorption length: float or ndarray
            absorption length in [m] (meter)
        """
        return -thickness / np.log(transmittance)
