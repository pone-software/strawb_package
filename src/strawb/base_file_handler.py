import os
import h5py

from strawb.config_parser.config_parser import Config


class BaseFileHandler:
    def __init__(self, file_name=None, module=None):
        # get all Meta Data arrays
        self.__members__ = [attr for attr in dir(self) if
                            not callable(getattr(self, attr)) and not attr.startswith("__")]

        self.file = None  # instance of the h5py file
        self.file_name = None
        self.module = None

        if file_name is None:
            pass
        elif os.path.exists(file_name):
            self.file_name = os.path.abspath(file_name)
            self.load_meta_data()
        elif os.path.exists(os.path.join(Config.raw_data_dir, file_name)):
            path = os.path.join(Config.raw_data_dir, file_name)
            self.file_name = os.path.abspath(path)
            self.load_meta_data()
        else:
            raise FileNotFoundError(file_name)

        # in case, extract the module name from the filename
        if module is None and file_name is not None:
            # '...le_data/TUMMINISPECTROMETER001_202104...' -> 'MINISPECTROMETER001'
            self.module = file_name.rsplit('/', 1)[-1].split('_', 1)[0].replace('TUM', '')

    def open(self):
        """Opens the file if it is not open"""
        if self.file is None:
            self.file = h5py.File(self.file_name, 'r', libver='latest', swmr=True)

    def close(self):
        """Close the file if it is open."""
        if self.file is not None:
            self.file.close()

    def __enter__(self):
        """For 'with' statement"""
        self.open()
        return self

    def __exit__(self, *args):
        """For 'with' statement"""
        self.close()

    def load_meta_data(self, ):
        """Opens the file and loads the data defined by __load_meta_data__."""
        self.open()
        self.__load_meta_data__()

    def __load_meta_data__(self, ):
        """Placeholder which defines how data are read."""
        pass
