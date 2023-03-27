# DAN damage model
import numpy as np


def dna_damage_spectrum(wavelength, normalized_wavelength=None):
    """https://agupubs.onlinelibrary.wiley.com/doi/epdf/10.1029/97JD00072 and the source of
    'notebooks/dna_absorption.txt'
    PARAMETER
    ---------
    wavelength: float, ndarray
        wavelength in [nm]
    normalized_wavelength: None or float
        of not None sets the wavelength to normalize, hence at this wavelength the spectrum will be 1.
    """
    spectrum = np.zeros_like(wavelength)
    a_0 = 0.0326
    a_1 = 13.82
    a_2 = 9.
    lambda_0 = 310.
    m_w = wavelength <= 370.
    spectrum[m_w] = 1. / a_0 * np.exp(a_1 * 1 / (1 + np.exp((wavelength[m_w] - lambda_0) / a_2)) - 1)
    if normalized_wavelength is not None:
        spectrum /= 1. / a_0 * np.exp(a_1 * 1 / (1 + np.exp((normalized_wavelength - lambda_0) / a_2)) - 1)
    return spectrum
