# Author: Kilian Holzapfel <kilian.holzapfel@tum.de>
import h5py

from .onc_downloader import *
from .sensors import *
from .tools import AsDatetimeWrapper

from .virtual_hdf5 import VirtualHDF5, DatasetsInGroupSameSize


# add '.asdatetime' to h5py packet
h5py.Dataset.asdatetime = AsDatetimeWrapper.asdatetime
