import os
import shutil

import cv2
import numpy as np

from .file_handler import FileHandler
from ...config_parser import Config


class Images:
    """Everything related to a single hdf5 file. The RAW image data is accessed directly
    form the hdf5 file to save RAM. It is capable of determine invalid pictures (property: valid_mask)
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

    def __init__(self, file_handler):
        self.file_handler = file_handler

        if not isinstance(file_handler, FileHandler):
            raise ValueError(f'file_handler is no instance of strawb.sensors.camera.FileHandler.'
                             f'{type(file_handler)}')
        # elif self.file_handler.is_empty is None:  # protect against empty file
        #     raise ValueError(f'No file defined in file handler.')
        # elif self.file_handler.is_empty:  # protect against empty file
        #     raise FileExistsError(f'File {self.file_handler.file_name} is empty! Can not load {type(self).__name__}.')

        # processed Data
        self._integrated_raw = None
        self._raw_dark_frame = None  # for property
        self._rgb_dark_frame = None  # for property
        self._valid_mask = None  # for property
        self._integrated_minus_dark = None  # for property
        self._max_value_minus_dark = None

    def __del__(self):
        self.file_handler = None  # unlink

        del self._integrated_raw
        del self._raw_dark_frame
        del self._rgb_dark_frame
        del self._valid_mask
        del self._integrated_minus_dark
        del self._max_value_minus_dark

    # ---- Properties ----
    @property
    def integrated_raw(self):
        if self._integrated_raw is None:
            self._integrated_raw = np.sum(self.file_handler.raw,
                                          axis=(1, 2))  # sum over all pixels per image

        return self._integrated_raw

    @property
    def integrated_minus_dark(self, ):
        if self._integrated_minus_dark is None:
            self._integrated_minus_dark = self.cal_integrated_minus_dark()

        return self._integrated_minus_dark

    @property
    def valid_mask(self, ):
        """Images which are not detected as corrupt"""
        if self._valid_mask is None:
            self.create_valid_mask()
        return self._valid_mask

    def create_valid_mask(self, limit=None):
        """Detect which images which are corrupt if the integrated_raw is below the limit.
        With limit=None it takes:
        For gain=50 end exposure time= ~60s: limit = 2e10
        For gain=30 end exposure time= ~60s: limit = 4e9
        """
        if limit is None and np.unique(self.file_handler.gain)[0] == 30.:
            limit = 4e9
        elif limit is None and np.unique(self.file_handler.gain)[0] == 50.:
            limit = 2e10
        self._valid_mask = self.integrated_raw > limit

    @property
    def raw_dark_frame(self):
        if self._raw_dark_frame is None:
            self.cal_raw_dark_frame()
        return self._raw_dark_frame

    def load_raw(self, index=None, exclude_invalid=True):
        """exclude_invalid only works with index=None"""
        index = self.get_index(index=index, exclude_invalid=exclude_invalid)
        raw = self.file_handler.raw.getunsorted(index)
        return raw[np.argsort(np.argsort(index))]  # revert sort

    def cal_integrated_minus_dark(self, ):
        raw = self.load_raw(exclude_invalid=False)  # exclude_invalid=False as the length hast to match
        raw = raw - self.raw_dark_frame  # subtract the dark frame
        raw = self.cut2effective_pixel(raw, axis=1)
        raw[raw < 4e4] = 0  # cut the noise
        raw = raw ** 2  # Chi**2
        return np.average(raw.reshape((raw.shape[0], -1)), axis=-1)

    def cal_raw_dark_frame(self, n=None):
        """Takes the 'n' most dim pictures in the series to calculate the dark frame"""
        self._integrated_minus_dark = None

        if n is None:
            n = 10
        n = int(n)
        integrated_raw_masked = np.ma.array(self.integrated_raw, mask=~self.valid_mask)
        index = np.ma.argsort(integrated_raw_masked)  # masked items count as greatest
        self._raw_dark_frame = np.average(self.load_raw(index[:n]), axis=0)  # n=10

    def get_index(self, index=None, exclude_invalid=True):
        if index is None:
            index = np.arange(self.file_handler.time.shape[0])

        elif isinstance(index, (int, float)):
            index = np.array([int(index)])

        elif isinstance(index, list):
            index = np.array([index], dtype=int)

        if exclude_invalid:
            index = index[self.valid_mask[index]]

        return index

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

    def cut2effective_pixel_single(self, rgb, eff_margin=None):
        """Shortcut for cut2effective_pixel(rgb_arr, axis=0, eff_margin=eff_margin)"""
        return self.cut2effective_pixel(rgb, axis=0, eff_margin=eff_margin)

    def cut2effective_pixel_arr(self, rgb_arr, eff_margin=None):
        """Shortcut for cut2effective_pixel(rgb_arr, axis=1, eff_margin=eff_margin)"""
        return self.cut2effective_pixel(rgb_arr, axis=1, eff_margin=eff_margin)

    def cut2effective_pixel(self, rgb, axis=-1, eff_margin=None):
        """
        Cuts the effective margin from the rgb array.
        PARAMETER
        ---------
        rgb: ndarray
            at a least 2d array. The x- and y-axes have to be in this order, next to each other, and can be
            positioned anywhere. rgb.shape = (..., x-axis, y-axis,...)
        axis: int, optional
            the position of the pixel x-axis, e.g. rgb.shape = (images, x-axis, y-axis,...) -> axis=1
            If value is negative, it counts from the second last entry so axis=-1 works for
            rgb.shape = (..., x-axis, y-axis) or axis=-2 <-> rgb.shape = (..., x-axis, y-axis, rgb)
        eff_margin: bool, list, ndarray, optional
            shifts the mask according to the effective margin for images where the margin is cut, e.g. with
            cut2effective_pixel(..., eff_margin=eff_margin) ->  get_raw_rgb_mask(..., eff_margin=eff_margin)
            If None or True, it takes the eff_margin from the file, i.e. file_handler.EffMargins[:]
            If its a list or ndarray: it must has the from [pixel_x_start, pixel_x_stop, pixel_y_start, pixel_y_stop]
            and only integers are allowed.
        RETURN
        ------
        reduced_rgb:
            the rgb array with cut margins
        """
        rgb = np.array(rgb)

        if len(rgb.shape) < 2:
            raise ValueError(f'Array needs at leas 2 dimensions. Got shape: {rgb.shape}')

        if axis < 0:
            axis += len(rgb.shape) - 1

        if axis > len(rgb.shape) - 2:
            raise ValueError(f"Specified axis to high for array. Axis>shape-2; got: {axis} > {len(rgb.shape) - 2}")

        if eff_margin is None or eff_margin is True:
            eff_margin = self.file_handler.EffMargins[:]

        slices = (*[slice(None)] * axis,
                  slice(eff_margin[0], -eff_margin[1] if eff_margin[1] != 0 else None),
                  slice(eff_margin[2], -eff_margin[3] if eff_margin[3] != 0 else None))
        return np.array(rgb)[slices]

    def get_raw_rgb_mask(self, shape, color='green', eff_margin=False):
        """
        PARAMETER
        ---------
        shape:
            shape of the mask or data
        color: str, optional
            color channel to create the mask for. Must be one of
            ['green', 'blue', 'red', 'g', 'b', 'r'] also the names of the matplotlib cmaps are allowed
            ['Greens', 'Blues', 'Reds']. Default is 'green'.
        eff_margin: bool, list, ndarray, optional
            shifts the mask according to the effective margin for images where the margin is cut, e.g. with
            cut2effective_pixel(..., eff_margin=eff_margin) ->  get_raw_rgb_mask(..., eff_margin=eff_margin)
            If None or True, it takes the eff_margin from the file, i.e. file_handler.EffMargins[:]
            If its a list or ndarray: it must has the from [pixel_x_start, pixel_x_stop, pixel_y_start, pixel_y_stop]
            and only integers are allowed.

        RETURN
        ------
        mask: ndarray
            a bool numpy array which selects the specified color
        """
        color = color.lower()
        color = color[:-1] if color.endswith('s') else color
        know_color = ['green', 'blue', 'red']
        know_color.extend([i[0] for i in know_color])
        if color not in know_color:
            raise ValueError(f'Unknown color. Supports: {know_color}; Got: {color}')

        if isinstance(eff_margin, bool) and eff_margin is False:
            eff_margin = [0, 0, 0, 0]
        if eff_margin is None or isinstance(eff_margin, bool) and eff_margin is True:
            eff_margin = self.file_handler.EffMargins[:]

        margin_x_shift = eff_margin[0] % 2
        margin_y_shift = eff_margin[2] % 2

        mask = np.zeros(shape, dtype=bool)

        if color in ['green', 'g']:
            mask[margin_x_shift + 1::2, margin_y_shift::2] = True
            mask[margin_x_shift::2, margin_y_shift + 1::2] = True
        elif color in ['blue', 'b']:
            mask[margin_x_shift + 1::2, margin_y_shift + 1::2] = True
        elif color in ['red', 'r']:
            mask[margin_x_shift::2, margin_y_shift::2] = True

        return mask

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

        # axes are: [images, pix_x, pix_y, RGB]
        image_arr = self.cut2effective_pixel(image_list, axis=1)

        return image_arr

    def normalize_rgb(self, image_arr, bit_out=0, bit_in=None, ):
        """Get the rgb values to the range 0->1. or 0,1...->255
        PARAMETERS
        ----------
        image_arr: ndarray
            array of images values. Can be a single image (2D array) or multiple (>3D array)
        bit_in: int, optional
            defines the range of the input values.
            - None: determins the bit from the dtype. Supports np.uint8, np.uint16, np.uint32, float 
            - 0 : (default) maps the values to the range [0, 1] as float
            - 8 : maps the values to the range [0, 255] as int
            - 16: maps the values to the range [0, 2**16-1] as int 
        bit_out: int, optional
            - 0 : (default) maps the values to the range [0, 1[ as float
            - 8 : maps the values to the range [0, 255] as int
            - 16: maps the values to the range [0, 2**16-1] as int  
        """
        bit_dict = {8: np.uint8, 16: np.uint16, 32: np.uint32, 64: np.uint64}
        bit_dict_inv = {np.dtype(j): i for i, j in bit_dict.items()}

        bit_in = 0
        max_in = 1.

        if image_arr.dtype in bit_dict_inv:
            bit_in = bit_dict_inv[image_arr.dtype]
            max_in = 2 ** bit_in - 1
        else:
            bit_in = 0
            max_in = 1.

        if bit_out in bit_dict:
            type_out = bit_dict[bit_out]
            max_out = 2 ** bit_out - 1
        else:
            type_out = np.float64
            max_out = 1.

        if max_out != max_in:
            image_arr = image_arr / max_in * max_out
            image_arr = image_arr.astype(type_out)
            image_arr[image_arr > max_out] = max_out

        return image_arr

    def image2png(self, f_name_formatter='{datetime}', directory='{proc_data_dir}/{module_lower}',
                  bit=8, index=None, overwrite=False, file_name_iterator=None, ending='.png', **kwargs):
        """f_name has to include at least on of the formatter_dict.keys

        PARAMETER
        ---------
        f_name_formatter: str, optional
            Defines the filename for each image. Possible placeholders are: {datetime}, {index} (in file) and {i}
            they can be combined. {i} is a placeholder for 'file_name_iterator'. See 'file_name_iterator' for more.
        index: List[int] or None, optional
            Specifies the which images are saved. The index is the index in the raw file. None (Default) is the
            placeholder for all images in the file.
        directory: str, optional,
            can have a placeholders {module}, {module_lower} or {proc_data_dir} which will be replaced with
            module name, the module name in lowercase or the directory for the processed STRAWb data specified in thee
            config file. Default is '{proc_data_dir}/{module_lower}'.
        ending: str, optional
            can be one of '.png' or '.jpg'. The ending is added automatically if the f_name_formatter doesn't end with
            the ending.
        overwrite: bool, optional
            If False (Default) existing files will not be overwritten.
        file_name_iterator: list or None, optional
            Has to match with the 'index' length. Each element is replaced with the '{i}' placeholder in
            'f_name_formatter', e.g., f_name_formatter='file_{i}', file_name_iterator=[1,2,3] -> file_1, file_2, file_3
        """

        if not f_name_formatter.endswith(ending):
            f_name_formatter += ending

        index = self.get_index(index=index, **kwargs)

        image_arr = self.load_rgb(index=index, **kwargs)

        # get bit's right, default is 16bit
        bit = int(bit)
        bit_dict = {8: np.uint8, 16: np.uint16}
        if bit == 8:
            image_arr = image_arr / 2 ** 16 * 2 ** 8  # - 1

        image_arr[image_arr == 2 ** bit] = image_arr[image_arr == 2 ** bit] - 1
        image_arr = image_arr.astype(bit_dict[bit])

        # prepare directory
        directory = os.path.abspath(directory.format(proc_data_dir=Config.proc_data_dir,
                                                     module=self.file_handler.module,
                                                     module_lower=self.file_handler.module.lower()))
        os.makedirs(directory, exist_ok=True)

        file_name_list = []
        for i, index_i in enumerate(index):
            # prepare file name, get time to correct format
            date_i = self.file_handler.time.getunsorted([index_i]).astype('datetime64[s]')[0]
            str_date_i = str(date_i).replace(':', '_').replace('.', '_').replace('-', '_').replace('T', '_')

            formatter_dict = {'datetime': str_date_i, 'index': index_i, 'i': i}
            if file_name_iterator is not None:
                formatter_dict['i'] = file_name_iterator[i]

            f_name_i = f_name_formatter.format(**formatter_dict)
            f_name_target_i = os.path.join(directory, f_name_i)
            if os.path.exists(f_name_target_i) and overwrite:
                pass
                # print('skip:', f_name_target_i)
            else:
                # print('save:', f_name_target_i)
                cv2.imwrite(f_name_i, image_arr[i, :, :, ::-1])  # [:,:,::-1] as cv2 takes BGR and not RGB
                shutil.move(os.path.join(os.path.abspath('.'), f_name_i), f_name_target_i)  # move file

            file_name_list.append(f_name_target_i)
        return file_name_list

    def get_lucifer_mask(self, mode_list=None):
        """ mode_list is something like [2, 0, 15, 7] or [1, 1, 15, -125] ([mode, addr, current, duration])"""
        if mode_list is None:
            mode_list = np.unique(self.file_handler.lucifer_options[:], axis=0)
            # in the following line, only 'mode_list[:, 0] == -125' without np.argwhere raise an FutureWarning
            mode_list = np.delete(mode_list, np.argwhere(mode_list[:, 0] == -125), axis=0)  # remove lucifer off

        mask_list = []
        for i in mode_list:
            mask_list.append(np.all(self.file_handler.lucifer_options[:] == i, axis=-1))

        return mode_list, mask_list

    def image2png_lucifer(self, **kwargs):
        mode_dict = {-125: 'OFF', 0: 'OFF', 1: 'TORCH', 2: 'FLASH'}
        index = self.get_index()

        mode_list, mask_list = self.get_lucifer_mask()

        process_dict = {}
        for mode_i, mask_i in zip(mode_list, mask_list):
            out_str = [mode_dict[mode_i[0]].lower()]  # the mode
            for i_i in mode_i[1:]:
                if i_i != -125:
                    out_str.append(str(i_i))  # the settings; address, [current, [duration]]
            out_str = '_'.join(out_str)  # <mode>_<address>_<current>_<duration>
            file_name_list = self.image2png(index=index[mask_i],
                                            directory='{proc_data_dir}/{module_lower}/' + out_str,
                                            **kwargs)
            process_dict[str(mode_i)] = file_name_list

        return process_dict
