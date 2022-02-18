import glob
import os
import h5py

from strawb.config_parser.__init__ import Config


class BaseFileHandler:
    def __init__(self, file_name=None, module=None, raise_error=True):
        """The Base File Handler defines the basic file handling for the strawb package.

        PARAMETER
        ---------
        file_name: Union[str, None], optional
            defines the file name. At initialisation, it checks if the file exists. The file name can be one of:
            - None, to load initialise without an file name specified
            - an absolut path, e.g. '/path/to/strawb/data/file_1.txt'
            - a relative path inside the strawb raw_data_dir, e.g. 'module_a/file_1.txt'
            - a file name which will be searched in the strawb raw_data_dir path, e.g. 'file_1.txt'
            If the file name is set, it will load the data into the class.
        module: Union[str, None], optional
            sets the name of the module which the file belongs to. If None (default) it extract the module name from the
            file name following the ONC naming scheme.
        raise_error: bool, optional
            if an empty or broken file should raise an error or continue without. Default is None.
        """
        # get all Meta Data arrays
        self.__members__ = [attr for attr in dir(self) if
                            not callable(getattr(self, attr)) and not attr.startswith("__")]

        self.file = None  # instance of the h5py file
        self.file_name = None
        self.module = None
        self.file_typ = None  # file type
        self.file_version = 0  # can be either a error str or int for the file version. Default is 0 <-> not loaded.

        # empty file
        self.is_empty = None

        self.file_attributes = None  # holds all hdf5-file attributes as dict

        if file_name is None:
            pass
        elif os.path.exists(file_name):
            self.file_name = os.path.abspath(file_name)
            self.file_typ = self.file_name.rsplit('.', 1)[-1]
            self.file_version = self._init_open_(raise_error=raise_error)
        elif os.path.exists(os.path.join(Config.raw_data_dir, file_name)):
            path = os.path.join(Config.raw_data_dir, file_name)
            self.file_name = os.path.abspath(path)
            self.file_typ = self.file_name.rsplit('.', 1)[-1]
            self.file_version = self._init_open_(raise_error=raise_error)
        else:
            file_name_list = glob.glob(Config.raw_data_dir + "/**/" + file_name, recursive=True)
            if len(file_name_list) == 1:
                self.file_name = file_name_list[0]
                self.file_typ = self.file_name.rsplit('.', 1)[-1]
                self.file_version = self._init_open_(raise_error=raise_error)
            else:
                if not file_name_list:
                    raise FileNotFoundError(f'{file_name} not found nor matches any file in "{Config.raw_data_dir}"')
                else:
                    raise FileExistsError(f'{file_name} matches multiple files in "{Config.raw_data_dir}": '
                                          f'{file_name_list}')

        # in case, extract the module name from the filename
        if module is None and file_name is not None:
            try:
                # '...le_data/TUMMINISPECTROMETER001_202104...' -> 'MINISPECTROMETER001'
                self.module = file_name.rsplit('/', 1)[-1].split('_', 1)[0].replace('TUM', '')
            except (KeyError, ValueError, TypeError):
                pass

    def close(self):
        """Close the file if it is open."""
        if self.file is not None:
            self.file.close()
            self.file = None

    def __enter__(self):
        """For 'with' statement"""
        self.open()
        return self

    def __exit__(self, *args):
        """For 'with' statement"""
        self.close()

    def __del__(self):
        """When object is not deleted, e.g. when program ends, variable deleted, deleted by the garbage collector."""
        self.close()

    def _open_(self, mode='r'):
        """Opens the file if it is not open.
        PARAMETER
        ---------
        mode: str, optional
            r	   : Readonly, file must exist (default)
            r+	   : Read/write, file must exist
            w	   : Create file, truncate if exists
            w- or x: Create file, fail if exists
            a	   : Read/write if exists, create otherwise
        """
        if self.file is None:
            if self.file_typ in ['h5', 'hdf5']:
                if mode in ['r']:
                    self.file = h5py.File(self.file_name, mode, libver='latest',
                                          # swmr=True
                                          )
                else:
                    self.file = h5py.File(self.file_name, mode, libver='latest')
                    # self.file.swmr_mode = True
                self.file_attributes = dict(self.file.attrs)

            elif self.file_typ in ['txt']:
                self.file = open(self.file_name, 'r')

            else:
                raise NotImplementedError(f'File_typ not implemented. Got: {self.file_typ}')

    def open(self, mode='r', load_data=True):
        """Opens the file and loads the data defined by __load_meta_data__.
        PARAMETER
        ---------
        mode: str, optional
            r	   : Readonly, file must exist (default)
            r+	   : Read/write, file must exist
            w	   : Create file, truncate if exists
            w- or x: Create file, fail if exists
            a	   : Read/write if exists, create otherwise
        load_data: bool, optional
            if data should be loaded and linked. Must be disabled if hdf5 group should be deleted.
        """
        self._open_(mode=mode)

        self.is_empty = True
        if self.file_typ in ['h5', 'hdf5']:
            if not list(self.file.keys()):  # no groups inside the file -> empty file
                self.is_empty = True
            else:
                self.is_empty = False

        elif self.file_typ in ['txt']:
            self.is_empty = False  # TODO: detect an empty txt file

        # link and load data
        if not self.is_empty and load_data:
            self.__load_meta_data__()

    def __load_meta_data__(self, ):
        """Placeholder which defines how data are read."""
        pass

    def _init_open_(self, raise_error=True):
        """Open file to get the file_error = file_version."""
        file_error = 'unknown error'

        if raise_error:
            self.open(mode='r', load_data=True)
            if self.is_empty:
                raise FileExistsError(f'HDF5 File is empty. Got: {self.file_name}')

        # noinspection PyBroadException
        try:
            self.open(mode='r', load_data=True)

            # group or dataset not in hdf5 file
        except KeyError as err:
            if err.args[0] == 'Unable to open object (component not found)':
                file_error = 'hdf5 missing group or dataset'  # -2

        except OSError as a:
            if a.args[0].startswith('Unable to open file (truncated file:'):
                file_error = 'broken hdf5'  # -3

        # all other exceptions
        except Exception:
            file_error = 'unknown error'

        else:
            if self.is_empty:
                file_error = 'empty file'  # -1
            else:
                return self.file_version

        return file_error

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
