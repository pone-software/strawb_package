import pandas

publications = {
    'morel77_b': [
        'pure water',
        """https://aslopubs.onlinelibrary.wiley.com/doi/pdf/10.4319/lo.1977.22.4.0709
      Attenuation (c_w), scattering (b_w), and absorption (a_w) coefficients
      for optically (and chemically) pure water
      [[Wavelength [nm], Attenuation (c_w) [m-1], scattering (b_w) [m-1], absorption (a_w) [m-1]]]"""
    ],
    'morel07': [
        'pure water',
        """André Morel, Bernard Gentili, Hervé Claustre, Marcel Babin, Annick Bricaud, Joséphine Ras, Fanny Tièche
      Optical properties of the "clearest" natural waters (2007)

      Tabel 2a:
      Adopted values for the absorption coefficient (m21) between 300 nm and 500 nm for pure water (cf. Fig. 12),
      as a function of the wavelength (l as nm). The column denoted aw1 corresponds to the absorption values proposed
      by Buiteveld et al. (1994), which are based on the attenuation values determined by Boivin et al. (1986)
      at 254, 313, and 366 nm. The values beyond 420 nm are those of Pope and Fry (1997).
      A smooth interpolation connects the value of Boivin at 366 nm and that of Pope and Fry at 420 nm.
      The column denoted aw2 corresponds to the absorption values deduced from the attenuation values obtained by
      Quickenden and Irvin (1980) (between 196 nm and 320 nm). The fitted values (between 300 and 320 nm; see Fig. 12)
      are connected (at 366 nm) to the aw1 values. The scattering coefficients (at 20uC) for optically pure seawater,
      bsw (m21) are derived from the values proposed by Buiteveld et al. (1994), increased by a factor of 1.30 to
      account for the presence of salt (at a mean salinity of 36); the backscattering coefficient of pure seawater,
      bbsw (m21), is half the scattering coefficient.
      The attenuation coefficient for downwelling irradiance in hypothetical pure seawater, Kdsw, displayed in Fig. 6,
      is computed according to the approximation (underestimation) Kdsw1 5 aw1 + bbsw, or Kdsw2 5 aw2 + bbsw."""
    ],
    'quickenden80_b': [
        'pure water',
        """ André Morel, Bernard Gentili, Hervé Claustre, Marcel Babin, Annick Bricaud, Joséphine Ras, Fanny Tièche
            Optical properties of the "clearest" natural waters (2007)

            Tabel 2b:
            The column denoted aw2 corresponds to the absorption values deduced from the attenuation 
            values obtained by Quickenden and Irvin (1980) (between 196 nm and 320 nm)."""
    ],

    'straw21': [
        'deep sea water',
        """STRAW - Team "Two-year optical site characterization for the Pacific Ocean Neutrino Experiment (P-{ONE}) 
      in the Cascadia Basin" (2021)"""
    ],

}

morel77_df = pandas.DataFrame(
    columns=['wavelength', 'attenuation', 'scattering', 'absorption'],
    data=[[380, 0.030, 0.0073, 0.023],
          [390, 0.027, 0.0066, 0.020],
          [400, 0.024, 0.0058, 0.018],
          [410, 0.022, 0.0052, 0.017],
          [420, 0.021, 0.0047, 0.016],
          [430, 0.013, 0.0043, 0.015],
          [440, 0.019, 0.0039, 0.015],
          [450, 0.018, 0.0035, 0.015],
          [460, 0.019, 0.0032, 0.016],
          [470, 0.019, 0.0029, 0.016],
          [480, 0.021, 0.0027, 0.018],
          [490, 0.022, 0.0024, 0.020],
          [500, 0.028, 0.0022, 0.026],
          [510, 0.038, 0.0020, 0.036],
          [520, 0.050, 0.0018, 0.048],
          [530, 0.053, 0.0017, 0.051],
          [540, 0.058, 0.0016, 0.056],
          [550, 0.066, 0.0015, 0.064],
          [560, 0.072, 0.0013, 0.071],
          [570, 0.081, 0.0013, 0.080],
          [580, 0.109, 0.0012, 0.108],
          [590, 0.158, 0.0011, 0.157],
          [600, 0.245, 0.00101, 0.245],
          [610, 0.290, 0.00094, 0.290],
          [620, 0.310, 0.00088, 0.310],
          [630, 0.320, 0.00088, 0.320],
          [640, 0.330, 0.00076, 0.330],
          [650, 0.350, 0.00071, 0.350],
          [660, 0.410, 0.00067, 0.410],
          [670, 0.450, 0.00063, 0.450],
          [680, 0.450, 0.00059, 0.450],
          [690, 0.500, 0.00055, 0.500],
          [700, 0.650, 0.00052, 0.650]])

