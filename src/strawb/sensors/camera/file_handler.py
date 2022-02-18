from ...base_file_handler import BaseFileHandler


class FileHandler(BaseFileHandler):
    def __init__(self, *args, **kwargs):
        # measurement data
        self.time = None
        self.exposure_time = None  # exposure time per measurement in seconds: float, [0...~63s]
        self.gain = None  # gain per measurement: uint, [0...100]
        self.raw = None  # the raw pictures: uint, [[[pixel_00...pixel_0m], ..., [pixel_n0...pixel_nm]]]

        # meta data
        # Lucifer options: opt: -127 or 0 off, 1 Torch, 2 Flash; addr: 0 all, [1..4] single
        self.lucifer_options = None  # [[opt, addr, current, duration]]
        self.exposure_time_cmd_setting = None
        self.measured_capture_time = None
        self.reported_resolution = None

        # Attributes
        self.EffMargins = None  # pixels margin after the demosaicing in pixels: int, [left, right, top, bottom]
        self.ExposureTimeScaleFactor = None
        self.ApproxPictureDownloadTime = None
        self.IgnoredMargins = None
        self.MODE = None
        self.RAW_Resolution = None
        self.Resolution = None

        self.all_attributes = None  # holds all hdf5-group camera attributes as dict

        # comes last to load the data in case file_name is set
        BaseFileHandler.__init__(self, *args, **kwargs)

    def __load_meta_data__(self, ):
        self.time = self.file['/camera/time']
        self.exposure_time = self.file['/camera/exposure_time']
        self.gain = self.file['/camera/gain']
        self.raw = self.file['/camera/raw']

        self.lucifer_options = self.file['/camera/lucifer_options']
        self.exposure_time_cmd_setting = self.file['/camera/exposure_time_cmd_setting']
        self.measured_capture_time = self.file['/camera/measured_capture_time']
        self.reported_resolution = self.file['/camera/reported_resolution']

        # Attributes
        self.EffMargins = self.file['camera'].attrs['EffMargins']
        self.ExposureTimeScaleFactor = self.file['camera'].attrs['ExposureTimeScaleFactor']
        self.ApproxPictureDownloadTime = self.file['camera'].attrs['ApproxPictureDownloadTime']
        self.IgnoredMargins = self.file['camera'].attrs['IgnoredMargins']
        self.MODE = self.file['camera'].attrs['MODE']
        self.RAW_Resolution = self.file['camera'].attrs['RAW_Resolution']
        self.Resolution = self.file['camera'].attrs['Resolution']

        self.all_attributes = dict(self.file['camera'].attrs)

        self.file_version = 1
