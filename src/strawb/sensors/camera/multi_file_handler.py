import glob
import os

import numpy as np
from tqdm import tqdm

from .file_handler import FileHandler
from ...config_parser.config_parser import Config


class MultiFileHandler(FileHandler):
    """Based on CameraRun it features the combination of multiple CameraRuns. This allows,
    e.g. to calculate the dark frame based on a bigger dataset."""

    def __init__(self, module, date, camera_run_list=None, number_files=None):
        FileHandler.__init__(self, module=module, file_name=None)  # keep it empty
        self.meta_data_run_index = None  # stores which meta data belongs to which item in the camera_run_list

        self.date = date  # used to search for filenames
        self.camera_run_list = camera_run_list

        if camera_run_list is None:
            self.load_all_from_path(date=date, number_files=number_files)
        else:
            self.camera_run_list = camera_run_list

    def load_all_from_path(self, path=None, date=None, number_files=None):
        """Loads all camera files from the path and the specified date.
        PARAMETER
        ---------
        path: str or None, optional
            The path where the raw hdf5 files are loaded. If None (default), it's the parameter from the config file.
        date: str or None, optional
            If None (default), it's the parameter from the config file. '20210429'
        """
        if path is None:
            path = Config.raw_data_dir

        if date is None:
            date = self.date

        search_string = f'TUM{self.module}*{date}*-SDAQ-CAMERA.hdf5'
        search_string = os.path.join(path, search_string)
        print(search_string)

        camera_run_list = []

        if self.meta_data_run_index is None:
            run_index = 0  # counts which meta data belongs to which item in the camera_run_list
        else:
            run_index = self.meta_data_run_index.max() + 1

        for i in tqdm(glob.glob(search_string)[:number_files]):
            try:
                cam_run_i = FileHandler(i)
                self.append(run_index, cam_run_i)
                camera_run_list.append(cam_run_i)
                run_index += 1
            except Exception as a:
                print(a)

        if self.camera_run_list is None:
            self.camera_run_list = camera_run_list
        else:
            self.camera_run_list.extend(camera_run_list)
        self.time_sort()

    def load_raw(self, index=None, exclude_invalid=True):

        if index is None:
            index = np.arange(self.integrated_raw.shape[0])
        else:
            index = np.array(index)

        if exclude_invalid:
            index = index[self.invalid_mask[index]]

        selected_index_run = self.meta_data_run_index[index]
        selected_index_in_file = self.index_in_file[index]

        # print(index, selected_index_run, selected_index_in_file)

        raw = np.zeros((len(index), *self.raw_resolution))
        dtype = raw.dtype
        for i in np.unique(selected_index_run):
            mask = selected_index_run == i
            raw_i = self.camera_run_list[i].load_raw(index=selected_index_in_file[mask],
                                                     exclude_invalid=exclude_invalid)
            dtype = raw_i.dtype  # to preserve the type, np.zeros is float64
            raw[mask] = raw_i

        return raw.astype(dtype)

    def cal_integrated_minus_dark(self, ):
        integrated_minus_dark = np.zeros(self.meta_data_run_index.shape[0])
        for i in np.unique(self.meta_data_run_index):
            mask = self.meta_data_run_index == i
            integrated_minus_dark_i = self.camera_run_list[i].cal_integrated_minus_dark()
            integrated_minus_dark[mask] = integrated_minus_dark_i
        return integrated_minus_dark

    def image2png(self, index=None, file_name_iterator=None, exclude_invalid=True, **kwargs):
        if index is None:
            index = np.arange(self.integrated_raw.shape[0])
        else:
            index = np.array(index)

        if exclude_invalid:
            index = index[self.invalid_mask[index]]

        selected_index_run = self.meta_data_run_index[index]
        selected_index_in_file = self.index_in_file[index]

        if file_name_iterator is None:
            file_name_iterator = np.arange(len(selected_index_in_file))

        for i in np.unique(selected_index_run):
            mask = selected_index_run == i
            self.camera_run_list[i].image2png(index=selected_index_in_file[mask],
                                              exclude_invalid=exclude_invalid,
                                              file_name_iterator=file_name_iterator[mask],
                                              **kwargs)

    def load_meta_data(self, ):
        pass  # this should be disabled in this class

    def append(self, run_index, camera_run):
        # self.raw = self.__append_single(self.raw, camera_run.raw)
        new_indexes = [run_index] * camera_run.integrated_raw.shape[0]

        self.meta_data_run_index = self.__append_single(self.meta_data_run_index, new_indexes)
        self.index_in_file = self.__append_single(self.index_in_file, camera_run.index_in_file)
        self.integrated_raw = self.__append_single(self.integrated_raw, camera_run.integrated_raw)
        self.exposure_time = self.__append_single(self.exposure_time, camera_run.exposure_time)
        self.gain = self.__append_single(self.gain, camera_run.gain)
        self.time = self.__append_single(self.time, camera_run.time)
        self.lucifer_options = self.__append_single(self.lucifer_options, camera_run.lucifer_options)

        self.EffMargins = camera_run.EffMargins
        self.raw_resolution = camera_run.raw_resolution

        # in case, the property calculates those values again.
        self._raw_dark_frame = None  # for property
        self._rgb_dark_frame = None  # for property
        self._invalid_mask = None  # for property
        self._integrated_minus_dark = None  # for property

    @staticmethod
    def __append_single(a, b):
        if a is None:
            return np.copy(b)  # converts also to an array
        elif b is None:
            return np.copy(a)  # converts also to an array
        else:
            return np.append(a, b, axis=0)

    def time_sort(self, ):
        index = FileHandler.time_sort(self)
        self.meta_data_run_index = self.meta_data_run_index[index]
        return index  # for overloading

# cam_mini_module = CameraModuleHandler('MINISPECTROMETER001', number_files=None)
# cam_mini_module.image2png_lucifer()
