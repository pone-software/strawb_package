# Author: Kilian Holzapfel <kilian.holzapfel@tum.de>
import h5py

from .onc_downloader import *
from .sensors import *
from .tools import AsDatetimeWrapper, hdf5_getunsorted

from .virtual_hdf5 import VirtualHDF5, DatasetsInGroupSameSize


# add '.asdatetime' to h5py packet
h5py.Dataset.asdatetime = AsDatetimeWrapper.asdatetime
h5py.Dataset.getunsorted = hdf5_getunsorted
