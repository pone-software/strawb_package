import os
import shutil

import cv2
import numpy as np

from ...config_parser.__init__ import Config


class PictureHandler:
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

    def __init__(self, file_handler):
        self.file = file_handler
        self.integrated_raw = np.sum(self.file.raw,
                                     axis=(1, 2))  # processed but close to raw, sum over all pixels per image

        # processed Data - !! have to be set to non after an append in the CameraModuleHandler !!
        self._raw_dark_frame = None  # for property
        self._rgb_dark_frame = None  # for property
        self._invalid_mask = None  # for property
        self._integrated_minus_dark = None  # for property
        self._max_value_minus_dark = None

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

    def load_raw(self, index=None, exclude_invalid=True):
        """exclude_invalid only works with index=None"""
        index = self.get_index(index=index, exclude_invalid=exclude_invalid)
        raw = self.file.raw.getunsorted(index)
        return raw[np.argsort(np.argsort(index))]  # revert sort

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
            index = np.arange(self.file.time.shape[0])

        elif type(index) is int:
            index = [index]

        if exclude_invalid:
            index = index[self.invalid_mask[index]]

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

    def cut2effective_pixel_single(self, rgb):
        return np.array(rgb)[self.file.EffMargins[0]:-self.file.EffMargins[1],
                             self.file.EffMargins[2]:-self.file.EffMargins[3]]

    def cut2effective_pixel_arr(self, rgb_arr):
        return np.array(rgb_arr)[:,
                                 self.file.EffMargins[0]:-self.file.EffMargins[1],
                                 self.file.EffMargins[2]:-self.file.EffMargins[3]]

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

        rgb = self.load_rgb(index=index, **kwargs)

        # get bit's right, default is 16bit
        bit = int(bit)
        bit_dict = {8: np.uint8, 16: np.uint16}
        if bit == 8:
            rgb = rgb / 2 ** 16 * 2 ** 8  # - 1

        rgb[rgb == 2 ** bit] = rgb[rgb == 2 ** bit] - 1
        rgb = rgb.astype(bit_dict[bit])

        # prepare directory
        directory = os.path.abspath(directory.format(proc_data_dir=Config.proc_data_dir,
                                                     module=self.file.module, module_lower=self.file.module.lower()))
        os.makedirs(directory, exist_ok=True)

        file_name_list = []
        for i, index_i in enumerate(index):
            # prepare file name, get time to correct format
            date_i = self.file.time.getunsorted([index_i]).astype('datetime64[s]')[0]
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
                cv2.imwrite(f_name_i, rgb[i, :, :, ::-1])  # [:,:,::-1] as cv2 takes BGR and not RGB
                shutil.move(os.path.join(os.path.abspath('.'), f_name_i), f_name_target_i)  # move file

            file_name_list.append(f_name_target_i)
        return file_name_list

    def get_lucifer_mask(self, mode_list=None):
        """ mode_list is something like [2, 0, 15, 7] or [1, 1, 15, -125] ([mode, addr, current, duration])"""
        if mode_list is None:
            mode_list = np.unique(self.file.lucifer_options[:], axis=0)
            # in the following line, only 'mode_list[:, 0] == -125' without np.argwhere raise an FutureWarning
            mode_list = np.delete(mode_list, np.argwhere(mode_list[:, 0] == -125), axis=0)  # remove lucifer off

        mask_list = []
        for i in mode_list:
            mask_list.append(np.all(self.file.lucifer_options[:] == i, axis=-1))

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
