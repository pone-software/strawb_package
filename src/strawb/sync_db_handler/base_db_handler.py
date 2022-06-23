import glob
import os

import pandas


class BaseDBHandler:
    # set defaults
    _default_file_name_ = None
    _default_raw_data_dir_ = None

    def __init__(self, file_name='Default', update=False, load_db=True):
        """Handle the DB, which holds the metadata from the ONC DB and adds quantities like hdf5 attributes.
        PARAMETER
        ---------
        file_name: Union[str, None], optional
            If None, it doesn't load the DB. If it is a string, it can be:
            - 'Default' it takes Config.pandas_file_sync_db
            - the full path to the DB
            - a relative path to the DB
            - a file name which is anywhere located in the strawb.Config.raw_data_dir
        update: bool, optional
            defines if the entries should be checked against existing files
        load_db: bool, update
            True (default) loads the DB if it exists and if `file_name` is not None. False doesn't load it.

        EXAMPLES
        --------
        Load the DB from disc (also works if there non on disc), update it and store it on disc
        >>> db = strawb.BaseDBHandler(load_db=False)  # loads the db
        >>> db.load_onc_db_update(output=True, save_db=True)

        Overwrites the existing DB, also works if there is no DB on disc.
        >>> db = strawb.BaseDBHandler(load_db=False)  # loads the db
        >>> db.load_onc_db_update(output=True, save_db=True)
        """
        self.dataframe = None  # stores the db in a pandas data frame

        if self._default_file_name_ is None:
            print(f"WARNING: _default_file_name_ isn't set")
        if self._default_raw_data_dir_ is None:
            print(f"WARNING: _default_raw_data_dir_ isn't set")

        # handle file_name or try to find it.
        self.file_name = None
        if file_name is None:  # non, doesn't load the DB
            pass
        elif file_name == 'Default':  # take the default
            self.file_name = self._default_file_name_
        elif os.path.isabs(file_name):
            self.file_name = file_name
        elif os.path.exists(file_name):  # if the file/path exists
            self.file_name = os.path.abspath(file_name)
        elif os.path.exists(os.path.join(self._default_raw_data_dir_, file_name)):  # maybe with raw_data_dir as path
            path = os.path.join(self._default_raw_data_dir_, file_name)
            self.file_name = os.path.abspath(path)
        else:  # try to find it in raw_data_dir. Fails if more than 1 file is found or non is found
            file_name_list = glob.glob(self._default_raw_data_dir_ + "/**/" + file_name, recursive=True)
            if len(file_name_list) == 1:
                self.file_name = file_name_list[0]
            else:
                if file_name_list:
                    raise FileExistsError(f'{file_name} matches multiple files in "{self._default_raw_data_dir_}": '
                                          f'{file_name_list}')

        if load_db:
            self.load_db()  # loads the db if file is valid
            # load the DB only if the file exists, i.e. file_name = 'Default'
            if update:
                self.update()

    def load_db(self):
        """Loads the DB file into a pandas.DataFrame from the file provided at the initialisation."""
        #  if self.file_name is not None:
        if self.file_name is None:
            raise ValueError(f"File_name is None. Can't load the file.")
        elif not os.path.exists(self.file_name):
            raise FileNotFoundError(f"{self.file_name} doesn't exist -> load data and execute .save_db() to create it.")
        else:
            self.dataframe = pandas.read_pickle(self.file_name)

    def save_db(self):
        """Saves the DB file into a pandas.DataFrame to the file provided at the initialisation."""
        # store information in a pandas-file
        if self.file_name is None:
            raise ValueError(f"File_name is None -> save_db can't be executed")
        if self.dataframe is not None:  # only save it, when there is something stored in the dataframe
            # check if the directory exits, if not create it
            os.makedirs(os.path.dirname(self.file_name), exist_ok=True)  # exist_ok, doesn't raise an error if it exists

            # if self.file_name is None:  # in case, set the default file name
            #     self.file_name = Config.pandas_file_sync_db
            self.dataframe.to_pickle(self.file_name,
                                     protocol=4,  # protocol=4 compatible with python>=3.4
                                     )

    def update(self):
        pass
