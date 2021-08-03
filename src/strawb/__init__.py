# Author: Kilian Holzapfel <kilian.holzapfel@tum.de>
import h5py

from .config_parser import Config
from .onc_downloader import ONCDownloader
from .sensors import *
from .tools import AsDatetimeWrapper, hdf5_getunsorted

from .virtual_hdf5 import VirtualHDF5, DatasetsInGroupSameSize

# add '.asdatetime' to h5py packet
h5py.Dataset.asdatetime = AsDatetimeWrapper.asdatetime
h5py.Dataset.getunsorted = hdf5_getunsorted

# store some properties
module_onc_id: dict = {'0000006605b0': {'ip_add': '10.136.117.166', 'dev_code': 'TUMSTANDARDMODULE001'},
                       '000000661e33': {'ip_add': 'XX.XXX.XXX.XXX', 'dev_code': 'TUMSTANDARDMODULE002'},
                       '00000065e581': {'ip_add': 'XX.XXX.XXX.XXX', 'dev_code': 'TUMSTANDARDMODULE003'},
                       '00000066127f': {'ip_add': '10.136.117.167', 'dev_code': 'TUMLIDAR001'},
                       '00000066178e': {'ip_add': '10.136.117.160', 'dev_code': 'TUMLIDAR002'},
                       '00000065fa1b': {'ip_add': '10.136.117.168', 'dev_code': 'TUMPMTSPECTROMETER001'},
                       '0000006606bd': {'ip_add': '10.136.117.161', 'dev_code': 'TUMPMTSPECTROMETER002'},
                       '00000065e091': {'ip_add': '10.136.117.164', 'dev_code': 'TUMMUONTRACKER001'},
                       '00000065ff9b': {'ip_add': '10.136.117.165', 'dev_code': 'TUMMINISPECTROMETER001'},
                       '0000006601ee': {'ip_add': '10.136.117.180', 'dev_code': 'TUMSTANDARDMODULE004'},
                       '00000065fcc0': {'ip_add': 'XX.XXX.XXX.XXX', 'dev_code': 'TEST'},
                       '__unittest__': {'ip_add': 'XX.XXX.XXX.XXX', 'dev_code': 'UNITTEST'}}
