import numpy as np


# TODO: this class isn't ready
class BaseSensor:
    def __init__(self):
        # Define all Meta Data arrays
        self.time = None  # time of the measurement since epoch in seconds [precision us]: float
        self.index_in_file = None  # the index of the specific measurement in the file, as the arrays may be sorted

        # get all Meta Data arrays
        self.__members__ = [attr for attr in dir(self) if
                            not callable(getattr(self, attr)) and not attr.startswith("__")]

    @staticmethod
    def timestamp2datetime64(data, unit='us'):
        unit_dict = {'s': 1, 'ms': 1e3, 'us': 1e6, 'ns': 1e9}
        if unit.lower() not in unit_dict:
            raise ValueError(f'unit not in unit_dict (unit_dict), got: {unit}')
        return (data * unit_dict[unit.lower()]).astype(f'datetime64[{unit.lower()}]')

    def sort(self, index):
        for i in self.__members__:
            if self.__getattribute__(i) is not None:
                self.__setattr__(i, self.__getattribute__(i)[index])

    def time_sort(self, ):
        if self.time is not None:
            self.sort(np.argsort(self.time))

    def append(self, file_handler):
        if not type(self) is type(file_handler):
            pass

    @staticmethod
    def __append_single(a, b):
        if a is None and b is None:
            return None
        if a is None:
            return np.copy(b)  # converts also to an array
        elif b is None:
            return np.copy(a)  # converts also to an array
        else:
            return np.append(a, b, axis=0)
