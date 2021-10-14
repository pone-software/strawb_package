import glob
import os
from unittest import TestCase

import h5py
import numpy as np
import pandas

from strawb import SyncDBHandler, dev_codes_deployed


class TestSyncDBHandler(TestCase):
    def test__check_index_(self):
        pd_result_0 = pandas.DataFrame([{'fullPath': 'TEST_1.txt', 'h5_attrs': None, 'synced': True},  # take
                                        {'fullPath': 'TEST_2.txt', 'h5_attrs': None, 'synced': True},
                                        ])

        SyncDBHandler._check_index_(pd_result_0)

        pd_result_0 = pandas.DataFrame([{'noFullPath': 'TEST_1.txt', 'h5_attrs': None, 'synced': True},  # take
                                        {'noFullPath': 'TEST_2.txt', 'h5_attrs': None, 'synced': True},
                                        ])

        self.assertRaises(KeyError, SyncDBHandler._check_index_, pd_result_0)

    # def test_load_db(self):
    #     self.fail()
    #
    # def test_save_db(self):
    #     self.fail()

    def test_add_new_db(self):
        pd_result_0 = pandas.DataFrame([{'fullPath': 'TEST_1.txt', 'h5_attrs': None, 'synced': True},  # take
                                        {'fullPath': 'TEST_2.txt', 'h5_attrs': None, 'synced': True},  # drop
                                        {'fullPath': 'TEST_3.txt', 'h5_attrs': None, 'synced': True},  # take
                                        {'fullPath': 'TEST_4.txt', 'h5_attrs': {'a': 1}, 'synced': False},  # take
                                        {'fullPath': 'TEST_5.txt', 'h5_attrs': {'a': 1}, 'synced': False},  # take
                                        {'fullPath': 'TEST_6.txt', 'h5_attrs': {'a': 1}, 'synced': False},  # take
                                        ])

        pd_result_1 = pandas.DataFrame([{'fullPath': 'TEST_2.txt', 'h5_attrs': {'a': 1}, 'synced': True},  # take
                                        {'fullPath': 'TEST_3.txt', 'h5_attrs': None, 'synced': True},  # drop
                                        {'fullPath': 'TEST_4.txt', 'h5_attrs': {'a': 5}, 'synced': False},  # drop
                                        {'fullPath': 'TEST_5.txt', 'h5_attrs': None, 'synced': False},  # drop
                                        {'fullPath': 'TEST_7.txt', 'h5_attrs': {'a': 1}, 'synced': False},  # (new)
                                        ])

        db_handler = SyncDBHandler(file_name=None)
        db_handler.dataframe = pd_result_0
        del pd_result_0

        db_handler.add_new_db(pd_result_1)

        self.assertTrue('TEST_7.txt' in db_handler.dataframe.index)  # added
        self.assertTrue(db_handler.dataframe['h5_attrs']['TEST_2.txt'] == {'a': 1})  # value updated
        self.assertTrue(db_handler.dataframe['h5_attrs']['TEST_4.txt'] == {'a': 1})  # value updated

    def test__check_double_indexes_(self):
        pd_result_0 = pandas.DataFrame([{'fullPath': 'TEST_1.txt', 'h5_attrs': None, 'synced': True},  # take
                                        {'fullPath': 'TEST_2.txt', 'h5_attrs': None, 'synced': True},  # drop
                                        {'fullPath': 'TEST_3.txt', 'h5_attrs': None, 'synced': True},  # take
                                        {'fullPath': 'TEST_4.txt', 'h5_attrs': {'a': 1}, 'synced': False},  # take
                                        {'fullPath': 'TEST_5.txt', 'h5_attrs': {'a': 1}, 'synced': False},  # take
                                        {'fullPath': 'TEST_6.txt', 'h5_attrs': {'a': 1}, 'synced': False},  # take
                                        ])

        pd_result_1 = pandas.DataFrame([{'fullPath': 'TEST_2.txt', 'h5_attrs': {'a': 1}, 'synced': True},  # take
                                        {'fullPath': 'TEST_3.txt', 'h5_attrs': None, 'synced': True},  # drop
                                        {'fullPath': 'TEST_4.txt', 'h5_attrs': {'a': 1}, 'synced': False},  # drop
                                        {'fullPath': 'TEST_5.txt', 'h5_attrs': None, 'synced': False},  # drop
                                        {'fullPath': 'TEST_7.txt', 'h5_attrs': {'a': 1}, 'synced': False},  # (new)
                                        ])

        SyncDBHandler._check_index_(pd_result_0)
        SyncDBHandler._check_index_(pd_result_1)

        # should mask all where synced=False
        SyncDBHandler._check_double_indexes_(pd_result_0, pd_result_1)

        # check pd_result_0
        self.assertTrue('TEST_2.txt' not in pd_result_0.index)  # 'TEST_2.hdf5' is not in pd_result_0
        # check pd_result_1
        self.assertTrue('TEST_3.txt' not in pd_result_1.index)  # 'TEST_2.hdf5' is not in pd_result_1
        self.assertTrue('TEST_4.txt' not in pd_result_1.index)  # 'TEST_2.hdf5' is not in pd_result_1
        self.assertTrue('TEST_5.txt' not in pd_result_1.index)  # 'TEST_2.hdf5' is not in pd_result_1

    # def test_update_sync_state(self):
    #     self.fail()
    #
    def test_update_hdf5_attributes(self):
        pd_result_0 = pandas.DataFrame([{'fullPath': 'TEST_1.hdf5', 'h5_attrs': {'a': 1}, 'synced': True},  # take
                                        {'fullPath': 'TEST_2.hdf5', 'h5_attrs': None, 'synced': True},  # drop
                                        {'fullPath': 'TEST_3.hdf5', 'h5_attrs': {'a': 1}, 'synced': True},  # drop
                                        {'fullPath': 'TEST_4.hdf5', 'h5_attrs': None, 'synced': False},  # drop
                                        {'fullPath': 'TEST_5.hdf5', 'h5_attrs': None, 'synced': False},  # (new)
                                        ])
        SyncDBHandler._check_index_(pd_result_0)

        pd_result_1 = pandas.DataFrame([{'fullPath': 'TEST_1.hdf5', 'synced': True},  # take
                                        {'fullPath': 'TEST_2.hdf5', 'synced': True},  # drop
                                        {'fullPath': 'TEST_3.hdf5', 'synced': True},  # drop
                                        {'fullPath': 'TEST_4.hdf5', 'synced': False},  # drop
                                        {'fullPath': 'TEST_5.hdf5', 'synced': False},  # (new)
                                        ])
        SyncDBHandler._check_index_(pd_result_1)

        for i in pd_result_0.index:
            if pd_result_0['synced'][i]:
                if isinstance(pd_result_0['h5_attrs'][i], dict):
                    attrs = pd_result_0['h5_attrs'][i]
                else:
                    attrs = {}
                with h5py.File(i, 'w') as f:
                    f.attrs.update(attrs)

        db_handler = SyncDBHandler(file_name=None)
        db_handler.dataframe = pd_result_1  # no 'h5_attrs' set

        # ---- set 'h5_attrs' and load from file ----
        db_handler.update_hdf5_attributes()
        self.assertTrue(db_handler.dataframe.loc['TEST_1.hdf5', 'h5_attrs'] == {'a': 1})  # take 'file' value
        self.assertTrue(db_handler.dataframe.loc['TEST_2.hdf5', 'h5_attrs'] == {})  # take 'file' value
        self.assertTrue(db_handler.dataframe.loc['TEST_5.hdf5', 'h5_attrs'] is None)  # file doesn't exist

        # ---- exiting values should NOT be updated ----
        # [] has to be used to set a dict with loc. (Why? No idea)
        db_handler.dataframe.loc['TEST_1.hdf5', 'h5_attrs'] = [{'a': 2}]  # different attrs
        db_handler.dataframe.loc['TEST_2.hdf5', 'h5_attrs'] = [{'a': 2}]  # attrs doesn't exist
        db_handler.dataframe.loc['TEST_5.hdf5', 'h5_attrs'] = [{'a': 2}]  # file doesn't exist

        db_handler.update_hdf5_attributes()
        self.assertTrue(db_handler.dataframe.loc['TEST_1.hdf5', 'h5_attrs'] == {'a': 2})
        self.assertTrue(db_handler.dataframe.loc['TEST_2.hdf5', 'h5_attrs'] == {'a': 2})
        self.assertTrue(db_handler.dataframe.loc['TEST_5.hdf5', 'h5_attrs'] == {'a': 2})

        # ---- force exiting values to updated ----
        db_handler.update_hdf5_attributes(update_existing=True)
        self.assertTrue(db_handler.dataframe.loc['TEST_1.hdf5', 'h5_attrs'] == {'a': 1})  # take 'file' value
        self.assertTrue(db_handler.dataframe.loc['TEST_2.hdf5', 'h5_attrs'] == {})  # take 'file' value
        self.assertTrue(db_handler.dataframe.loc['TEST_5.hdf5', 'h5_attrs'] == {'a': 2})  # take 'old' value

    def test_load_db_from_onc(self):
        db_handler = SyncDBHandler(file_name=None)
        db_handler.load_db_from_onc(dev_codes=dev_codes_deployed[0])

        self.assertTrue('h5_attrs' in db_handler.dataframe)
        self.assertTrue(any(db_handler.dataframe['deviceCode'] == dev_codes_deployed[0]))

    def tearDown(self):
        hdf5_files = glob.glob('./*.hdf5')
        for i in hdf5_files:
            os.remove(i)
