import cv2
import numpy as np
import h5py
import os

from ...config_parser.config_parser import Config


class FileHandler:
    """Everything related to a single hdf5 file. The RAW image data is accessed directly
    form the hdf5 file to save RAM. It is capable of determine invalid pictures (property: invalid_mask)
    and takes the n darkest pictures as an average for a dark frame. It also includes the
    basic functions to demosaic the raw data into RGB values for both, multiple frames or a single frame"""
    bayer_pattern_dict = {  # "COLOR_BAYER_BG2BGR_EA":cv2.COLOR_BAYER_BG2BGR_EA,
        # "COLOR_BAYER_GB2BGR_EA":cv2.COLOR_BAYER_GB2BGR_EA,
        # "COLOR_BAYER_RG2BGR_EA":cv2.COLOR_BAYER_RG2BGR_EA,
        # "COLOR_BAYER_GR2BGR_EA":cv2.COLOR_BAYER_GR2BGR_EA,
        "COLOR_BAYER_BG2RGB_EA": cv2.COLOR_BAYER_BG2RGB_EA,  # <- that's what we need
        # "COLOR_BAYER_GB2RGB_EA":cv2.COLOR_BAYER_GB2RGB_EA,
        # "COLOR_BAYER_RG2RGB_EA":cv2.COLOR_BAYER_RG2RGB_EA, # <- default
        # "COLOR_BAYER_GR2RGB_EA":cv2.COLOR_BAYER_GR2RGB_EA,
    }
    bayer_pattern = cv2.COLOR_BAYER_BG2RGB_EA  # <- that's what we need as cv2 exports BGR -> BG2 instead of RG2

    def __init__(self, file_name=None, module=None):
        if file_name is None:
            self.file_name = None
        elif os.path.exists(file_name):
            self.file_name = os.path.abspath(file_name)
        elif os.path.exists(os.path.join(Config.raw_data_dir, file_name)):
            path = os.path.join(Config.raw_data_dir, file_name)
            self.file_name = os.path.abspath(path)
        else:
            raise FileNotFoundError(file_name)

        # in case, extract the module name from the filename
        if module is None:
            # '...le_data/TUMMINISPECTROMETER001_202104...' -> 'MINISPECTROMETER001'
            self.module = file_name.rsplit('/', 1)[-1].split('_', 1)[0].replace('TUM', '')
        else:
            self.module = module

        # RAW MetaData
        self.index_in_file = None  # the index of the specific measurement in the file, as the arrays may be sorted
        self.exposure_time = None  # exposure time per measurement in seconds: float, [0...~63s]
        self.gain = None  # gain per measurement: int, [0...100]
        self.EffMargins = None  # pixels margin after the demosaicing in pixels: int, [left, right, top, bottom]
        self.time = None  # time of the measurement since epoch in seconds [precision us]: float

        # Lucifer options: opt: -127 or 0 off, 1 Torch, 2 Flash; addr: 0 all, [1..4] single
        self.lucifer_options = None  # [[opt, addr, current, duration]]
        self.integrated_raw = None  # processed but close to raw, sum over all pixels per image
        self.raw_resolution = None

        # processed Data - !! have to be set to non after an append in the CameraModuleHandler !!
        self._raw_dark_frame = None  # for property
        self._rgb_dark_frame = None  # for property
        self._invalid_mask = None  # for property
        self._integrated_minus_dark = None  # for property
        self._max_value_minus_dark = None

        if self.file_name is not None:
            self.load_meta_data()

    # ---- Properties ----
    @property
    def integrated_minus_dark(self, ):
        if self._integrated_minus_dark is None:
            self._integrated_minus_dark = self.cal_integrated_minus_dark()

        return self._integrated_minus_dark

    @property
    def invalid_mask(self, ):
        if self._invalid_mask is None:
            self.create_invalid_mask()
        return self._invalid_mask

    def create_invalid_mask(self, limit=2e10):
        self._invalid_mask = self.integrated_raw > limit

    @property
    def raw_dark_frame(self):
        if self._raw_dark_frame is None:
            self.cal_raw_dark_frame()
        return self._raw_dark_frame

    def cal_integrated_minus_dark(self, ):
        raw = self.load_raw(exclude_invalid=False)  # exclude_invalid=False as the length hast to match
        raw = raw - self.raw_dark_frame  # subtract the dark frame
        raw = self.cut2effective_pixel_arr(raw)
        raw[raw < 4e4] = 0  # cut the noise
        raw = raw ** 2  # Chi**2
        return np.average(raw.reshape((raw.shape[0], -1)), axis=-1)

    def cal_raw_dark_frame(self, n=None):
        """Takes the 'n' most dim pictures in the series to calculate the dark frame"""
        self._integrated_minus_dark = None

        if n is None:
            n = 10
        n = int(n)
        integrated_raw_masked = np.ma.array(self.integrated_raw, mask=~self.invalid_mask)
        index = np.ma.argsort(integrated_raw_masked)  # masked items count as greatest
        self._raw_dark_frame = np.average(self.load_raw(index[:n]), axis=0)  # n=10

    def get_index(self, index=None, exclude_invalid=True):
        if index is None:
            index = np.arange(self.index_in_file.shape[0])

        elif type(index) is int:
            index = [index]

        index_in_file = self.index_in_file[index]

        if exclude_invalid:
            index_in_file = index_in_file[self.invalid_mask[index]]

        return index, index_in_file

    # ---- Load and sort data ----
    def load_raw(self, index=None, exclude_invalid=True):
        """exclude_invalid only works with index=None"""
        index, index_in_file = self.get_index(index=index, exclude_invalid=exclude_invalid)

        with h5py.File(self.file_name, 'r') as f:
            raw_table = f['camera/raw']
            # the indexes for the access have to be sorted (restriction of h5py)
            raw = raw_table[index_in_file[np.argsort(index_in_file)]]

        return raw[np.argsort(np.argsort(index_in_file))]  # revert sort

    def load_meta_data(self, ):
        with h5py.File(self.file_name, 'r') as f:
            raw_table = f['camera/raw']
            self.EffMargins = f['camera'].attrs['EffMargins']
            self.raw_resolution = raw_table.shape[1:]

            self.integrated_raw = np.sum(np.sum(raw_table, axis=-1), axis=-1)
            self.index_in_file = np.arange(self.integrated_raw.shape[0])
            self.time = (f['camera/time'][:] * 1e6).astype('datetime64[us]')
            self.exposure_time = f['camera/exposure_time'][:]
            self.gain = f['camera/gain'][:]
            self.lucifer_options = f['camera/lucifer_options'][:]

    def time_sort(self, ):
        index = np.argsort(self.time)
        self.index_in_file = self.index_in_file[index]
        self.exposure_time = self.exposure_time[index]
        self.gain = self.gain[index]
        self.time = self.time[index]
        self.integrated_raw = self.integrated_raw[index]
        self.lucifer_options = self.lucifer_options[index]
        self._invalid_mask = None
        self._integrated_minus_dark = None
        return index  # for overloading

    # ---- RGB related stuff (maybe move to another class inheriting from FileHandler) ----
    @property
    def rgb_dark_frame(self):
        if self._rgb_dark_frame is None:
            self.cal_rgb_dark_frame()
        return self._rgb_dark_frame

    def cal_rgb_dark_frame(self):
        """Takes the 'n' most dim pictures in the series to calculate the dark frame"""
        self._rgb_dark_frame = cv2.cvtColor(self.raw_dark_frame.astype(np.uint16),
                                            self.bayer_pattern)

    def cut2effective_pixel_single(self, rgb):
        return np.array(rgb)[self.EffMargins[0]:-self.EffMargins[1], self.EffMargins[2]:-self.EffMargins[3]]

    def cut2effective_pixel_arr(self, rgb_arr):
        return np.array(rgb_arr)[:, self.EffMargins[0]:-self.EffMargins[1], self.EffMargins[2]:-self.EffMargins[3]]

    def frame_raw_to_rgb(self, frame_raw):
        """Values have to be from [0...2**16-1] i.e. np.uint16."""
        frame_raw[frame_raw < 0] = 0  # correct for negative entries
        bgr = cv2.cvtColor(frame_raw.astype(np.uint16), self.bayer_pattern)  # cv2 exports BGR
        return bgr  # [:,:,::-1] BGR -> RGB

    def load_rgb(self, index=None, subtract_dark=True, **kwargs):

        raw_arr = self.load_raw(index, **kwargs)

        if subtract_dark:
            raw_arr = raw_arr - self.raw_dark_frame

        image_list = []
        for i, raw_i in enumerate(raw_arr):
            image_list.append(self.frame_raw_to_rgb(raw_i))

        image_arr = self.cut2effective_pixel_arr(image_list)
        return image_arr

    def image2png(self, f_name_formatter='{datetime}', directory='{proc_data_dir}/{module}',
                  bit=8, index=None, overwrite=False, file_name_iterator=None, ending='.png', **kwargs):
        """f_name has to include at least on of the formatter_dict.keys

        PARAMETER
        ---------
        f_name_formatter: str, optional
            Defines the filename for each image. Possible placeholders are: {datetime}, {index_in_file}, {index} and {i}
            they can be combined. {i} is a placeholder for 'file_name_iterator'. See 'file_name_iterator' for more.
        index: List[int] or None, optional
            Specifies the which images are saved. The index is the index in the raw file. None (Default) is the
            placeholder for all images in the file.
        directory: str, optional,
            can have a placeholders {module} or {proc_data_dir} which will be replaced with module name or the directory
            for the processed STRAWb data specified in thee config file. Default is '{proc_data_dir}/{module}'.
        ending: str, optional
            can be one of '.png' or '.jpg'. The ending is added automatically if the f_name_formatter doesn't end with
            the ending.
        overwrite: bool, optional
            If False (Default) existing files will not be overwritten.
        file_name_iterator: list or None, optional
            Has to match with the 'index' length. Each element is replaced with the '{i}' placeholder in 'f_name_formatter'.
            e.g. f_name_formatter='file_{i}', file_name_iterator=[1,2,3] -> file_1, file_2, file_3
        """

        if not f_name_formatter.endswith(ending):
            f_name_formatter += ending

        index, index_in_file = self.get_index(index=index, **kwargs)

        rgb = self.load_rgb(index=index, **kwargs)

        # get bit's right, default is 16bit
        bit = int(bit)
        bit_dict = {8: np.uint8, 16: np.uint16}
        if bit == 8:
            rgb = rgb / 2 ** 16 * 2 ** 8  # - 1

        rgb[rgb == 2 ** bit] = rgb[rgb == 2 ** bit] - 1
        rgb = rgb.astype(bit_dict[bit])

        # prepare directory
        directory = os.path.abspath(directory.format(module=self.module,
                                                     proc_data_dir=Config.proc_data_dir))
        os.makedirs(directory, exist_ok=True)

        for i, index_i in enumerate(index):
            # prepare file name, get time to correct format
            date_i = self.time[index_i].astype('datetime64[s]')
            str_date_i = str(date_i).replace(':', '_').replace('.', '_').replace('-', '_').replace('T', '_')

            formatter_dict = {'datetime': str_date_i,
                              'index_in_file': index_in_file[i],
                              'index': index_i,
                              'i': i}
            if file_name_iterator is not None:
                formatter_dict['i'] = file_name_iterator[i]

            f_name_i = f_name_formatter.format(**formatter_dict)
            f_name_target_i = os.path.join(directory, f_name_i)
            if os.path.exists(f_name_target_i) and overwrite:
                print('skip:', f_name_target_i)
            else:
                print('save:', f_name_target_i)
                cv2.imwrite(f_name_i, rgb[i, :, :, ::-1])  # [:,:,::-1] as cv2 takes BGR and not RGB
                os.replace(os.path.join(os.path.abspath('.'), f_name_i), f_name_target_i)  # move file

    def get_lucifer_mask(self, mode_list=None):
        """ mode_list is something like [2, 0, 15, 7] or [1, 1, 15, -125] ([mode, addr, current, duration])"""
        if mode_list is None:
            mode_list = np.unique(self.lucifer_options, axis=0)
            # in the following line, only 'mode_list[:, 0] == -125' without np.argwhere raise an FutureWarning
            mode_list = np.delete(mode_list, np.argwhere(mode_list[:, 0] == -125), axis=0)  # remove lucifer off

        mask_list = []
        for i in mode_list:
            mask_list.append(np.all(self.lucifer_options == i, axis=-1))

        return mode_list, mask_list

    def image2png_lucifer(self, options=None, **kwargs):
        mode_dict = {-125: 'OFF', 0: 'OFF', 1: 'TORCH', 2: 'FLASH'}
        index, index_in_file = self.get_index()

        mode_list, mask_list = self.get_lucifer_mask()
        for mode_i, mask_i in zip(mode_list, mask_list):
            out_str = [mode_dict[mode_i[0]]]
            for i_i in mode_i[1:]:
                if i_i != -125:
                    out_str.append(str(i_i))
            out_str = '_'.join(out_str)
            self.image2png(index=index[mask_i], directory='{proc_data_dir}/{module}/' + out_str, **kwargs)
