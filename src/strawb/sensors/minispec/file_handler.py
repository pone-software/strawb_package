import numpy as np

from strawb.base_file_handler import BaseFileHandler


class FileHandler(BaseFileHandler):
    def __init__(self, *args, **kwargs):
        self.mini_spectrometer_list = None

        # comes last to load the data in case file_name is set
        BaseFileHandler.__init__(self, *args, **kwargs)

    # auxiliary functions
    def __load_meta_data__(self):
        # create lucifer instances, depending on which are available in the file, Lucifer(ID) from hdf5 group lucifer_ID
        self.mini_spectrometer_list = []
        for i in self.file:
            if i.isnumeric() and int(i) in [1, 2, 3, 4, 5]:
                mini_spectrometer = SingleMiniSpectrometer(int(i.replace('lucifer_', '')))
                mini_spectrometer.__load_meta_data__(self.file)
                self.mini_spectrometer_list.append(mini_spectrometer)

        self.file_version = 1


class SingleMiniSpectrometer:
    # the object fill into FileHandler.data_array, each one represent a bridgette channel
    def __init__(self, index):
        """This class holds the parameters and measurements of one MiniSpectrometer.
        Parameter
        ---------
        index: int, str
            Index to identify the MiniSpectrometer. It corresponds to the port on the Brigette (SPI-Multiplexer).
        """
        # device specific parameters
        self.index = int(index)  # index to identify the MiniSpectrometer. It corresponds to the port on the Brigette.
        self.w1_uid = None  # device series number: int
        self.cal_arr = None  # wavelength calibration parameters
        self.wavelength_arr = None  # wavelength array [nm], calculated from `cal_arr`

        # measurement data
        self.time = None  # absolute timestamp of the data, shape=(n,)
        self.adc_counts = None  # data of 288 wavelength (pixel) per measurement, shape=(n, 288)
        self.exposure_time = None  # exposure time [seconds]
        self.temperature_before = None  # PCB temperature before the measurement [deg]
        self.temperature_after = None  # PCB temperature after the measurement [deg]
        self.trigger_counter = None  # trigger counter, counts one up for each measurement

    def __load_meta_data__(self, file):
        """ Loads the data the one MiniSpectrometer."""
        group = file[str(self.index)]

        # measurement data
        self.time = group['time']
        self.adc_counts = group['ADCcounts']
        self.exposure_time = group['exposure_time']
        self.temperature_before = group['temperature_before']
        self.temperature_after = group['temperature_after']
        self.trigger_counter = group['trigger_counter']

        # calibration parameters
        self.cal_arr = group.attrs['CAL.ARR']  # [a_0, b_1, b_2, b_3, b_4, b_5] <-> wavelength calibration polynomial
        self.w1_uid = group.attrs['W1 UID']  # the unique ID
        self.wavelength_arr = group.attrs['WAVELENGTH.ARR']  # the calculated wavelength from w1_uid

    def calculate_wavelength(self, cal_arr=None):
        """"Calculates the calibrated wavelength per pixel from the calibration parameters provided by Hamamatsu and
        stored in `self.cal_arr`. The calibration is done with a polynomial for all 288 pixel from:
        a_0 + b_1*pix_id**1 + b_2*pix_id**2 + b_3*pix_id**3 + b_4*pix_id**4 + b_5*pix_id**5
        with cal_arr = [a_0, b_1, b_2, b_3, b_4, b_5].

        Parameter
        ---------
        cal_arr: ndarray, optional
            calibration scalars for the polynomial with shape=(6,). Default is None, which takes the internal cal_arr
            parameters.
        Returns
        -------
        wavelength_arr: ndarray
            the calibrated wavelength in nm as a array with shape=(288,)
        """
        pix = np.arange(288.).reshape(-1, 1)  # 288 pixel
        i = np.arange(6).reshape(1, -1)  # index for sum
        if cal_arr is None:
            cal_arr = self.cal_arr.reshape(1, -1)  # calibration

        # The wavelength calibration polynomial: Sum over i=0->5 of self.cal_arr[i] * pix**i
        # or: a_0 + b_1*pix_id**1 + b_2*pix_id**2 + b_3*pix_id**3 + b_4*pix_id**4 + b_5*pix_id**5
        wavelength_arr = np.sum(pix ** i * cal_arr, axis=1)  # numpy version of wavelength calibration
        return wavelength_arr

    # def calibrate_adc_counts(self):
    #     """ subtract calculated dark counts
    #     the opt parameters were taken from minispec_calibration.py, class DarkCountFit, fit_loop_pixel()
    #     almost all measurements are dark, no need to select particular events.
    #     """
    #     for n in range(len(self.data_array)):  # n:select a channel
    #         # generate a DarkCountFit object and get fit parameter from it
    #         calibration_obj = DarkCountFit(self, n)
    #         opt_parameters = calibration_obj.fit_loop_pixel()
    #
    #         # calculation
    #         single_device = self.data_array[n]
    #         for pixel_number in range(self.ADC_shape[1]):
    #             for measurement_number in range(self.ADC_shape[0]):
    #                 single_device.ADC_counts_dark[
    #                 measurement_number:pixel_number] = calibration_obj.darkcounts_fit_function(
    #                     single_device.exposure_time[measurement_number],
    #                     single_device.temperature_after[measurement_number],
    #                     *opt_parameters.reshape(calibration_obj.len_opt_parameter, 1, -1))
    #
    #                 # subtract dark count
    #         single_device.ADC_counts_cal = single_device.ADC_counts - single_device.ADC_counts_dark

    #     def calibrate_adc_counts(self):
    #         """ subtract calculated dark counts
    #         the opt parameters were taken from minispec_calibration.py, class DarkCountFit, fit_loop_pixel()
    #         almost all measurements are dark, no need to select particular events.
    #         """
    #         calibration_obj = DarkCountFit(self)
    #         opt_parameters = calibration_obj.fit_loop_pixel()
    #         for pixel_number in range(288):
    #             for measurement_number in self.ADC_counts:
    #                 self.ADC_counts_cal = self.ADC_counts[measurement_number:pixel_number] -
    #                 self.calibration_obj.darkcounts_fit_function(
    #                     self.exposure_time[measurement_number,],
    #                     self.temperature_after[measurement_number,],
    #                     *opt_parameters.reshape(calibration_obj.len_opt_parameter, 1, -1))
