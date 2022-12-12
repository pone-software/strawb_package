import os

import pandas

from strawb.calibration.base_dataset_handler import DatasetHandler


class Laser(DatasetHandler):
    """
    Dataset with relative the laser emission profile for different pulse width configs:
    https://www.thorlabs.com/thorproduct.cfm?partnumber=NPL45B
    (Data got extracted directly from the vector data (.pdf) to ensure accuracy)

    Laser specs (NPL45B):
    Center Wavelength (Typical): 450 nm ± 10 nm
    FWHM Min: 5 ns ± 1 ns
    FWHM Max: 39 ns ± 3 ns 2
    Internal Trigger: Yes (1, 5, or 10 MHz)
    Max Trigger Frequency: 10 MHz
    Pulse Energy, Max: 3.0 nJ
    Average Power, Max: 30 mW
    Peak Power, Max: 75 mW
    Beam Pointing Accuracy: ≤3°
    Beam Divergence (1/e2), Typical: 0.5 mrad (Major Axis) 0.25 mrad (Minor Axis)
    Beam Full Width (1/e2) at 5.0 m: 3.3 mm (Major Axis) 1.6 mm (Minor Axis)
    Collimating Lens: C610TME-A

    Trigger Specifications:
    ...
    Max Jitter RMS: 20 ps
    Max Jitter Peak-to-Peak: 100 ps
    Delay From External Trigger Input to Optical Output: 35 ns ± 5 ns
    Delay From Internal Trigger Output to Optical Output: 28 ns ± 5 ns

    config_parameters is a DataFrame with the columns:
    time-ns,optical_power-mW,label

    EXAMPLE
    -------
    >>> import strawb.calibration
    >>> import matplotlib.pyplot as plt
    >>>
    >>> plt.figure()
    >>> for i in strawb.calibration.Laser.available_labels:
    >>>     laser = strawb.calibration.Laser(label=i)
    >>>     plt.plot(laser.time, laser.power, label=laser.label)
    >>> plt.legend()
    >>> plt.grid()
    >>> plt.xlabel('time [ns]')
    >>> plt.ylabel('optical power [mW]')
    >>> plt.yscale('log')
    >>> plt.tight_layout()
    """
    local_path = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    config_parameters = pandas.read_csv(os.path.join(local_path, 'lidar_laser-NPL45B-timeprofile.csv'))
    available_labels = list(config_parameters['label'].unique())

    def __init__(self, label=None):
        self._time_ = None
        self._power_ = None
        DatasetHandler.__init__(self, label=label)

    @property
    def time(self):
        """Time in ns"""
        return self._time_

    @property
    def power(self):
        """power in mW"""
        return self._power_

    def _load_data_(self, mask):
        self._time_ = self.config_parameters.loc[mask, 'time-ns']
        self._power_ = self.config_parameters.loc[mask, 'optical_power-mW']

    def _free_data_(self):
        self._time_ = None
        self._power_ = None
