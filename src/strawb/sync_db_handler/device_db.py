import pandas

import strawb
import utm
from ..config_parser import Config
from ..onc_downloader import ONCDownloader
from strawb.sync_db_handler.base_db_handler import BaseDBHandler


class ONCDeviceDB(BaseDBHandler):
    # set defaults
    _default_raw_data_dir_ = Config.raw_data_dir
    _default_file_name_ = Config.onc_device_db

    def __init__(self, file_name='Default', update=False, load_db=True, **kwargs):
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
        kwargs: dict, optional
            parsed to ONCDownloader(**kwargs), e.g.: token, outPath, download_threads

        EXAMPLES
        --------
        Load the DB from disc (also works if there non on disc), update it and store it on disc
        >>> db = strawb.BaseDBHandler(load_db=False)  # loads the db
        >>> db.load_onc_db_update(output=True, save_db=True)

        Overwrites the existing DB, also works if there is no DB on disc.
        >>> db = strawb.BaseDBHandler(load_db=False)  # loads the db
        >>> db.load_onc_db_update(output=True, save_db=True)
        """
        self.onc_downloader = ONCDownloader(**kwargs)

        BaseDBHandler.__init__(self, file_name=file_name, update=update, load_db=load_db)

        self._df_devices_only_ = None

    def load_devices_from_onc(self, force=False):
        if self._df_devices_only_ is None or force:
            result = self.onc_downloader.getDevices()

            # convert the result to a DataFrame
            self._df_devices_only_ = pandas.DataFrame(data=result)
        return self._df_devices_only_

    def load_positions_for_devices(self, df_devices=None, force=False):
        """Load the positions of the devices (specified in df_devices). This can take some minutes.
        PARAMETER
        ---------
        df_devices: pandas.DataFrame, optional
            defines the devices to load the position. Default (None) takes the df from load_devices_from_onc().
        force: bool, optional
            if the positions should be loaded if they exist already. Default, False.
        """
        if self.dataframe is not None and not force:
            return self.dataframe

        if df_devices is None:
            if self._df_devices_only_ is None:
                self.load_devices_from_onc()
            df_devices = self._df_devices_only_

        sjt = strawb.tools.ShareJobThreads(thread_n=12)
        sjt.do(self.get_location, list(df_devices.index), df=df_devices)

        # convert the result to a DataFrame
        df_i = pandas.DataFrame(data=sjt.return_buffer)
        df_i.set_index('index', drop=True, inplace=True)

        # combine both DataFrames
        self.dataframe = df_devices.merge(df_i, how='left', left_index=True, right_index=True)
        self.add_distance_to_straw()

    def get_location(self, index, df):
        """Function to get the location of one module. The module is defined by the index and the dataframe."""

        # no data rating
        if df.loc[index].dataRating is None or df.loc[index].dataRating == []:
            return  # print(0, df.loc[index])

        # limit the `dateFrom` to get the latest position.
        # Some modules have been deployed several times (at least they report multiple locations)
        result_i = self.onc_downloader.getLocations({'deviceCode': df.loc[index].deviceCode,
                                                     'dateFrom': df.loc[index].dataRating[-1]['dateFrom']
                                                     })

        # multiple locations reported
        if len(result_i) > 1 or len(result_i) == 0:
            #         print(1, df.loc[index])
            return
        else:
            result_i[-1].update({'index': index})
            return result_i[-1]
            
    def add_distance_to_straw(self):
        """ adds position in meters to the DataFrame (normalized to STRAW-b's position, i.e. TUMSTANDARDMODULE001)"""
        mask_xy = ~(self.dataframe.lat.isnull() | self.dataframe.lon.isnull())
        # limit it to the northern hemisphere also because utm can't handle positiv and negative lat. simultaniously
        mask_xy &= self.dataframe.lat >=0 
    
        # gen two arrays with np.nan at the masked data, copy() is here important
        x = self.dataframe.lat.to_numpy().copy()
        x[mask_xy] = np.nan
        y = x.copy()
        
        x[mask_xy], y[mask_xy], _, _ = utm.from_latlon(
            self.dataframe[mask_xy].lat.to_numpy(),
            self.dataframe[mask_xy].lon.to_numpy())
    
        # normalize pos, use TUMSTANDARDMODULE001
        standard_module1 = self.dataframe[self.dataframe.deviceCode == 'TUMSTANDARDMODULE001'].iloc[0]
        x_norm, y_norm, _, _ = utm.from_latlon(standard_module1.lat, standard_module1.lon)
    
        # add positions to DataFrame
        self.dataframe['pos_x'] = x - x_norm
        self.dataframe['pos_y'] = y - y_norm
