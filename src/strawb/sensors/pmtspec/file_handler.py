# Author: Kilian Holzapfel <kilian.holzapfel@tum.de>
import numpy as np
import pandas

from strawb.base_file_handler import BaseFileHandler


class FileHandler(BaseFileHandler):
    def __init__(self, *args, **kwargs):
        """The File Handler of the PMTSpectrometer hdf5 data."""
        # Counter
        self.counts_time = None  # absolute timestamps in seconds for each counts reading
        self.counts_ch0 = None  # channel which counts up at a constant frequency -> PMT Spectrometer
        self.counts_ch1 = None  # the PMT channel 1.
        self.counts_ch3 = None  # the PMT channel
        self.counts_ch5 = None  # the PMT channel
        self.counts_ch6 = None  # the PMT channel
        self.counts_ch7 = None  # the PMT channel
        self.counts_ch8 = None  # the PMT channel
        self.counts_ch9 = None  # the PMT channel
        self.counts_ch10 = None  # the PMT channel
        self.counts_ch11 = None  # the PMT channel
        self.counts_ch12 = None  # the PMT channel
        self.counts_ch13 = None  # the PMT channel
        self.counts_ch15 = None  # the PMT channel

        # interpolated rates. Based on the `counts` and interpolated to fit a artificially readout frequency.
        self.interp_frequency = None  # artificially readout frequency
        self.interp_time = None  # absolute timestamps. Shape: [time_j]
        self.interp_rates = None  # rates a s a 2d array. Shape: [channel_i, time_j]

        # Padiwa Settings thresholds
        self.padiwa_time = None
        self.padiwa_th1 = None  # 350 nm
        self.padiwa_th2 = None  # 400 nm
        self.padiwa_th3 = None  # 425 nm
        self.padiwa_th4 = None  # 450 nm
        self.padiwa_th5 = None  # 460 nm
        self.padiwa_th6 = None  # 470 nm
        self.padiwa_th7 = None  # 480 nm
        self.padiwa_th8 = None  # 492 nm
        self.padiwa_th9 = None  # not connected
        self.padiwa_th10 = None  # not connected
        self.padiwa_th11 = None  # 510 nm
        self.padiwa_th12 = None  # 525 nm
        self.padiwa_th13 = None  # 550 nm
        self.padiwa_th14 = None  # NO FILTER
        self.padiwa_th15 = None  # not connected
        self.padiwa_th16 = None  # not connected
        self.padiwa_offset = None
        self.padiwa_power = None

        self.channel_id = None
        self.counts_raw = None

        # HV-PMT Settings
        self.hv_time = None
        self.hv_ch0 = None  # 350 nm
        self.hv_ch1 = None  # 400 nm, 480 nm
        self.hv_ch2 = None  # 425 nm
        self.hv_ch3 = None  # 450 nm, 470 nm
        self.hv_ch4 = None  # 460 nm, 492 nm
        self.hv_ch5 = None  # 510 nm, 550 nm
        self.hv_ch6 = None  # 525 nm
        self.hv_ch7 = None  # NO FILTER
        self.hv_ch8 = None  # not connected
        self.hv_ch9 = None  # not connected
        self.hv_ch10 = None  # not connected
        self.hv_ch11 = None  # not connected
        self.hv_ch12 = None  # not connected
        self.hv_ch13 = None  # not connected
        self.hv_ch14 = None  # not connected
        self.hv_ch15 = None  # not connected
        self.hv_power = None

        # TRB Settings
        self.daq_frequency_readout = None
        self.daq_state = None
        self.daq_time = None
        self.daq_trb = None

        # holds the file version
        self.file_version = None

        # comes last to load the data in case file_name is set
        BaseFileHandler.__init__(self, *args, **kwargs)

    def __load_meta_data__(self, ):
        # 'counts' (older files 'rates') is the measurement data and most important group
        if not ('counts' in self.file or 'rates' in self.file):
            raise KeyError('missing important group')

        err_list = []
        for i in [self.__load_meta_data_v6__, self.__load_meta_data_v5__, self.__load_meta_data_v4__,
                  self.__load_meta_data_v3__, self.__load_meta_data_v2__, self.__load_meta_data_v1__]:
            try:
                i()  # try file versions
                return
            # version is detected because datasets in the hdf5 aren't present -> i() fails with KeyError
            except (TypeError, KeyError) as a:
                err_list.append(a.args[0])

        raise KeyError('; '.join(err_list))

    def __load_meta_data_v1__(self, ):
        """In older versions, only the counts have been written.
        `padiwa`, `hv`, and `daq` not, because there was no change. Support it here.
        This version has no: `padiwa`, `hv`, and `daq`."""
        self.__load_counts_v1__()
        self.file_version = 1

        # its the default frequency to fix files where writing failed
        self.daq_frequency_readout = np.array([10000.], dtype=np.float32)

    def __load_meta_data_v2__(self, ):
        """In older versions, only the counts have been written.
        `padiwa`, `hv`, and `daq` not, because there was no change. Support it here.
        This version has `padiwa`, `hv`, and `daq`."""
        self.__load_counts_v1__()
        self.__load_padiwa_v1__()
        self.__load_hv__()
        self.__load_daq_v1__()
        self.file_version = 2

    def __load_meta_data_v3__(self, ):
        """
        In older versions, only the counts have been written.
        `padiwa`, `hv`, and `daq` not, because there was no change. Support it here.
        This version has no: `padiwa`, `hv`, and `daq`.

        CHANGES to v2:
        - renamed group `rates` to `counts`: `rates/ch0` -> `counts/ch0`
        """
        self.__load_counts_v2__()
        self.file_version = 3

        # its the default frequency to fix files where writing failed
        self.daq_frequency_readout = np.array([10000.], dtype=np.float32)

    def __load_meta_data_v4__(self, ):
        """Similar to file_version v2 with `padiwa`, `hv`, and `daq`.
        This version has: `padiwa`, `hv`, and `daq`.

        CHANGES to v3:
        - This version has: `padiwa`, `hv`, and `daq`.
        """
        self.__load_counts_v2__()
        self.__load_padiwa_v1__()
        self.__load_hv__()
        self.__load_daq_v1__()
        self.file_version = 4

    def __load_meta_data_v5__(self, ):
        """Similar to file_version v2 with `padiwa`, `hv`, and `daq`.

        CHANGES to v4:
        - moved '/daq/padiwa' -> '/padiwa/power'
        """
        self.__load_counts_v2__()
        self.__load_padiwa_v2__()
        self.__load_hv__()
        self.__load_daq_v2__()
        self.file_version = 5

    def __load_meta_data_v6__(self, ):
        """Similar to file_version v2 with `padiwa`, `hv`, and `daq`.
        This version has: `padiwa`, `hv`, and `daq`.

        CHANGES to v2:
        - renamed: '/daq/rate_readout' -> '/daq/frequency_readout'
        """
        self.__load_counts_v2__()
        self.__load_padiwa_v2__()
        self.__load_hv__()
        self.__load_daq_v3__()
        self.file_version = 6

    def __load_counts_v1__(self):
        self.counts_time = self.file['/rates/time']
        self.counts_ch0 = self.file['/rates/ch0']
        self.counts_ch1 = self.file['/rates/ch1']
        self.counts_ch3 = self.file['/rates/ch3']
        self.counts_ch5 = self.file['/rates/ch5']
        self.counts_ch6 = self.file['/rates/ch6']
        self.counts_ch7 = self.file['/rates/ch7']
        self.counts_ch8 = self.file['/rates/ch8']
        self.counts_ch9 = self.file['/rates/ch9']
        self.counts_ch10 = self.file['/rates/ch10']
        self.counts_ch11 = self.file['/rates/ch11']
        self.counts_ch12 = self.file['/rates/ch12']
        self.counts_ch13 = self.file['/rates/ch13']
        self.counts_ch15 = self.file['/rates/ch15']

    def __load_counts_v2__(self):
        self.counts_time = self.file['/counts/time']
        self.counts_ch0 = self.file['/counts/ch0']
        self.counts_ch1 = self.file['/counts/ch1']
        self.counts_ch3 = self.file['/counts/ch3']
        self.counts_ch5 = self.file['/counts/ch5']
        self.counts_ch6 = self.file['/counts/ch6']
        self.counts_ch7 = self.file['/counts/ch7']
        self.counts_ch8 = self.file['/counts/ch8']
        self.counts_ch9 = self.file['/counts/ch9']
        self.counts_ch10 = self.file['/counts/ch10']
        self.counts_ch11 = self.file['/counts/ch11']
        self.counts_ch12 = self.file['/counts/ch12']
        self.counts_ch13 = self.file['/counts/ch13']
        self.counts_ch15 = self.file['/counts/ch15']

    def __load_padiwa_v1__(self):
        """Old: no '/padiwa/power' in daq"""
        self.padiwa_time = self.file['/padiwa/time']
        self.padiwa_offset = self.file['/padiwa/offset']
        self.padiwa_th1 = self.file['/padiwa/th1']  # 350 nm
        self.padiwa_th2 = self.file['/padiwa/th2']  # 400 nm
        self.padiwa_th3 = self.file['/padiwa/th3']  # 425 nm
        self.padiwa_th4 = self.file['/padiwa/th4']  # 450 nm
        self.padiwa_th5 = self.file['/padiwa/th5']  # 460 nm
        self.padiwa_th6 = self.file['/padiwa/th6']  # 470 nm
        self.padiwa_th7 = self.file['/padiwa/th7']  # 480 nm
        self.padiwa_th8 = self.file['/padiwa/th8']  # 492 nm
        self.padiwa_th9 = self.file['/padiwa/th9']  # not connected
        self.padiwa_th10 = self.file['/padiwa/th10']  # not connected
        self.padiwa_th11 = self.file['/padiwa/th11']  # 510 nm
        self.padiwa_th12 = self.file['/padiwa/th12']  # 525 nm
        self.padiwa_th13 = self.file['/padiwa/th13']  # 550 nm
        self.padiwa_th14 = self.file['/padiwa/th14']  # NO FILTER
        self.padiwa_th15 = self.file['/padiwa/th15']  # not connected
        self.padiwa_th16 = self.file['/padiwa/th16']  # not connected

    def __load_padiwa_v2__(self):
        """Old: with '/padiwa/power' """
        self.padiwa_time = self.file['/padiwa/time']
        self.padiwa_offset = self.file['/padiwa/offset']  # new
        self.padiwa_power = self.file['/padiwa/power']
        self.padiwa_th1 = self.file['/padiwa/th1']  # 350 nm
        self.padiwa_th2 = self.file['/padiwa/th2']  # 400 nm
        self.padiwa_th3 = self.file['/padiwa/th3']  # 425 nm
        self.padiwa_th4 = self.file['/padiwa/th4']  # 450 nm
        self.padiwa_th5 = self.file['/padiwa/th5']  # 460 nm
        self.padiwa_th6 = self.file['/padiwa/th6']  # 470 nm
        self.padiwa_th7 = self.file['/padiwa/th7']  # 480 nm
        self.padiwa_th8 = self.file['/padiwa/th8']  # 492 nm
        self.padiwa_th9 = self.file['/padiwa/th9']  # not connected
        self.padiwa_th10 = self.file['/padiwa/th10']  # not connected
        self.padiwa_th11 = self.file['/padiwa/th11']  # 510 nm
        self.padiwa_th12 = self.file['/padiwa/th12']  # 525 nm
        self.padiwa_th13 = self.file['/padiwa/th13']  # 550 nm
        self.padiwa_th14 = self.file['/padiwa/th14']  # NO FILTER
        self.padiwa_th15 = self.file['/padiwa/th15']  # not connected
        self.padiwa_th16 = self.file['/padiwa/th16']  # not connected

    def __load_hv__(self):
        self.hv_time = self.file['/hv/time']
        self.hv_ch0 = self.file['/hv/ch0']  # 350 nm
        self.hv_ch1 = self.file['/hv/ch1']  # 400 nm, 480 nm
        self.hv_ch2 = self.file['/hv/ch2']  # 425 nm
        self.hv_ch3 = self.file['/hv/ch3']  # 450 nm, 470 nm
        self.hv_ch4 = self.file['/hv/ch4']  # 460 nm, 492 nm
        self.hv_ch5 = self.file['/hv/ch5']  # 510 nm, 550 nm
        self.hv_ch6 = self.file['/hv/ch6']  # 525 nm
        self.hv_ch7 = self.file['/hv/ch7']  # NO FILTER
        self.hv_ch8 = self.file['/hv/ch8']  # not connected
        self.hv_ch9 = self.file['/hv/ch9']  # not connected
        self.hv_ch10 = self.file['/hv/ch10']  # not connected
        self.hv_ch11 = self.file['/hv/ch11']  # not connected
        self.hv_ch12 = self.file['/hv/ch12']  # not connected
        self.hv_ch13 = self.file['/hv/ch13']  # not connected
        self.hv_ch14 = self.file['/hv/ch14']  # not connected
        self.hv_ch15 = self.file['/hv/ch15']  # not connected
        self.hv_power = self.file['/hv/power']

    def __load_daq_v1__(self):
        """Old: daq '/padiwa/power' as '/daq/padiwa' """
        self.daq_frequency_readout = self.file['/daq/rate_readout']
        self.daq_state = self.file['/daq/state']
        self.daq_time = self.file['/daq/time']
        self.daq_trb = self.file['/daq/trb']
        self.padiwa_power = self.file['/daq/padiwa']

    def __load_daq_v2__(self):
        """CHANGES to V1:
        - daq '/daq/padiwa' -> '/padiwa/power'"""
        self.daq_frequency_readout = self.file['/daq/rate_readout']
        self.daq_state = self.file['/daq/state']
        self.daq_time = self.file['/daq/time']
        self.daq_trb = self.file['/daq/trb']

    def __load_daq_v3__(self):
        """CHANGES to V1:
        - daq '/daq/rate_readout' -> '/daq/frequency_readout'"""
        self.daq_frequency_readout = self.file['/daq/frequency_readout']
        self.daq_state = self.file['/daq/state']
        self.daq_time = self.file['/daq/time']
        self.daq_trb = self.file['/daq/trb']

    # Define pandas DataFrame export helpers
    def get_pandas_daq(self):
        df = pandas.DataFrame(dict(time=self.daq_time.asdatetime()[:],
                                   daq_frequency_readout=self.daq_frequency_readout,
                                   state=self.daq_state,
                                   trb=self.daq_trb))
        df.set_index('time', drop=False, inplace=True)
        return df

    def get_pandas_padiwa(self):
        df = pandas.DataFrame(dict(time=self.padiwa_time.asdatetime()[:],
                                   th1=self.padiwa_th1,
                                   th2=self.padiwa_th2,
                                   th3=self.padiwa_th3,
                                   th4=self.padiwa_th4,
                                   th5=self.padiwa_th5,
                                   th6=self.padiwa_th6,
                                   th7=self.padiwa_th7,
                                   th8=self.padiwa_th8,
                                   th9=self.padiwa_th9,
                                   th10=self.padiwa_th10,
                                   th11=self.padiwa_th11,
                                   th12=self.padiwa_th12,
                                   th13=self.padiwa_th13,
                                   th14=self.padiwa_th14,
                                   th15=self.padiwa_th15,
                                   th16=self.padiwa_th16,
                                   offset=self.padiwa_offset,
                                   power=self.padiwa_power,
                                   ))

        df.set_index('time', drop=False, inplace=True)
        return df

    def get_pandas_hv(self):
        df = pandas.DataFrame(dict(time=self.hv_time.asdatetime()[:],
                                   ch1=self.hv_ch1,
                                   ch2=self.hv_ch2,
                                   ch3=self.hv_ch3,
                                   ch4=self.hv_ch4,
                                   ch5=self.hv_ch5,
                                   ch6=self.hv_ch6,
                                   ch7=self.hv_ch7,
                                   ch8=self.hv_ch8,
                                   ch9=self.hv_ch9,
                                   ch10=self.hv_ch10,
                                   ch11=self.hv_ch11,
                                   ch12=self.hv_ch12,
                                   ch13=self.hv_ch13,
                                   ch14=self.hv_ch14,
                                   ch15=self.hv_ch15,
                                   power=self.hv_power,
                                   ))
        df.set_index('time', drop=False, inplace=True)
        return df

    def get_pandas_counts(self):
        df = pandas.DataFrame(dict(time=self.counts_time.asdatetime()[:],
                                   ch1=self.counts_ch1,
                                   ch3=self.counts_ch3,
                                   ch5=self.counts_ch5,
                                   ch6=self.counts_ch6,
                                   ch7=self.counts_ch7,
                                   ch8=self.counts_ch8,
                                   ch9=self.counts_ch9,
                                   ch10=self.counts_ch10,
                                   ch11=self.counts_ch11,
                                   ch12=self.counts_ch12,
                                   ch13=self.counts_ch13,
                                   ch15=self.counts_ch15,
                                   ))
        df.set_index('time', drop=False, inplace=True)
        return df

    # ---- OLD CODE ----
    # def load_from_file(self, read_until_index=None):
    #     """Load data from file. Loads: self.rate_readout, self.counts_raw, self.channel_id
    #     PARAMETER
    #     ---------
    #     read_until_index: int, optional
    #         Loads only the first items until read_until_index; None (default) loads all
    #     """
    #     if read_until_index is not None:
    #         read_until_index = int(read_until_index)
    #
    #     data_dict = {}  # key= channel_id; value= counts
    #
    #     with tables.open_file(self.filename) as f:
    #         # shouldn't change -> select the first value
    #         try:  # old file
    #             self.rate_readout = f.get_node('/daq/rate_readout')[-1]
    #         except:
    #             self.rate_readout = f.get_node('/daq/frequency_readout')[-1]
    #
    #         for i in f.get_node('/counts'):
    #             if i.name == 'time':
    #                 self.time_read = f.get_node(i)[:read_until_index]
    #
    #             else:
    #                 data_dict[int(i.name.replace('ch', ''))] = f.get_node(i)[:read_until_index]
    #
    #     # data to 2d numpy array
    #     channel_id = np.array(list(data_dict.keys()))
    #     self.counts_raw = np.array(list(data_dict.values()), dtype=np.int32)
    #
    #     # sort data by channel name; ch0, ch1,...
    #     self.counts_raw = self.counts_raw[np.argsort(channel_id)]
    #     self.channel_id = channel_id[np.argsort(channel_id)]
    #
    # def calibrate_time(self, offset):
    #     """offset: int
    #         Offset in seconds"""
    #     self.time_read += offset
    #
    # def solve_leading_invalid_data(self, ):
    #     counts = np.copy(self.counts_raw)
    #
    #     # sometime the TRB shows at the beginning 0 with single values !=0
    #     # e.g. [0,0,0,4382,0] -> diff [-4382] -> +2 ** 31
    #     # solution, get single values surrounded by 0 also to 0 and replace this values with the first real counter
    #     mask_0 = counts == 0
    #     mask_0_sur = ~mask_0[:, 1:-1] & mask_0[:, :-2] & mask_0[:, 2:]
    #     counts[:, 1:-1][mask_0_sur] = 0
    #
    #     # detect the positions in each channel where the 0-series ends
    #     index_leading_0 = []
    #     for i, counts_i in enumerate(counts):
    #         if counts_i[0] == 0:
    #             index_leading_0.append(np.argwhere(np.diff(counts[i], axis=-1)).flatten()[0] + 1)
    #
    #     # delete those leading elements
    #     if len(index_leading_0) > 0:
    #         print(np.unique(index_leading_0))
    #         self.counts_raw = self.counts_raw[:, np.max(index_leading_0):]
    #         self.time_read = self.time_read[np.max(index_leading_0):]
    #
    # def solve_unsorted_in_time(self, ):
    #     """ This happened at some versions of the SDAQJob. Should be fixed."""
    #     if np.any(np.diff(self.time_read) < 0):
    #         print("The entries are not sorted in time, fix it here")
    #         index_sort = np.argsort(self.time_read)
    #         self.counts_raw = self.counts_raw[:, index_sort]
    #         self.time_read = self.time_read[index_sort]
    #
    # def get_datetime64(self, precision='us'):
    #     unit_dict = {'Y': 0, 'M': 0, 'D': 0, 'h': 0, 'm': 0, 's': 0, 'ms': -3, 'us': -6, 'ns': -6, 'as': -9}
    #     if precision in unit_dict:
    #         return (self.time_read / 10 ** unit_dict[precision]).astype(f'datetime64[{precision}]')
    #     else:
    #         raise KeyError(f' precision:{precision} not in {unit_dict.keys()}')
