import numpy as np
import h5py
import os

from ...config_parser.config_parser import Config
import minispec_calibration
import device_handler

class FileHandler:
    def __init__(self, file_name=None):
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
    #check if file is from MINISPECTROMETER001
    if self.module == "MINISPECTROMETER001":
        pass
    else:
        raise ValueError('This device doesn\'t have multi minispecs.')

    self.device_container = []


    def load_devices(self, number_of_devices): #for example number_of_devices=[1,2,3,4,5]
        for number_i in number_of_devices:
            device = device_handler(filename=self.file_name,device_number=number_i)
            device.load_meta_data()
            device_container.append(device)

    def plot_all_spectrums(self):