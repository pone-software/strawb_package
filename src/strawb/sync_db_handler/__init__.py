import ast
import glob
import os
import time

import h5py
import numpy as np
import pandas

from ..config_parser import Config
from ..onc_downloader import ONCDownloader
from ..tools import human_size, ShareJobThreads


class SyncDBHandler:
    def __init__(self, file_name='Default', update=False):
        """Handle the DB, which holds the metadata from the ONC DB and adds quantities like hdf5 attributes.
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
        else:  # try to find it in raw_data_dir. Fails if more than 1 file is found or non is found
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
            try:
                dataframe.sort_values(by=['dateFrom', 'dateTo', 'deviceCode', 'dataProductCode'],
                                      inplace=True,
                                      ascending=True)  # old first, latest last
            except KeyError:
                pass
            # dataframe.sort_index(inplace=True, ignore_index=False)  # and sort it inplace
        self._dataframe = dataframe

    def load_db(self):
        """Loads the DB file into a pandas.DataFrame from the file provided at the initialisation."""
        if self.file_name is not None:
            self.dataframe = pandas.read_pickle(self.file_name)

    def save_db(self):
        """Saves the DB file into a pandas.DataFrame to the file provided at the initialisation."""
        # store information in a pandas-file
        if self.dataframe is not None:  # only save it, when there is something stored in the dataframe
            if self.file_name is None:  # in case, set the default file name
                self.file_name = Config.pandas_file_sync_db
            self.dataframe.to_pickle(self.file_name,
                                     protocol=4,  # protocol=4 compatible with python>=3.4
                                     )

    def add_new_db(self, dataframe2add, dataframe=None, ):
        """Updates a pandas.DataFrame to the internal pandas.DataFrame. If there is no internal pandas.DataFrame it set
        the provided dataframe as the internal. Otherwise it appends the dataframe to the internal.

        PARAMETER
        ---------
        dataframe2add: pandas.DataFrame
            either the index or the column name have to be 'fullPath' to prevent duplicates.
        dataframe: pandas.DataFrame, optional
            either the index or the column name have to be 'fullPath' to prevent duplicates. If None (default) it takes
            the internal database.

        RETURNS
        -------
        dataframe: pandas.DataFrame
            with the added columns. As this happens inplace, the return can be ignored.
            `dataframe = add_new_columns(dataframe2add, dataframe)` equals to
            `add_new_columns(dataframe2add, dataframe)`
        """
        to_self = False
        if dataframe is None:
            to_self = True
            dataframe = self.dataframe

        if self.dataframe is None:
            return dataframe2add  # no second dataframe defined -> nothing to add

        else:
            self._check_index_(dataframe2add)  # check the new dataframe
            self._check_index_(dataframe)  # check the new dataframe
            # append it
            self._check_double_indexes_(self.dataframe, dataframe2add)
            dataframe = dataframe.append(dataframe2add,
                                         ignore_index=False,
                                         verify_integrity=True)
            if to_self:
                self.dataframe = dataframe

        return dataframe

    def add_new_columns(self, dataframe2add, dataframe=None, overwrite=False):
        """Adds new columns from a pandas.DataFrame to the internal pandas.DataFrame. If there is no internal
        pandas.DataFrame it set the provided dataframe as the internal. Otherwise it adds the columns from the provided
         dataframe to the internal dataframe (here in-place).

        PARAMETER
        ---------
        dataframe2add: pandas.DataFrame
            either the index or the column name have to be 'fullPath' to prevent duplicates.
        dataframe: pandas.DataFrame, optional
            either the index or the column name have to be 'fullPath' to prevent duplicates. If None (default) it takes
            the internal database.

        RETURNS
        -------
        dataframe: pandas.DataFrame
            with the added columns. As this happens inplace, the return can be ignored.
            `dataframe = add_new_columns(dataframe2add, dataframe)` equals to
            `add_new_columns(dataframe2add, dataframe)`
        """
        in_place = False
        if dataframe is None:
            in_place = True
            dataframe = self.dataframe

        if dataframe is None:
            return dataframe2add  # no second dataframe defined -> nothing to add

        else:
            self._check_index_(dataframe2add)  # check the new dataframe
            self._check_index_(dataframe)  # check the new dataframe

            # handle rows with the same indexes
            intersection = dataframe2add.index.intersection(dataframe.index)
            if intersection.shape[0] != 0:
                dataframe2add_inter = dataframe2add.loc[intersection]

                for col_i in dataframe2add_inter:
                    if col_i not in dataframe:
                        # append the columns at the end: self.dataframe.keys().shape[0]
                        dataframe.insert(dataframe.keys().shape[0], col_i, dataframe2add_inter[col_i])
                    else:
                        # handle rows with the same indexes
                        intersection = dataframe.index.intersection(dataframe2add_inter.index)
                        mask_null = dataframe.loc[intersection, col_i].isnull()

                        if np.sum(mask_null):
                            dataframe.loc[intersection[mask_null], col_i] = dataframe2add_inter.loc[
                                intersection[mask_null], col_i]

                        if overwrite:
                            dataframe.loc[intersection[~mask_null], col_i] = \
                                dataframe2add_inter.loc[intersection[~mask_null], col_i]
                        elif np.sum(~mask_null) and (dataframe.loc[intersection[~mask_null], col_i] !=
                                                     dataframe2add_inter.loc[intersection[~mask_null], col_i]).any():
                            print(f'WARNING: duplicate column with different entries "{col_i}"')

            # handle rows with the new indexes
            difference = dataframe2add.index.difference(dataframe.index)
            if difference.shape[0] != 0:
                dataframe2add_diff = dataframe2add.loc[difference]
                dataframe = dataframe.append(dataframe2add_diff)

        if in_place:
            self.dataframe = dataframe

        return dataframe

    def get_mask_h5_attrs(self, dataframe=None):
        """Return a mask which mask all indexes where the column 'h5_attrs' is not 'np.nan' nor '{}'."""
        if dataframe is None:
            dataframe = self.dataframe

        mask = dataframe['h5_attrs'].isnull() + (dataframe['h5_attrs'] == {})
        return ~mask

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

    @staticmethod
    def _convert_dict_entries_(dictionary, converter):
        """Converts entries in a dictionary following the converter dict. The converter must be in the shape
        {<key>: {<value>: <replacement>} where the original dictionary is {<key>: <value>}. It also suports np.nan as
        <values>, because np.nan == np.nan if False, by default.

        PARAMETER
        ---------
        dictionary: dict
            dictionary to replace the values
        converter: dict
            The converter must be in the shape of {<key>: {<value>: <replacement>}

        EXAMPLE
        -------
        >>> con = {1: {1: 2, 2: 3}, 'a': {'b': 'c'}, 3: {np.nan: -1}}
        >>> dict_1 = {1: 1, 2: 2}
        >>> SyncDBHandler._convert_dict_entries_(dict_1, con)  # {1: 2, 2: 2}
        >>> dict_2 = {1: 2, np.nan: 2, 'a': 'b', 3: np.nan}
        >>> SyncDBHandler._convert_dict_entries_(dict_2, con)  # {1: 3, 2: 2,  3: -1, 'a': 'c'}
        """
        dictionary_return = dictionary.copy()

        # prepare converter
        converter_nan = {}
        for key_i in converter:
            for key_ii in converter[key_i]:
                if isinstance(key_ii, float) and np.isnan(key_ii):
                    converter_nan[key_i] = converter[key_i][key_ii]
                    break  # there can only be one np.nan per key_i as its a dict

        for key_i in converter:
            if key_i in dictionary:
                if dictionary[key_i] in converter[key_i]:
                    dictionary_return[key_i] = converter[key_i][dictionary[key_i]]
                elif isinstance(dictionary[key_i], float) and np.isnan(dictionary[key_i]) and key_i in converter_nan:
                    dictionary_return[key_i] = converter_nan[key_i]

        return dictionary_return

    @staticmethod
    def _convert_dict_keys_(dictionary, converter, raise_error=False):
        """Converts entries in a dictionary following the converter dict. The converter must be in the shape
        {<key>: <replacement>} where the original dictionary is {<key>: <value>}. Flipping keys isn't supported.

        PARAMETER
        ---------
        dictionary: dict
            dictionary to replace the values
        converter: dict
            The converter must be in the shape of {<key>: {<value>: <replacement>}

        EXAMPLE
        -------
        >>> SyncDBHandler._convert_dict_keys_({1: 1, 2: 2}, {1: 3})  # {3: 1, 2: 2}
        pay attention if the new key exits
        >>> SyncDBHandler._convert_dict_keys_({1: 1, 2: 2}, {1: 2})  # no change as key 2 exits -> {1: 1, 2: 2}
        >>> SyncDBHandler._convert_dict_keys_({1: 1, 2: 2}, {1: 2}, raise_error=True)  # raise an KeyError
        and flipping keys isn't supported aswell
        >>> SyncDBHandler._convert_dict_keys_({np.nan: 3, None: 4}, {np.nan: None, None: 0})

        """
        dictionary_return = dictionary.copy()

        for key_i in converter:
            if key_i in dictionary:
                if not converter[key_i] in dictionary:
                    dictionary_return[converter[key_i]] = dictionary_return.pop(key_i)
                # elif isinstance(key_i, float) and np.isnan(key_i)
                else:
                    if raise_error:
                        KeyError(f'{converter[key_i]} exists already in dictionary')

        return dictionary_return

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

        dataframe['synced'] = np.array([os.path.exists(i) for i in dataframe["fullPath"]], dtype=bool)

    def _extract_hdf5_attribute_(self, i, dataframe, entries_converter, keys_converter):
        full_path = dataframe['fullPath'].iloc[i]
        try:
            with h5py.File(full_path, 'r') as f:
                attrs_dict = dict(f.attrs)

        except OSError as err:  # file not found or can't load it
            for err_i in err.args:
                if isinstance(err_i, str) and 'file signature not found' in err_i:  # no hdf5 file
                    pass
                if isinstance(err_i, str) and 'No such file or directory' in err_i:  # filed doesn't exist
                    pass

        except Exception as err:
            print(f'WARNING: {err}')

        else:
            attrs_dict = self._convert_dict_entries_(attrs_dict, converter=entries_converter)

            attrs_dict = self._convert_dict_keys_(attrs_dict, converter=keys_converter)
            dataframe.loc[full_path, 'h5_attrs'] = [attrs_dict]  # [] has to be used to set the dict - (why?)

    def update_hdf5_attributes(self, dataframe=None, update_existing=False,
                               entries_converter=None, keys_converter=None, add_hdf5_attributes2dataframe=True):
        """Get all hdf5 file attributes from the dataframe and adds it as 'h5_attrs' to it. It can also replace keys or
        entries of the hdf5 attribute dictionary. This is controlled by entries_converter and keys_converter
        PARAMETER
        ---------
        dataframe: pandas.DataFrame
            either the index or the column name have to be 'fullPath' to prevent duplicates. If None (default) it takes
            the internal dataframe.
        update_existing: bool, optional
            if existing attributes should be loaded again (True) or not (False, default)
        entries_converter: dict or None, optional
            a dict parsed to _convert_dict_entries_(). If None (default) it uses:
            {'previous_file_id': {np.nan: 0}, 'following_file_id': {np.nan: 0}}
        keys_converter: dict or None, optional
            a dict parsed to _convert_dict_keys_(). If None (default) it uses:
            {'mes_typ': 'measurement_type', 'mes_duration': 'measurement_duration'}
        add_hdf5_attributes2dataframe: bool, optional
            if the hdf5_attributes should be added to the dataframe as new columns.
            A hdf5_attributes={'file_id'=123} will result in a dataframe column 'file_id'.
        """

        if dataframe is None:
            dataframe = self.dataframe
        if dataframe is None:  # when self.dataframe is None
            return

        if 'h5_attrs' not in dataframe:
            # add column
            dataframe.insert(dataframe.columns.shape[0], 'h5_attrs', None)
            # take all
            items_to_check = dataframe['synced'].copy()  # exclude non existing files
        elif update_existing:
            # take all
            items_to_check = dataframe['synced'].copy()  # exclude non existing files
        else:
            # take only the one with missing parameters
            items_to_check = dataframe.h5_attrs.isnull()  # takes all None or np.nan

        # include only file which ends with 'hdf5' or 'h5'
        items_to_check &= dataframe.fullPath.str.endswith('hdf5') | dataframe.fullPath.str.endswith('h5')
        items_to_check &= dataframe['synced']  # exclude non existing files

        # convert file_id's with nan to int. Otherwise pandas interprets the Series as float and the resolution
        # of the np.float64 isn't sufficient for a np.uint64.
        if entries_converter is None:
            entries_converter = {'previous_file_id': {np.nan: 0}, 'following_file_id': {np.nan: 0}}

        if keys_converter is None:
            keys_converter = {'mes_typ': 'measurement_type', 'mes_duration': 'measurement_duration',
                              'mes_steps': 'measurement_steps'}

        sjt = ShareJobThreads(thread_n=5)
        sjt.do(self._extract_hdf5_attribute_,
               np.argwhere(items_to_check.to_numpy(dtype=bool)).flatten(),
               dataframe=dataframe,
               entries_converter=entries_converter,
               keys_converter=keys_converter)

        if add_hdf5_attributes2dataframe:
            h5_dataframe = self.dataframe_from_hdf5_attributes(dataframe=dataframe)
            dataframe = self.add_new_columns(dataframe2add=h5_dataframe, dataframe=dataframe, overwrite=True)

        return dataframe

    def dataframe_from_hdf5_attributes(self, dataframe=None):
        """Generates a dataframe from the SDAQ hdf5 file attributes. There must be at least the keys (columns):
        'file_start', 'file_end', 'run_start' and 'run_end'.

        PARAMETER
        ---------
        dataframe: pandas.DataFrame
            either the index or the column name have to be 'fullPath' to prevent duplicates. If None (default) it takes
            the internal dataframe. Attention, this does NOT happen inplace.

        RETURN
        ------
        h5_dataframe: pandas.DataFrame
            a pandas.DataFrame from the hdf5 file attributes. This is a new DataFrame and independent from the provided
            dataframe. Therefore, both DataFrames have to be combined in case this is needed.
        """
        if dataframe is None:
            dataframe = self.dataframe
        if dataframe is None:  # when self.dataframe is None
            return

        self._check_index_(dataframe)
        mask = self.get_mask_h5_attrs(dataframe)
        h5_dataframe = pandas.DataFrame(dataframe[mask]['h5_attrs'].to_list(),
                                        index=dataframe[mask]['fullPath'])

        # append the columns needed
        missing = {'rollover_interval', 'file_start', 'file_end',
                   'run_start', 'run_end'}.difference(h5_dataframe.columns)
        for i in missing:
            h5_dataframe[i] = None

        # format the columns
        h5_dataframe.rollover_interval.apply(
            lambda x: ast.literal_eval(str(x)))  # is dataframe string like "{'days': 1}"
        h5_dataframe.file_start = pandas.to_datetime(h5_dataframe.file_start,
                                                     unit='s', errors='coerce', utc=True, infer_datetime_format=True)
        h5_dataframe.file_end = pandas.to_datetime(h5_dataframe.file_end,
                                                   unit='s', errors='coerce', utc=True, infer_datetime_format=True)
        h5_dataframe.run_start = pandas.to_datetime(h5_dataframe.run_start,
                                                    unit='s', errors='coerce', utc=True, infer_datetime_format=True)
        h5_dataframe.run_end = pandas.to_datetime(h5_dataframe.run_end,
                                                  unit='s', errors='coerce', utc=True, infer_datetime_format=True)
        return h5_dataframe

    def load_db_from_onc(self, output=False, download=False, add_hdf5_attributes=True, add_dataframe=True, **kwargs):
        """Loads and downloads the db directly from the ONC server.

        PARAMETER
        ---------
        output: bool, optional
            if information about the progress should be printed
        download: bool, optional
            if the missing files should be downloaded.
        add_hdf5_attributes: bool, optional
            scan files for hdf5 attributes and adds to the dataframe as new columns
        add_dataframe: bool, optional
            if the dataframe should be added to the internal dataframe or not. Default is True.
        kwargs: dict, optional
            parsed to ONCDownloader().get_files_structured(**kwargs) to filter the files. Parameters are e.g.:
            dev_codes, date_from, date_to, extensions, min_file_size, and max_file_size.
        """
        if output:
            print('-> Get metadata from ONC DB')

        dataframe = ONCDownloader().get_files_structured(**kwargs)
        return self.update_db_and_load_files(dataframe,
                                             output=output,
                                             download=download,
                                             add_hdf5_attributes=add_hdf5_attributes,
                                             add_dataframe=add_dataframe)

    def update_db_and_load_files(self, dataframe, output=False, download=False, add_hdf5_attributes=True,
                                 add_dataframe=True):
        """Depending which options are set, this function does any combination of the following three tasks:
        1. `download=True` -> loads all missing files from the dataframe
        2. `add_hdf5_attributes=True` -> updates the hdf5 attributes from the files which are present on the disc
        3. `add_dataframe=True` -> adds the dataframe to the internal stored DB (must be saved separately to disc)


        PARAMETER
        ---------
        download: bool, optional
            if the missing files should be downloaded.
        add_hdf5_attributes: bool, optional
            scan files for hdf5 attributes and adds to the dataframe as new columns
        add_dataframe: bool, optional
            if the dataframe should be added to the internal dataframe or not. Default is True.
        kwargs: dict, optional
            parsed to ONCDownloader().get_files_structured(**kwargs) to filter the files. Parameters are e.g.:
            dev_codes, date_from, date_to, extensions, min_file_size, and max_file_size.
        """
        # remove the pointer to the original dataframe,
        # i.e. if it is a slice <-> update_db_and_load_files(dataframe[mask])
        dataframe = dataframe.copy()

        self.update_sync_state(dataframe=dataframe)
        if output:
            download_size = (dataframe[~dataframe['synced']]['fileSize']).sum()
            print(f'  In total: {dataframe.shape[0]} files; skips synced: {dataframe["synced"].sum()}; '
                  f'size to download: {human_size(download_size)}, '
                  f'from deviceCode: {pandas.unique(dataframe["deviceCode"])}')

        if download:
            if output:
                print('\n-> Download the files from the ONC server')
            # download the files which passed the filter
            ONCDownloader().getDirectFiles(filters_or_result=dataframe[~dataframe['synced']])
            self.update_sync_state(dataframe=dataframe)

        if add_hdf5_attributes:
            if output:
                print('\n-> Update hdf5 attributes')
            self.update_hdf5_attributes(dataframe=dataframe, add_hdf5_attributes2dataframe=True)

        if add_dataframe:
            if output:
                print('\n-> Add to db')
            # here 'self.dataframe =' is important as it could be None before and that brakes the inplace
            self.dataframe = self.add_new_columns(dataframe2add=dataframe, dataframe=self.dataframe, overwrite=True)

        return dataframe

    def load_entire_db_from_ONC(self, **kwargs):
        kwargs.update(dict(date_from='strawb_all'))
        return self.load_db_from_onc(**kwargs)

    def get_files_from_names(self, file_names):
        """Checks:
        1. if all files are listed in the DB. If not it raise a ValueError.
        2. if all files are downloaded. In case load the missing files
        3. return the masked dataframe with entries to the related file

        PARAMETER
        ---------
        file_name: Union(str, list, set)
            The file_names, it can be multiple file names as a list or set, or one as a str.
        """

        if isinstance(file_names, str):
            file_names = {file_names}  # convert to a set
        else:
            file_names = set(file_names)

        difference = file_names.difference(set(self.dataframe.filename))

        if difference:
            raise ValueError(f"The following files can't be found in the DB: {difference}")

        mask = self.dataframe.filename == ''
        for i in file_names:
            mask |= self.dataframe.filename == i

        if not all(self.dataframe.synced[mask]):
            return self.update_db_and_load_files(self.dataframe[mask], download=True)

        else:
            return self.dataframe[mask]
