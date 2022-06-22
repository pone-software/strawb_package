from .camera import Camera
from .module import Module
from .lidar import Lidar
from .pmtspec import PMTSpec
from .minispec import MiniSpectrometer
from .adcp import ADCP


# class BaseSensor:
#     data_product_code_mapping = {
#         "LF": None,
#         "MTSD": None,  # TUMMUONTRACKER001_20210503T000000.000Z-SDAQ-MUON.hdf5
#         "LIDARSD": Lidar,  # TUMLIDAR001_20210503T000000.000Z-SDAQ-LIDAR.hdf5
#         "MSRD": MiniSpectrometer,  # TUMLIDAR001_20210503T000000.000Z-SDAQ-MINISPEC.hdf5
#         "SMRD": Module,  # TUMLIDAR001_20210503T000000.000Z-SDAQ-MODULE.hdf5
#         "MSSD": MiniSpectrometer,  # TUMPMTSPECTROMETER002_20210503T000000.000Z-SDAQ-MINISPEC.hdf5
#         "MTRD": None,  # TUMMUONTRACKER001_20210503T000001.223Z-MUON.hld
#         "LIDARTOT": None,  # TUMLIDAR001_20210503T000610.343Z-TOT-LIDAR.txt
#         "MSSCD": Camera,  # TUMPMTSPECTROMETER002_20210503T190000.000Z-SDAQ-CAMERA.hdf5
#         "MTTOT": None,  # TUMMUONTRACKER001_20210802T230012.933Z-TOT-MUON.txt
#         "LIDARRD": None,  # TUMLIDAR001_20210830T001811.088Z-LIDAR.hld
#         "PMTSD": PMTSpec,  # TUMPMTSPECTROMETER001_20211018T200000.000Z-SDAQ-PMTSPEC.hdf5
#     }
#
#     file_ending2data_product_code = {
#         # "LF": None,
#         "-SDAQ-MUON.hdf5": "MTSD",
#         "-SDAQ-LIDAR.hdf5": 'LIDARSD',
#         "-SDAQ-MINISPEC.hdf5": 'MSRD',  # or 'MSSD'
#         "-SDAQ-MODULE.hdf5": 'SMRD',
#         "-MUON.hld": 'MTRD',
#         "-TOT-LIDAR.txt": 'LIDARTOT',
#         "-SDAQ-CAMERA.hdf5": 'MSSCD',
#         "-TOT-MUON.txt": 'MTTOT',
#         "-LIDAR.hld": 'LIDARRD',
#         "-SDAQ-PMTSPEC.hdf5": 'PMTSD',
#     }
