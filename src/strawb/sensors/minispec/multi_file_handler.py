import numpy as np
import h5py
import os
from datetime import datetime
from datetime import timedelta

from ...config_parser import Config
from strawb.sensors.minispec.file_handler import FileHandler

class MultiFileHandler:
    def __init__(self, file_name_list):
        self.file_name_list = file_name_list
        for file_name in file_name_list:
            if file_name is None:
                self.file_name = None
            elif os.path.exists(file_name):
                self.file_name = os.path.abspath(file_name)
            elif os.path.exists(os.path.join(Config.raw_data_dir, file_name)):
                path = os.path.join(Config.raw_data_dir, file_name)
                self.file_name = os.path.abspath(path)
            else:
                raise FileNotFoundError(file_name)

        #check if they are from the same devices
        self.module_name = None
        module_name_list = []
        for file_name in file_name_list:
            self.module_name = file_name.rsplit('/', 1)[-1].split('_', 1)[0].replace('TUM', '')
            module_name_list.append(self.module_name)
        check_values = ["MINISPECTROMETER001","PMTSPECTROMETER001","PMTSPECTROMETER002"]
        if (all(name in check_values for name in module_name_list))\
                and (all(name == module_name_list[0] for name in module_name_list)):
            pass
        else:
            raise ValueError("cannot combine files from different module")

        #for simplicity, multi file only store wavelength attributes,start and end time
        #as well as ADC accounts
        self.start_time = None
        self.end_time = None
        self.WAVELENGTH_ARR = None
        self.ADC_counts_dict_0 = {}
        self.ADC_counts_dict_1 = {}
        self.ADC_counts_dict_2 = {}
        self.ADC_counts_dict_3 = {}
        self.ADC_counts_dict_4 = {}

        #check if date_time in file_name_list are uninterrupted,
        #if uninterrupt -> combine; else -> remind  -> combine
        self.check_uninterruption(self)
        self.time_combine(self)

    @staticmethod
    def check_uninterruption(self):
        start_datetime_list = np.empty(shape=(len(self.file_name_list),), dtype=object)
        end_datetime_list = np.empty(shape=(len(self.file_name_list),), dtype=object)
        minimal_gap = timedelta(minutes=5.0)
        for i in range(0,len(self.file_name_list)):
            file_name=self.file_name_list[i]
            single_file = FileHandler(file_name)
            start_datetime_list[i]=single_file.start_time
            end_datetime_list[i]=single_file.end_time
        if start_datetime_list[1:]-end_datetime_list[:-1] < minimal_gap:
            pass
        else:
            print("there are large time gap between the input files, make sure you want to combine")
            
    @staticmethod
    def time_combine(self):
        #fill the data into class, first let's fill time and wavelength
        first_file = FileHandler(self.file_name_list[0])
        self.start_time = first_file.start_time
        last_file = FileHandler(self.file_name_list[-1])
        self.start_time = last_file.end_time
        self.WAVELENGTH_ARR = first_file.data_array[0].WAVELENGTH_ARR

        #now fill the ADC count and update
        for file_name in self.file_name_list:
            single_file = FileHandler(file_name)
            datetime_str = file_name.split("_")[1][0:15] #datetime string as dictionary key
            
            #input data into dict
            self.WAVELENGTH_ARR= single_file.data_array[0].WAVELENGTH_ARR
            if self.module_name == "MINISPECTROMETER001":
                self.ADC_counts_dict_0[datetime_str] = single_file.data_array[0].ADC_counts
                self.ADC_counts_dict_1[datetime_str] = single_file.data_array[1].ADC_counts
                self.ADC_counts_dict_2[datetime_str] = single_file.data_array[2].ADC_counts
                self.ADC_counts_dict_3[datetime_str] = single_file.data_array[3].ADC_counts
                self.ADC_counts_dict_4[datetime_str] = single_file.data_array[4].ADC_counts
            elif self.module_name == "PMTSPECTROMETER001" or "PMTSPECTROMETER002":
                self.ADC_counts_dict_0[datetime_str] = single_file.data_array[0].ADC_counts