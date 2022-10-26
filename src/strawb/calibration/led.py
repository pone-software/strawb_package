import os

import pandas


class LED:
    """
    Dataset with relative radiation power for different LEDs from:
    CREE LED: https://assets.cree-led.com/a/ds/x/XLamp-XPG3.pdf
    CREE LED: https://assets.cree-led.com/a/ds/x/XLamp-XPE2.pdf
    LUMINUS : https://download.luminus.com/datasheets/Luminus_SST-10-UV_Datasheet.pdf
    (Data got extracted directly from the vector data (.pdf) to ensure accuracy)

    config_parameters is a DataFrame with the columns:
    label,type,wavelength,relative_radiation

    In STRAWb use the following LEDs:
    config_parameters.label == '5000K_70CRI'   # White LED
    config_parameters.label == 'Royal Blue'  # Blue LED
    config_parameters.label == '365 nm'  # UV LED

    Arrangement of the LEDs in STRAWb
    https://transfer.ktas.ph.tum.de/wiki/dokuwiki/doku.php?id=straw_b:electronics:list_of_modules
    address/color -> 1W = 51/white; hz = horizontal, dw=downwards, up=upwards, W/U/B = white/ultraviolet/blue
    muon, lidar's = 1W,2U,3W,4U  - position: 1W hz, 2U hz, 3W dw, 4U dw
    PMTSpec's     = 1W,3W        - position: 1W up, 3W up
    Art 1,2,3,4   = 1W,2B        - position: 1W hz, 2B hz
    """
    local_path = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    config_parameters = pandas.read_csv(os.path.join(local_path, 'strawb_leds.csv'))

    led_labels = list(config_parameters.label.unique())

    def __init__(self, label=None):
        self._wavelength_ = None
        self._relative_radiation_ = None

        # set the label and check if it a valid label
        self.label = label

    @property
    def wavelength(self):
        """Wavelength in nm"""
        return self._wavelength_

    @property
    def relative_radiation(self):
        """relative radiation: [0,1]"""
        return self._relative_radiation_

    @property
    def label(self):
        """label of the LED in the config_parameters dataset"""
        return self._label_

    @label.setter
    def label(self, label):
        """Set the label of the LED and loads the data from the config_parameters dataset
        Label must be a value in config_parameters.label or None."""
        if label is not None:
            self._wavelength_ = None
            self._relative_radiation_ = None
        if label is not None:
            if label not in self.led_labels:
                raise ValueError(f'label must be one of: {self.led_labels}. Got: {label}')
            mask = self.config_parameters.label == label
            self._wavelength_ = self.config_parameters.wavelength[mask]
            self._relative_radiation_ = self.config_parameters.relative_radiation[mask]
