import os

import numpy as np
import pandas

from strawb.calibration.absorption import Absorption


class BK7(Absorption):
    """Class to calculate the absorption of a BK7 glass and dispertion.
    There are three datasets for the absorption: Thorlabs 10mm (default):
    https://www.thorlabs.com/images/TabImages/Uncoated_N-BK7_Transmission.xlsx Schott 10mm, and Schott 25mm from the
    Data Sheet SCHOTT N-BK 7® 517642.251: https://www.schott.com/shop/medias/schott-datasheet-n-bk7-eng.pdf?context=bWFzdGVyfHJvb3R8NjkxODAwfGFwcGxpY2F0aW9uL3BkZnxoZTUvaDM4Lzg4MTAzMTYxMDM3MTAucGRmfGJjNmI4ZjFmY2Q1NjMxMTE0MjkzMTUwOGRmMTUzOTg2NWJjZTgzMjA0OTc2NTNiMThjN2RhMjI4NGZmMWM4MWU

    For the dispertion, there is a dataset from Data Sheet SCHOTT N-BK 7® 517642.251 and the constants for sellmeier
    also from the data sheet.

    You can switch the absorption dataset to schott with:
    >>> bk7 = BK7()
    >>> bk7.config_parameters = config_parameters_schott.copy()
    # and back to default Thorlabs:
    >>> bk7.config_parameters = config_parameters_thorlabs.copy()

    Plot all datasets with:
    >>> import matplotlib.pyplot as plt
    >>> plt.figure()
    >>> plt.plot(bk7.config_parameters.wavelength, bk7.config_parameters.absorption, label='thorlabs')
    >>> plt.plot(bk7.config_parameters_schott.wavelength, bk7.config_parameters_schott.absorption_10mm,
    >>>          label='schott 10mm')
    >>> plt.plot(bk7.config_parameters_schott.wavelength, bk7.config_parameters_schott.absorption_25mm,
    >>>          label='schott 25mm')
    >>> plt.legend()
    >>> plt.xlabel('wavelength [nm]')
    >>> plt.ylabel('absorption [1/m]')
    >>> plt.yscale('log')

    Data from Schott are calculated with the values from the Data Sheet SCHOTT N-BK 7® 517642.251
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
    config_parameters_schott = pandas.DataFrame(
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

    local_path = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    config_parameters_thorlabs = pandas.read_csv(os.path.join(local_path, 'bk7_10mm_thorlabs.csv'))

    # set default
    config_parameters = config_parameters_thorlabs.copy()

    # Dispersion of BK7
    # SCHOTT N-BK7® 517642.251
    config_refraction = pandas.DataFrame(
        columns=['wavelength', 'n'],
        data=[[2325.4, 1.48921],
              [1970.1, 1.49495],
              [1529.6, 1.50091],
              [1060.0, 1.50669],
              [1014.0, 1.50731],
              [852.1, 1.50980],
              [706.5, 1.51289],
              [656.3, 1.51432],
              [643.8, 1.51472],
              [632.8, 1.51509],
              [589.3, 1.51673],
              [587.6, 1.51680],
              [546.1, 1.51872],
              [486.1, 1.52238],
              [480.0, 1.52283],
              [435.8, 1.52668],
              [404.7, 1.53024],
              [365.0, 1.53627],
              [334.1, 1.54272],
              [312.6, 1.54862]])

    # Constant of dispersion formular
    b_bk7 = np.array([1.03961212, 0.231792344, 1.01046945])
    c_bk7 = np.array([0.00600069867, 0.0200179144, 103.560653]) * 1e6  # [nm]: 1e6 to convert from um to nm

    # cite: Sellmeier (1871): Zur Erklärung der abnormen Farbenfolge im Spectrum einiger Substanzen
    @staticmethod
    def sellmeier(wavelength, b=None, c=None):
        """ Dispersion formular by Sellmeier.
        PARAMETER
        ---------
        wavelength: ndarray, float
            wavelength in nm
        b, c:
            Constants of the dispersion formular by Sellmeier constants for a material.
            c must be in [nm]
        """
        if b is None:
            b = BK7.b_bk7
        if c is None:
            c = BK7.c_bk7

        wavelength = np.array(wavelength).reshape(-1, 1)
        b, c = np.array(b).reshape(1, -1), np.array(c).reshape(1, -1)
        x = np.sum(wavelength ** 2 * b / (wavelength ** 2 - c), axis=-1)
        return np.sqrt(1 + x)
