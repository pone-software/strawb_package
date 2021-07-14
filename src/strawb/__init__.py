# Author: Kilian Holzapfel <kilian.holzapfel@tum.de>
import h5py

from .onc_downloader import *
from .sensors import *

from .virtual_hdf5 import VirtualHDF5, DatasetsInGroupSameSize

import numpy


# add new asdatetime to h5py Dataset similar to asdtype for datetime64 when time is given as float in seconds
# a = np.array([1624751981.4857635], float)  # time in seconds since epoch
# a.asdatetime('ms')
# -> np.array('2021-06-26T23:59:41.485763', datetime64[ms])
class AsDatetimeWrapper(object):
    """Wrapper to convert data on reading from a dataset.
    """

    def __init__(self, dset, unit='us'):
        self._dset = dset

        self.unit_dict = {'s': 1, 'ms': 1e3, 'us': 1e6, 'ns': 1e9}
        if unit.lower() not in self.unit_dict:
            raise ValueError(f'unit not in unit_dict (unit_dict), got: {unit}')

        self._dtype = numpy.dtype(f'datetime64[{unit.lower()}]')
        self.scale = float(self.unit_dict[unit.lower()])

    def __getitem__(self, args):
        return (self._dset.__getitem__(args, ) * self.scale).astype(self._dtype)

    # def __enter__(self):
    #     # pylint: disable=protected-access
    #     return self
    #
    # def __exit__(self, *args):
    #     # pylint: disable=protected-access
    #     pass

    @staticmethod
    def asdatetime(self, ):
        return AsDatetimeWrapper(self, )


# h5py.Dataset.asdatetime = types.MethodType(new_asdatetime, h5py.Dataset)
h5py.Dataset.asdatetime = AsDatetimeWrapper.asdatetime
