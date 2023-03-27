import numpy as np

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
            the internal parameters stored in filter_para_0. Otherwise, the dict must
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
        the error function: scipy.special.erfc to calculate the curve."""
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
        to calculate the curve. This describes the lab measurements very well
        and replace the transmittance_erfc function."""
        if wavelength is None:
            wavelength = self.get_linspace_wavelength(*args, **kwargs)

        if self.central_wavelength == -1:
            return np.ones_like(wavelength) * self.transmittance_max

        # https://en.wikipedia.org/wiki/Full_width_at_half_maximum
        sigma = self.fwhm / (2. * np.sqrt(2 * np.log(2)))
        return self.transmittance_max * np.exp(-(wavelength - self.central_wavelength) ** 2 / (2 * sigma ** 2))

    def get_linspace_wavelength(self, fwhm_scale=2, *args, **kwargs):
        """Returns an array of wavelengths around the filter central wavelength.
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
