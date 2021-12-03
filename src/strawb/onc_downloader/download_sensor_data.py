import pandas
import numpy as np
import datetime
import h5py
import time
from src.strawb.onc_downloader import ONCDownloader


# TODO: get this section updated with the feedback from ONC. Now it doesn't work as download from ONC is very slow.
#  `onc_downloader.getDirectByDevice` is the problem.

# # code to execute
# # define the period a file should cover
# timedelta = np.timedelta64(3, 'h')
# time_array = np.arange(np.datetime64('2021-10-10'),
#                        np.datetime64('2021-10-11'),
#                        timedelta).astype('datetime64[ms]')
#
# # define function to download one file
# def get_file(np_datetime64):
#     filters = {'deviceCode': 'ONCMJB016',  # 'NORTEKAQDCM9987', #'NORTEKAQDCM2886',
#                'dateFrom': np.datetime_as_string(np_datetime64, timezone='UTC'),  # '2021-08-03T00:00:00.000Z',
#                'dateTo': np.datetime_as_string(np_datetime64 + timedelta - np.timedelta64(1, 'ms'), timezone='UTC'),
#                # '2021-08-03T23:59:59.000Z',
#                }
#     dev = ONCDevice(filters=filters)
#     dev.to_hdf5()
#     return dev
#
# # download parallel
# sjt = strawb.tools.ShareJobThreads(thread_n=1)
# sjt.do(get_file, time_array)

def convert_str2timestamp(value, fmt='%Y-%m-%dT%H:%M:%S.%fZ'):
    return datetime.datetime.strptime(value, fmt).timestamp()


class SensorData:
    def __init__(self, sensor_dict, sensor=None):
        """ Represents the data from a single ONC sensorData. Located at result['sensorData'][i] for all i.

        sensor_dict: dictionary
            dictionary which is a item `result['sensorData']` list. `result` is the return dictionary of the ONC
            `getDirectByDevice()` function.
            result = onc_downloader.getDirectByDevice(...)
            sensor_dict = result['sensorData'][i]  # take the item i, i.e.: i=0
        sensor: str, optional
            specifies the name for the sensor data. Used at pandas.DataFrame column name. If None (default) it takes
            sensor_dict['sensorCode'].
        """
        if sensor is None:
            self.sensor = sensor_dict['sensorCode']
        else:
            self.sensor = sensor

        self.dataframe = self.__get_dataframe__(sensor_dict)

        self.attributes = sensor_dict.copy()
        self.attributes.pop('data')  # remove the data
        self.attributes.pop('actualSamples')  # remove the number of data entries

    def __get_dataframe__(self, sensor_dict):
        t = pandas.to_datetime(sensor_dict['data']['sampleTimes'], utc=True, infer_datetime_format=True)
        t = t.round(freq='ms')  # round from ms to s happens inplace

        df = pandas.DataFrame({  # 'qaqcFlags': self.qaqcFlags,
            self.sensor: sensor_dict['data']['values']},
            index=t)
        return df[~df[self.sensor].isnull()]

    def __repr__(self):
        return f'<{type(self).__name__}: {self.sensor}>'


