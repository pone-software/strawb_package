import numpy as np
import h5py
import os
import matplotlib.pyplot as plt

from ...config_parser.config_parser import Config
from src.strawb.sensors.minispec.minispec_calibration import DarkCountFit
from src.strawb import ONCDownloader

#This class only handle device 1 by default.
#There are 5 devices on MINISPECTROMETER001  module, to handle them all, check multi_devices_handler.py

class DeviceHandler:
    def __init__(self, file_name=None,darkcount_cal=False,wavelength_cal=False,device_number=1):
        if file_name is None:
            self.file_name = None
        elif os.path.exists(file_name):
            self.file_name = os.path.abspath(file_name)
        elif os.path.exists(os.path.join(Config.raw_data_dir, file_name)):
            path = os.path.join(Config.raw_data_dir, file_name)
            self.file_name = os.path.abspath(path)
        else:
            raise FileNotFoundError(file_name)

        #from which module is this minispec device
        self.module = file_name.rsplit('/', 1)[-1].split('_', 1)[0].replace('TUM', '')
        self.device_number = device_number

        # initial device fixed data
        self.CAL_ARR = None  # calibration array
        self.W1_UID = None  # device series number: int
        self.WAVELENGTH_ARR = None  # wavelength array

        # initial measured data
        self.ADC_counts = None  # shape=(862, 288), 288 pixels, 862 frequency of measurement
        self.ADC_counts_cal = np.zeros((862,288))
        self.exposure_time = None  # shape=(862,)
        self.temperature_after = None  # shape=(862,)
        self.temperature_before = None  # shape=(862,)
        self.time = None  # shape=(862,)
        self.trigger_counter = None  # shape=(862,)

        #calibtration status
        self.if_wavcal = False
        self.if_darksub = False

        if self.file_name is not None:
            self.load_meta_data()

        self.calibration_obj = DarkCountFit(self)
        if darkcount_cal:
            self.calibrate_adc_counts()
            self.if_darksub =True

        if wavelength_cal:
            self.calculate_wavelength(self)
            self.if_wavecal = True

    #auxiliary functions
    def load_meta_data(self):
        with h5py.File(self.file_name, 'r') as f:
            device_key = str(self.device_number)
            dset1 = f[device_key]

            self.CAL_ARR = dset1.attrs['CAL.ARR']
            self.W1_UID = dset1.attrs['W1 UID']
            self.WAVELENGTH_ARR = dset1.attrs['WAVELENGTH.ARR']

            #TODO: need unit convert ?
            self.ADC_counts = dset1['ADCcounts'][:]
            self.exposure_time = float(dset1['exposure_time'][:]) / 1.e6  # convert us to s
            self.temperature_after = dset1['temperature_after'][:]
            self.temperature_before = dset1['temperature_before'][:]
            self.time = dset1['time'][:]
            self.trigger_counter = dset1['trigger_counter'][:]

    @staticmethod
    def calculate_wavelength(self):
        """"takes wavelength calibration parameters
        and returns calibrated wavelength (w_i) for all 288 pixel
        from a_0 + b_1*pix_id**1 + b_2*pix_id**2 + b_3*pix_id**3 + b_4*pix_id**4 + b_5*pix_id**5

        example usage:
        # wavelength(*get_param(0xe300000b18ef6228))
        """
        if self.if_wavcal is True:
            pass
        elif self.if_wavcal is False:
            pix = np.arange(288.)
            self.WAVELENGTH_ARR = self.CAL_ARR[0] + self.CAL_ARR[1] * pix + self.CAL_ARR[2] * pix ** 2 + \
                   self.CAL_ARR[3]* pix ** 3 + self.CAL_ARR[4] * pix ** 4 + self.CAL_ARR[5] * pix ** 5


    def calibrate_adc_counts(self):
        """ subtract calculated dark counts
        the opt parameters were taken from minispec_calibration.py, class DarkCountFit, fit_loop_pixel()
        almost all measurements are dark, no need to select particular events.
        """
        calibration_obj = DarkCountFit(self)
        opt_parameters = calibration_obj.fit_loop_pixel()
        for pixel_number in range(288):
            for measurement_number in self.ADC_counts:
                 self.ADC_counts_cal = self.ADC_counts[measurement_number:pixel_number] - self.calibration_obj.darkcounts_fit_function(
                         self.exposure_time[measurement_number,],
                         self.temperature_after[measurement_number,],
                         *opt_parameters.reshape(calibration_obj.len_opt_parameter, 1, -1))

    def plot_simple(self, with_dark):
        """TODO: adjust label"""
        plt.plot(self.WAVELENGTH_ARR, self.ADC_counts_cal[:1],
                    #label=self.label,
                    #*args, **kwargs
                 )

        # show 2 plots if dark run included, else 1 plot
        if with_dark != None:
            widths = [1]
            heights = [2, 1]
            gs_kw = dict(width_ratios=widths, height_ratios=heights)
        else:
            widths = [1]
            heights = [1]
            gs_kw = dict(width_ratios=widths, height_ratios=heights)

        # create subplots
        fig, ax = plt.subplots(nrows=len(heights),
                               figsize=(7.5, 5),
                               gridspec_kw=gs_kw,
                               shareax=True,
                               squeeze=False)
        ax = ax.flatten()

        # additional settings
        # for ax_i in ax:
        #     ax_i.grid()
        #     ax_i.legend()

        # additional settings for single plots and figure
        ax[0].set_xlim((self.WAVELENGTH_ARR.min(), self.WAVELENGTH_ARR.max()))
        ax[0].set_ylabel(r"$\Delta$Counts/Second")


        # additional settings for figure
        plt.xlabel("Wavelength [nm]")
        plt.legend()
        plt.tight_layout()


    def load_camera_picture_spectrum(self,device_code,name_of_picture):
        """given a name of camera's picture,for example 2021_05_01_19_19_34.png
        valid input for device_code see ONC_readme.md deviceCode
        plot the corresponding minispec spectrum"""
        date_list = name_of_picture.split("_")
        search_str = device_code + date_list[0]+date_list[1]+date_list[2]+"T000000.000Z-SDAQ-MINISPEC.hdf5"
        #check if minispec data exist
        if os.path.exists(os.path.join(Config.raw_data_dir, search_str)):
            path = os.path.join(Config.raw_data_dir, search_str)
            self.file_name = os.path.abspath(path)
            self.load_meta_data()
        else:
            downloader = ONCDownloader(showInfo=False)

            hour = int(name_of_picture[11:13])
            datefrom_str = name_of_picture.replace("_", "-")[:9]+"T"+str(hour)+":00:00.000Z"
            dateto_str = name_of_picture.replace("_", "-")[:9] + "T" + str(hour+1) + ":00:00.000Z"
            filters = {'deviceCode': device_code,
                       'dateFrom': datefrom_str,
                        'dateTo': dateto_str,
                        'extension': 'hdf5'}
            downloader.download_file(filters=filters, allPages=True)
            self.load_meta_data()

    def save_current_data_as_new_hdf5(self):
        #for convenient, only save important data
        if self.if_wavcal and self.if_darksub:
            new_name_set = (self.file_name).split(".")
            new_name = new_name_set[0]+"cal"+new_name_set[1]
            with h5py.File(new_name, 'w') as hf:
                hf.create_dataset('ADCcounts', (862,288),data=self.ADC_counts)
                #TODO:add others
                hf.close()
        else:
            raise ValueError('no change of data.')
