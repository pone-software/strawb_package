import datetime
from datetime import datetime
from datetime import timedelta

import h5py
import numpy as np

from strawb.base_file_handler import BaseFileHandler
from strawb.sensors.minispec.minispec_calibration import DarkCountFit


# This class only handle device 1 by default.
# There are 5 devices on MINISPECTROMETER001  module, to handle them all, check multi_files_handler.py

class FileHandler(BaseFileHandler):
    def __init__(self, darkcount_cal=False, wavelength_cal=False, *args, **kwargs):
        # time_step, which is useful when combine multiple files
        self.start_time = None
        self.end_time = None
        self.module = None
        self.device_number = None
        self.data_array = None
        self.ADC_shape = None

        self.if_wavecal = None
        self.if_darksub = None

        # calibration status
        if darkcount_cal:
            self.calibrate_adc_counts()
            self.if_darksub = True
        else:
            self.if_darksub = False

        if wavelength_cal:
            self.calculate_wavelength()
            self.if_wavecal = True
        else:
            self.if_wavecal = False

        self.all_attributes = None  # holds all hdf5-file attributes as dict

        # comes last to load the data in case file_name is set
        BaseFileHandler.__init__(self, *args, **kwargs)

    # auxiliary functions
    def open(self):
        # from which module is this minispec device? generate an array to store data from each device
        # if it is from pmtspec/minispec module, it has 1/5 devices
        if self.module == "MINISPECTROMETER001":
            self.device_number = 5
        elif self.module == "PMTSPECTROMETER001" or "PMTSPECTROMETER002":
            self.device_number = 1
        else:
            raise ValueError('unknown minispec device')

        # generate an object array to store data
        self.data_array = np.empty(shape=(self.device_number,), dtype=object)

        # start_time
        hdf5_name = self.file_name.rsplit('/', 1)[-1]
        datetime_str = hdf5_name.split("_")[1][0:15]
        print(datetime_str)
        self.start_time = datetime.strptime(datetime_str, "%Y%m%dT%H%M%S")

        # other data
        with h5py.File(self.file_name, 'r') as file:
            for i in range(1, self.device_number + 1):
                channel = i
                dset = file[str(channel)]

                get_ADC_counts_shape = dset['ADCcounts'][:]
                self.ADC_shape = np.shape(get_ADC_counts_shape)
                temp_spectrum = Spectrum(self.ADC_shape)

                temp_spectrum.CAL_ARR = dset.attrs['CAL.ARR']
                temp_spectrum.W1_UID = dset.attrs['W1 UID']
                temp_spectrum.WAVELENGTH_ARR = dset.attrs['WAVELENGTH.ARR']

                temp_spectrum.exposure_time = (dset['exposure_time'][:]) / 1e6  # convert us to s
                temp_spectrum.temperature_after = dset['temperature_after'][:]
                temp_spectrum.temperature_before = dset['temperature_before'][:]
                temp_spectrum.time = dset['time'][:]
                temp_spectrum.trigger_counter = dset['trigger_counter'][:]

                self.data_array[channel - 1] = temp_spectrum

        # this part check if this file is 24 hours complete
        with h5py.File(self.file_name, 'r') as file:
            dset = file['1']
            start = dset['time'][0]
            end = dset['time'][-1]
            if (86400 - (end - start)) <= 120:  # allow 2 min time gap
                # endtime
                self.end_time = self.start_time + timedelta(seconds=abs(end - start))
            else:
                print("be careful, this file is not 24 hours complete")
        file.close()

    def calculate_wavelength(self):
        """"takes wavelength calibration parameters
        and returns calibrated wavelength (w_i) for all 288 pixel
        from a_0 + b_1*pix_id**1 + b_2*pix_id**2 + b_3*pix_id**3 + b_4*pix_id**4 + b_5*pix_id**5
        example usage:
        # wavelength(*get_param(0xe300000b18ef6228))
        """
        if self.if_wavecal is True:
            print("wavelength is already calibrated")
        elif self.if_wavecal is False:
            for n in range(len(self.data_array)):
                pix = np.arange(288.)
                single_device = self.data_array[n]
                new_wavelength_array = single_device.CAL_ARR[0] + single_device.CAL_ARR[1] * pix + \
                                       single_device.CAL_ARR[2] * pix ** 2 + \
                                       single_device.CAL_ARR[3] * pix ** 3 + single_device.CAL_ARR[4] * pix ** 4 + \
                                       single_device.CAL_ARR[5] * pix ** 5
                print(new_wavelength_array)
                self.data_array[n].WAVELENGTH_ARR = new_wavelength_array
        self.if_wavecal = True

    def calibrate_adc_counts(self):
        """ subtract calculated dark counts
        the opt parameters were taken from minispec_calibration.py, class DarkCountFit, fit_loop_pixel()
        almost all measurements are dark, no need to select particular events.
        """
        for n in range(len(self.data_array)):  # n:select a channel
            # generate a DarkCountFit object and get fit parameter from it
            calibration_obj = DarkCountFit(self, n)
            opt_parameters = calibration_obj.fit_loop_pixel()

            # calculation
            single_device = self.data_array[n]
            for pixel_number in range(self.ADC_shape[1]):
                for measurement_number in range(self.ADC_shape[0]):
                    single_device.ADC_counts_dark[
                    measurement_number:pixel_number] = calibration_obj.darkcounts_fit_function(
                        single_device.exposure_time[measurement_number],
                        single_device.temperature_after[measurement_number],
                        *opt_parameters.reshape(calibration_obj.len_opt_parameter, 1, -1))

                    # subtract dark count
            single_device.ADC_counts_cal = single_device.ADC_counts - single_device.ADC_counts_dark


#     def calibrate_adc_counts(self):
#         """ subtract calculated dark counts
#         the opt parameters were taken from minispec_calibration.py, class DarkCountFit, fit_loop_pixel()
#         almost all measurements are dark, no need to select particular events.
#         """
#         calibration_obj = DarkCountFit(self)
#         opt_parameters = calibration_obj.fit_loop_pixel()
#         for pixel_number in range(288):
#             for measurement_number in self.ADC_counts:
#                 self.ADC_counts_cal = self.ADC_counts[
#                                       measurement_number:pixel_number] - self.calibration_obj.darkcounts_fit_function(
#                     self.exposure_time[measurement_number,],
#                     self.temperature_after[measurement_number,],
#                     *opt_parameters.reshape(calibration_obj.len_opt_parameter, 1, -1))      


class Spectrum:
    # the object fill into FileHandler.data_array, each one represent a bridgette channel
    def __init__(self, input_shape):
        # initial device fixed data
        self.CAL_ARR = None  # calibration array
        self.W1_UID = None  # device series number: int
        self.WAVELENGTH_ARR = None  # wavelength array

        # initial measured data
        self.ADC_counts = np.empty(
            shape=input_shape)  # shape=(n, 288), 288 wavelength pixels, n times of measurements per channel per file
        self.ADC_counts_cal = np.empty(shape=input_shape)  # shape=(n, 288)
        self.ADC_counts_dark = np.empty(shape=input_shape)
        self.exposure_time = None  # shape=(n,)
        self.temperature_after = None  # shape=(n,)
        self.temperature_before = None  # shape=(n,)
        self.time = None  # shape=(862,)
        self.trigger_counter = None  # shape=(n,)