class SensorGroup:
    def __init__(self, group='data'):
        """Represent a sensor group, i.e. port of the miniJB (e.g. 'p4'). The group groups multiple SensorData objects.
         SensorData objects are added with SensorGroup.add_obj(sensor_data). It stores the data of all sensors in a
         pandas DataFrame in addition.

         PARAMETER
         ---------
         group: str, optional
            defines the name of the group. Default is 'data'.
         """
        self.group = group

        self.sensor_dict = {}
        self.dataframe = None

    def add_sensor(self, sensor_data: SensorData):
        """Adds a sensor_data to the internal list and to the dataframe."""
        self.sensor_dict[sensor_data.sensor] = sensor_data
        self.dataframe = self.add_new_columns(sensor_data.dataframe)

    def add_new_columns(self, dataframe2add, dataframe=None, overwrite=False):
        """Adds new columns from a pandas.DataFrame to the internal pandas.DataFrame. If there is no internal
        pandas.DataFrame it set the provided dataframe as the internal. Otherwise it adds the columns from the provided
         dataframe to the internal dataframe.

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
        if dataframe is None and self.dataframe is not None:
            dataframe = self.dataframe.copy()

        if dataframe is None:
            return dataframe2add  # no second dataframe defined -> nothing to add

        else:
            for col_i in dataframe2add:
                if col_i not in dataframe:
                    # append the columns at the end: self.dataframe.keys().shape[0]
                    dataframe.insert(dataframe.keys().shape[0], col_i, dataframe2add[col_i])
                else:
                    # handle rows with the same indexes
                    intersection = dataframe.index.intersection(dataframe2add.index)
                    mask_null = dataframe.loc[intersection, col_i].isnull()

                    if np.sum(mask_null):
                        dataframe.loc[intersection[mask_null], col_i] = dataframe2add.loc[
                            intersection[mask_null], col_i]

                    if overwrite:
                        dataframe.loc[intersection[~mask_null], col_i] = \
                            dataframe2add.loc[intersection[~mask_null], col_i]
                    elif np.sum(~mask_null) and (dataframe.loc[intersection[~mask_null], col_i] !=
                                                 dataframe2add.loc[intersection[~mask_null], col_i]).any():
                        print(f'WARNING: duplicate column with different entries "{col_i}"')

                    # handle rows with the new indexes
                    difference = dataframe2add.index.difference(dataframe.index)
                    for i in difference:
                        dataframe.loc[i, col_i] = dataframe2add.loc[i, col_i]

        return dataframe


class ONCDevice:
    def __init__(self, result=None, filters=None, onc_downloader=None):
        """Process the data from result=onc.getDirectByDevice(filters). Either the result or the filter can be parsed.
        In addition it distinguish between an ONC miniJB (ONCMJB) and other devices. It separates the data into
        sensor_groups. The sensor_group holds the data in panda.DataFrames together with metadata of the sensor. An
        export to hdf5 files is possible too.

        PARAMETERS
        ----------
        result: dict, optional
            a result dict from onc_downloader.getDirectByDevice. One of `results` or `filters` have to be not None.
        filters: dict, optional
            a filter parsed to onc_downloader.getDirectByDevice(filters=filters). One of `results` or `filters` have to
            be not None.
        """
        if onc_downloader is None:
            self.onc_downloader = ONCDownloader(showInfo=False, timeout=120)
        elif isinstance(onc_downloader, ONCDownloader):
            self.onc_downloader = onc_downloader
        else:
            raise TypeError(f'<onc_downloader> must be None or of type <ONCDownloader>. Got: {type(onc_downloader)}')

        if filters is not None:  # get data
            print(f'download: {filters}')
            t_0 = time.time()
            self.result = onc_downloader.getDirectByDevice(filters, allPages=True)
            print(f'downloaded: {time.time() - t_0:.2f}')
        elif result is not None:
            self.result = result
        else:
            raise ValueError('One of `results` or `filters` have to be not None.')

        self.device_code = self.result['parameters']['deviceCode']
        self.sensor_groups = {}

        if self.result['sensorData'] is None:
            print('WARNING: no data downloaded')
            pass
        elif 'ONCMJB' in self.device_code:
            for i in self.result['sensorData']:
                port, sensor_name = self.mini_jb_split_port(i['sensorCode'])

                if port not in self.sensor_groups:
                    self.sensor_groups[port] = SensorGroup(port)

                self.sensor_groups[port].add_sensor(SensorData(i, sensor_name))

        else:
            self.sensor_groups['data'] = SensorGroup()
            for i in self.result['sensorData']:
                self.sensor_groups['data'].add_sensor(SensorData(i))

    @staticmethod
    def mini_jb_split_port(label, skip_head: int = 1):
        """ Split the port label from the ONC label. 'p10c_returncurrent' -> 'p10', 'c_returncurrent'
        It skips the indexes and look for the first non decimal values, i.e. 'p' and 'c', respectively.
        PARAMETER
        ---------
        label: str
            the label, i.e. 'p10c_returncurrent'
        skip_head: int, optional
            skip the n leading entries, e.g. 1: -> 'p'
        """
        for i, label_i in enumerate(label[skip_head:]):
            if not label_i.isdecimal():
                return label[:i + 1], label.split('_', 1)[-1]  # b[i+1:]

    def to_hdf5(self, file_name: str = None, h5py_dataset_options: dict = None):
        """Save device data as hdf5 file. Each sensor_groups gets its own group.
        PARAMETERS
        ----------
        file_name: str, optional
            the file name of the resulting hdf5 file. If None (default), use the original ONC file naming.
            <device_code>_<date_from>.h5
        h5py_dataset_options: None, optional
            dictionary for h5py.create_dataset. If None (default) it takes:
            {'compression': 'gzip', 'compression_opts': 9, 'shuffle': True, 'fletcher32': True}

        """
        if file_name is None:
            date_from = self.result['parameters']['dateFrom']
            date_from = date_from.replace(':', '').replace('-', '')
            file_name = f"{self.device_code}_{date_from}.hdf5"
            print(file_name)

        if h5py_dataset_options is None:
            h5py_dataset_options = {'compression': 'gzip',
                                    'compression_opts': 9,
                                    'shuffle': True,
                                    'fletcher32': True}

        with h5py.File(file_name, 'w') as f:
            # only included specified fields as hdf5 attr
            parameters = {'file_start': convert_str2timestamp(self.result['parameters']['dateFrom']),
                          'file_end': convert_str2timestamp(self.result['parameters']['dateTo']),
                          'deviceCode': self.device_code}
            f.attrs.update(parameters)

            for i, sensor_group_i in self.sensor_groups.items():
                group = f.create_group(i)
                # add time as seconds since epoch
                group.create_dataset('time',
                                     data=sensor_group_i.dataframe.index.to_numpy(dtype=float),
                                     **h5py_dataset_options)

                for sensor_i in sensor_group_i.dataframe:
                    dataset = group.create_dataset(sensor_i,
                                                   data=sensor_group_i.dataframe[sensor_i],
                                                   **h5py_dataset_options)
                    dataset.attrs.update(sensor_group_i.sensor_dict[sensor_i].attributes)
