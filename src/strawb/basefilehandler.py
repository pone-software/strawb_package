import os
from strawb.config_parser.config_parser import Config


class BaseFileHandler:
    def __init__(self, file_name=None, module=None):
        if file_name is None:
            self.file_name = None
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
        if module is None:
            # '...le_data/TUMMINISPECTROMETER001_202104...' -> 'MINISPECTROMETER001'
            self.module = file_name.rsplit('/', 1)[-1].split('_', 1)[0].replace('TUM', '')
        else:
            self.module = module

    @staticmethod
    def timestamp2datetime64(data, unit='us'):
        unit_dict = {'s': 1, 'ms': 1e3, 'us': 1e6, 'ns': 1e9}
        if unit.lower() not in unit_dict:
            raise ValueError(f'unit not in unit_dict (unit_dict), got: {unit}')
        return (data * unit_dict[unit.lower()]).astype(f'datetime64[{unit.lower()}]')

    def load_meta_data(self, ):
        pass