morel77_df['publication'] = 'morel77_b'
morel77_df['medium'] = 'pure water'

# The following two datasets come from:
morel07_df = pandas.DataFrame(
    columns=['wavelength', 'absorption', 'scattering'],
    data=[[300, 0.03820, 0.0226],
          [305, 0.03350, 0.0211],
          [310, 0.02880, 0.0197],
          [315, 0.02515, 0.0185],
          [320, 0.02150, 0.0173],
          [325, 0.01875, 0.0162],
          [330, 0.01600, 0.0152],
          [335, 0.01395, 0.0144],
          [340, 0.01190, 0.0135],
          [345, 0.01050, 0.0127],
          [350, 0.00910, 0.0121],
          [355, 0.00810, 0.0113],
          [360, 0.00710, 0.0107],
          [365, 0.00656, 0.0099],
          [370, 0.00602, 0.0095],
          [375, 0.00561, 0.0089],
          [380, 0.00520, 0.0085],
          [385, 0.00499, 0.0081],
          [390, 0.00478, 0.0077],
          [395, 0.00469, 0.0072],
          [400, 0.00460, 0.0069],
          [405, 0.00460, 0.0065],
          [410, 0.00460, 0.0062],
          [415, 0.00457, 0.0059],
          [420, 0.00454, 0.0056],
          [425, 0.00475, 0.0054],
          [430, 0.00495, 0.0051],
          [435, 0.00565, 0.0049],
          [440, 0.00635, 0.0047],
          [445, 0.00779, 0.0044],
          [450, 0.00922, 0.0043],
          [455, 0.00951, 0.0040],
          [460, 0.00979, 0.0039],
          [465, 0.01011, 0.0037],
          [470, 0.01060, 0.0035],
          [475, 0.01140, 0.0034],
          [480, 0.01270, 0.0033],
          [485, 0.01360, 0.0031],
          [490, 0.01500, 0.0030],
          [495, 0.01730, 0.0029],
          [500, 0.02040, 0.0027]])
morel07_df['publication'] = 'morel07'
morel07_df['medium'] = 'pure water'

quickenden80_df = pandas.DataFrame(
    columns=['wavelength', 'absorption'],
    data=[[300, 0.01150, ],
          [305, 0.01100, ],
          [310, 0.01050, ],
          [315, 0.01013, ],
          [320, 0.00975, ],
          [325, 0.00926, ],
          [330, 0.00877, ],
          [335, 0.00836, ],
          [340, 0.00794, ],
          [345, 0.00753, ],
          [350, 0.00712, ],
          [355, 0.00684, ],
          [360, 0.00656, ],
          [365, 0.00629, ],
          [370, 0.00602, ]
          ])

quickenden80_df['publication'] = 'quickenden80_b'
quickenden80_df['medium'] = 'pure water'

straw21_df = pandas.DataFrame(
    columns=['wavelength', 'absorption'],
    data=[[365, 1. / 10.4],
          [400, 1. / 14.6],
          [450, 1. / 27.7],
          [585, 1. / 7.1]])
straw21_df['publication'] = 'straw21'
straw21_df['medium'] = 'deep sea water'
