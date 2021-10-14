import glob
import os

import h5py
import numpy as np
import pandas

from ..config_parser import Config
from ..onc_downloader import ONCDownloader


class SyncDBHandler:
    def __init__(self, file_name='Default', update=False):
        """Handle the DB
        PARAMETER
        file_name: Union[str, None], optional
            If None, it doesn't load the DB. If it is a string, it can be:
            - 'Default' it takes Config.pandas_file_sync_db
            - the full path to the DB
            - a relative path to the DB
            - a file name which is anywhere located in the strawb.Config.raw_data_dir
        update: bool, optional
            defines if the entries should be checked against existing files
        """

        # find handle file_name and fine it.
        if file_name is None:
            self.file_name = None
        elif file_name == 'Default':  # take the default or None if it doesn't exist
            if os.path.exists(Config.pandas_file_sync_db):
                self.file_name = Config.pandas_file_sync_db
            else:
                self.file_name = None
        elif os.path.exists(file_name):  # if the file/path exists
            self.file_name = os.path.abspath(file_name)
        elif os.path.exists(os.path.join(Config.raw_data_dir, file_name)):  # maybe with raw_data_dir as path
            path = os.path.join(Config.raw_data_dir, file_name)
            self.file_name = os.path.abspath(path)
        else:  # try to fine it in raw_data_dir. Fails if more than 1 file is found or non is found
            file_name_list = glob.glob(Config.raw_data_dir + "/**/" + file_name, recursive=True)
            if len(file_name_list) == 1:
                self.file_name = file_name_list[0]
            else:
                if not file_name_list:
                    raise FileNotFoundError(f'{file_name} not found nor matches any file in "{Config.raw_data_dir}"')
                else:
                    raise FileExistsError(f'{file_name} matches multiple files in "{Config.raw_data_dir}": '
                                          f'{file_name_list}')

        self.dataframe = None  # stores the db in a pandas data frame

        self.load_db()  # loads the db if file is valid

        if update and self.dataframe is not None:
            self.update_sync_state()
            self.update_hdf5_attributes()

    @property
    def dataframe(self):
        return self._dataframe

    @dataframe.setter
    def dataframe(self, dataframe):
        if dataframe is not None:
            self._check_index_(dataframe)  # sets column 'fullPath' as index or check that index is 'fullPath'
            dataframe.sort_index(inplace=True, ignore_index=False)  # and sort it inplace
        self._dataframe = dataframe

    def load_db(self):
        """Loads the DB file into a pandas.DataFrame from the file provided at the initialisation."""
        if self.file_name is not None:
            self.dataframe = pandas.read_pickle(self.file_name)

    def save_db(self):
        """Saves the DB file into a pandas.DataFrame to the file provided at the initialisation."""
        # store information in a pandas-file
        if self.file_name is not None and self.dataframe is not None:
            self.dataframe.to_pickle(self.file_name,
                                     protocol=4,  # protocol=4 compatible with python>=3.4
                                     )

    def add_new_db(self, dataframe):
        """Updates a pandas.DataFrame to the internal pandas.DataFrame. If there is no internal pandas.DataFrame it set
        the provided dataframe as the internal. Otherwise it appends the dataframe to the internal.
        PARAMETER
        ---------
        dataframe: pandas.DataFrame
            either the index or the column name have to be 'fullPath' to prevent duplicates.
        """
        self._check_index_(dataframe)  # check the new dataframe

        if self.dataframe is None:
            self.dataframe = dataframe
        else:
            # append it
            self._check_double_indexes_(self.dataframe, dataframe)
            self.dataframe = self.dataframe.append(dataframe,
                                                   ignore_index=False,
                                                   verify_integrity=True)

    @staticmethod
    def _check_double_indexes_(a, b):
        """Check if two datasets have the same indexes and delete this index (drop=pop index) from one of the datasets.
        The dataset to delete from, is chosen if the datasets has something stored in column 'h5_attrs', with a higher
        priority for a. The indexes are deleted 'inplace' for both datasets.
        PARAMETER
        ---------
        a: dataset
        b: dataset
        """
        if 'h5_attrs' not in a:
            a['h5_attrs'] = None
        if 'h5_attrs' not in b:
            b['h5_attrs'] = None

        for i, b_i in enumerate(b.index):
            if b_i in a.index:
                # if 'h5_attrs' are available in b but not in db_handler.dataframe -> db_handler.dataframe.drop
                if a['h5_attrs'][b_i] is None and not b['h5_attrs'][b_i] is None:
                    a.drop(index=b_i, inplace=True)

                # if 'h5_attrs' are available in db_handler.dataframe but not in b -> b.drop
                # or if 'h5_attrs' is not available in db_handler.dataframe nor b -> b.drop
                else:
                    b.drop(index=b_i, inplace=True)

    @staticmethod
    def _check_index_(dataframe):
        """Checks if dataframe has the right ('fullPath') index. In case set the column 'fullPath' as the index.

        PARAMETER
        ---------
        dataframe: Union[None, pandas.DataFrame], optional
            the dataframe to check
        """

        if dataframe.index.name != 'fullPath':
            dataframe.set_index(['fullPath'],
                                inplace=True,
                                verify_integrity=True,
                                drop=False,
                                )

    def update_sync_state(self, dataframe=None):
        """Checks if the sync state of all items in the dataframe.
        PARAMETER
        ---------
        dataframe: Union[None, pandas.DataFrame], optional
            If None (default) it checks the internal dataframe. Otherwise it checks the provided dataframe.
        """
        if dataframe is None:
            dataframe = self.dataframe
        if dataframe is None:  # when self.dataframe is None
            return

        dataframe['synced'] = np.array([os.path.exists(i) for i in dataframe["fullPath"]])

    def update_hdf5_attributes(self, dataframe=None, update_existing=False):
        """Get all hdf5 file attributes from the dataframe and adds it as 'h5_attrs' to it.
        PARAMETER
        ---------
        dataframe: pandas.DataFrame
            either the index or the column name have to be 'fullPath' to prevent duplicates.
        update_existing: bool, optional
            if existing attributes should be loaded again (True) or not (False, default)
        """
        if dataframe is None:
            dataframe = self.dataframe
        if dataframe is None:  # when self.dataframe is None
            return

        if 'h5_attrs' not in dataframe:
            # add column
            dataframe.insert(dataframe.columns.shape[0], 'h5_attrs', None)
            # take all
            items_to_check = np.ones_like(dataframe['fullPath'], dtype=bool)
        elif update_existing:
            # take all
            items_to_check = np.ones_like(dataframe['fullPath'], dtype=bool)
        else:
            # take only the one with missing parameters
            items_to_check = (dataframe['h5_attrs'].isnull()).to_numpy(dtype=bool)  # takes all None or np.nan

        items_to_check[~dataframe['synced']] = False  # exclude non existing files

        for i in np.argwhere(items_to_check).flatten():
            full_path = dataframe['fullPath'].iloc[i]
            # if full_path.endswith('hdf5') or full_path.endswith('h5'):
            try:
                with h5py.File(full_path, 'r') as f:
                    dataframe.loc[full_path, 'h5_attrs'] = [dict(f.attrs)]  # [] has to be used to set the dict - (why?)

            except OSError as err:  # file not found or can't load it
                for err_i in err.args:
                    if isinstance(err_i, str) and 'file signature not found' in err_i:  # no hdf5 file
                        pass
                    if isinstance(err_i, str) and 'No such file or directory' in err_i:  # filed doesn't exist
                        pass

            except Exception as err:
                print(f'WARNING: {err}')

    def load_db_from_onc(self, **kwargs):
        """Loads downloads the db directly from the ONC server.
        PARAMETER
        ---------
        kwargs: dict, optional
            kwargs are parsed to strawb.ONCDownloader().download_structured. 'download' will be set to False.
        """
        kwargs.update(dict(download=False))

        onc_downloader = ONCDownloader()
        self.dataframe = onc_downloader.download_structured(**kwargs)
        self.update_hdf5_attributes()

    def load_entire_db_from_ONC(self, **kwargs):
        kwargs.update(dict(date_from='strawb_all', download=False))
        self.load_db_from_onc(**kwargs)
