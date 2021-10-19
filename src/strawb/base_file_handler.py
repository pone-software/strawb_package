import glob
import os
import h5py

from strawb.config_parser.__init__ import Config


class BaseFileHandler:
    def __init__(self, file_name=None, module=None):
        # get all Meta Data arrays
        self.__members__ = [attr for attr in dir(self) if
                            not callable(getattr(self, attr)) and not attr.startswith("__")]

        self.file = None  # instance of the h5py file
        self.file_name = None
        self.module = None
        self.file_typ = None  # file type

        self.file_attributes = None  # holds all hdf5-file attributes as dict

        if file_name is None:
            pass
        elif os.path.exists(file_name):
            self.file_name = os.path.abspath(file_name)
            self.file_typ = self.file_name.rsplit('.', 1)[-1]
            self.load_meta_data()
        elif os.path.exists(os.path.join(Config.raw_data_dir, file_name)):
            path = os.path.join(Config.raw_data_dir, file_name)
            self.file_name = os.path.abspath(path)
            self.file_typ = self.file_name.rsplit('.', 1)[-1]
            self.load_meta_data()
        else:
            file_name_list = glob.glob(Config.raw_data_dir + "/**/" + file_name, recursive=True)
            if len(file_name_list) == 1:
                self.file_name = file_name_list[0]
                self.file_typ = self.file_name.rsplit('.', 1)[-1]
                self.load_meta_data()
            else:
                if not file_name_list:
                    raise FileNotFoundError(f'{file_name} not found nor matches any file in "{Config.raw_data_dir}"')
                else:
                    raise FileExistsError(f'{file_name} matches multiple files in "{Config.raw_data_dir}": '
                                          f'{file_name_list}')

        # in case, extract the module name from the filename
        if module is None and file_name is not None:
            # '...le_data/TUMMINISPECTROMETER001_202104...' -> 'MINISPECTROMETER001'
            self.module = file_name.rsplit('/', 1)[-1].split('_', 1)[0].replace('TUM', '')

    def open(self):
        """Opens the file if it is not open"""
        if self.file is None:
            if self.file_typ in ['h5', 'hdf5']:
                self.file = h5py.File(self.file_name, 'r', libver='latest', swmr=True)
            elif self.file_typ in ['txt']:
                self.file = open(self.file_name, 'r')
            else:
                raise NotImplementedError(f'file_typ not implemented {self.file_typ}')

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

    def __del__(self):
        """ When object is not used anymore."""
        self.close()

    def load_meta_data(self, ):
        """Opens the file and loads the data defined by __load_meta_data__."""
        self.open()
        self.file_attributes = dict(self.file.attrs)
        self.__load_meta_data__()

    def __load_meta_data__(self, ):
        """Placeholder which defines how data are read."""
        pass

    @staticmethod
    def find_files_glob(file_pattern='*.hdf5', directory=None, recursive=True, raise_nothing_found=False):
        """ Find files with the given pattern via glob.glob.
        Parameter
        ---------
        file_pattern: str, optional
            The search pattern, which may contain simple shell-style wildcards.
        directory: str, optional
            The root directory for the search, None (default) takes the `Config.raw_data_dir`.
        recursive: bool, optional
            If True (default), subdirectories are included in the search.
        raise_nothing_found: bool, optional
            If True, a FileNotFoundError is raised if no files are found. Default, False.
        """
        if directory is None:
            directory = Config.raw_data_dir

        if recursive:
            file_list = glob.glob(f'{directory.rstrip("/")}/**/{file_pattern}', recursive=True)
            file_list.sort()
        else:
            file_list = glob.glob(f'{directory.rstrip("/")}/{file_pattern}')
            file_list.sort()

        if raise_nothing_found and not file_list:
            raise FileNotFoundError(f'No files found for file_pattern: {file_pattern} in {directory}')

        return file_list

    @staticmethod
    def find_files(*args, **kwargs):
        print('WARNING: Use find_files_glob() instead of find_files()')
        return BaseFileHandler.find_files_glob(*args, **kwargs)

    @staticmethod
    def test_load_meta_data(file_name, load_function):
        class Fake:
            def __init__(self, file):
                self.file = file

        with h5py.File(file_name, 'r', libver='latest', swmr=True) as f:
            fake = Fake(f)
            load_function(fake)

        return fake
