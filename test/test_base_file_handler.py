import os
import random
from unittest import TestCase

from src.strawb.config_parser import Config
from src.strawb.base_file_handler import BaseFileHandler


class TestBaseFileHandlerInit(TestCase):
    def setUp(self):
        search_path_list = ['*.hdf5', '*.txt']

        file_list = []
        for i in search_path_list:
            file_list.extend(BaseFileHandler.find_files_glob(file_pattern=i, directory=None, recursive=True))

        if not file_list:
            raise FileNotFoundError(f'No files found for search_path: {search_path_list} in {Config.raw_data_dir}')

        self.full_path = random.choice(file_list)  # select a random file
        self.file_name = os.path.split(self.full_path)[-1]

    def test_init_full_path(self):
        module = BaseFileHandler(self.full_path, raise_error=False)
        # check here only the the three parameters
        self.assertEqual(module.file_name, self.full_path)
        self.assertIsNotNone(module.module)
        self.assertIsNotNone(module.file)  # instance of the h5py file

    def test_init_default_path(self):
        module = BaseFileHandler(self.file_name, raise_error=False)
        # check here only the the three parameters
        self.assertEqual(module.file_name, self.full_path)
        self.assertIsNotNone(module.module)
        self.assertIsNotNone(module.file)  # instance of the h5py file

    def test_init_non_exiting_file(self):
        file_name = 'abc.cba'
        self.assertRaises(FileNotFoundError, BaseFileHandler, file_name=file_name)

    def test_init_multiple_exiting_file(self):
        file_name = '*.*'
        self.assertRaises(FileExistsError, BaseFileHandler, file_name=file_name)
