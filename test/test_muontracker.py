import os
from unittest import TestCase

import numpy as np

from src.strawb.sensors.muontracker.file_handler import FileHandler
from strawb import SyncDBHandler


# def get_files():
#     db = SyncDBHandler(file_name='Default')  # loads the db
#
#     # mask by device
#     mask = db.dataframe['deviceCode'] == 'TUMMUONTRACKER001'
#     mask &= db.dataframe.dataProductCode == 'MTSD'  # see SyncDBHandler.sensor_mapping
#     mask &= db.dataframe.synced  # only downloaded files
#     mask &= db.dataframe.file_version > 0  # only valid files
#
#     file_list = db.dataframe.fullPath[mask].to_list()
#
#     return file_list, mask, db


class TestMuonTrackerFileHandlerInit(TestCase):
    def setUp(self):
        file_list = ['TUMMUONTRACKER001_20220731T001146.146Z-SDAQ-MUON.hdf5']
        db = SyncDBHandler(file_name='Default')  # loads the db
        db_i = db.get_files_from_names(file_list)

        # file_list, mask, db = get_files()

        # self.full_path = random.choice(db_i.fullPath)  # select a random file
        self.full_path = db_i.fullPath.iloc[0]
        self.file_name = os.path.split(self.full_path)[-1]

    def test_init_full_path(self):
        muon = FileHandler(self.full_path)
        # check here only the time
        self.assertIsInstance(muon.daq_time[:],
                              np.ndarray,
                              f'muon.time[:] has to be a np.ndarray, got: {type(muon.daq_time)}')
