# Author: Kilian Holzapfel <kilian.holzapfel@tum.de>
import pandas

from strawb.base_file_handler import BaseFileHandler


class FileHandler(BaseFileHandler):
    def __init__(self, *args, **kwargs):
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
        self.padiwa_th1 = None
        self.padiwa_th3 = None
        self.padiwa_th5 = None
        self.padiwa_th6 = None
        self.padiwa_th7 = None
        self.padiwa_th8 = None
        self.padiwa_th9 = None
        self.padiwa_th10 = None
        self.padiwa_th11 = None
        self.padiwa_th12 = None
        self.padiwa_th13 = None
        self.padiwa_th15 = None
        self.padiwa_offset = None
        self.padiwa_power = None

        self.channel_id = None
        self.counts_raw = None

        # HV-PMT Settings
        self.hv_time = None
        self.hv_ch1 = None
        self.hv_ch3 = None
        self.hv_ch5 = None
        self.hv_ch6 = None
        self.hv_ch7 = None
        self.hv_ch8 = None
        self.hv_ch9 = None
        self.hv_ch10 = None
        self.hv_ch11 = None
        self.hv_ch12 = None
        self.hv_ch13 = None
        self.hv_ch15 = None
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
        for i in [self.__load_meta_data_v2__]:
            try:
                i()  # try file versions
                return
            # version is detected because datasets in the hdf5 aren't present -> i() fails with KeyError
            except (KeyError, TypeError) as a:
                pass

        self.__load_meta_data_v1__()  # try with file default version

    def __load_meta_data_v1__(self, ):
        self.__load_counts__()
        self.__load_padiwa__()
        self.__load_hv__()
        self.__load_daq_v1__()
        self.file_version = 1

    def __load_meta_data_v2__(self, ):
        """
        CHANGES to v1:
        renamed: '/daq/rate_readout' -> '/daq/frequency_readout'
        """
        self.__load_counts__()
        self.__load_padiwa__()
        self.__load_hv__()
        self.__load_daq_v2__()
        self.file_version = 2

    def __load_counts__(self):
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

    def __load_padiwa__(self):
        self.padiwa_time = self.file['/padiwa/time']
        self.padiwa_th1 = self.file['/padiwa/th1']
        self.padiwa_th3 = self.file['/padiwa/th3']
        self.padiwa_th5 = self.file['/padiwa/th5']
        self.padiwa_th6 = self.file['/padiwa/th6']
        self.padiwa_th7 = self.file['/padiwa/th7']
        self.padiwa_th8 = self.file['/padiwa/th8']
        self.padiwa_th9 = self.file['/padiwa/th9']
        self.padiwa_th10 = self.file['/padiwa/th10']
        self.padiwa_th11 = self.file['/padiwa/th11']
        self.padiwa_th12 = self.file['/padiwa/th12']
        self.padiwa_th13 = self.file['/padiwa/th13']
        self.padiwa_th15 = self.file['/padiwa/th15']
        self.padiwa_offset = self.file['/padiwa/offset']
        self.padiwa_power = self.file['/padiwa/power']

    def __load_hv__(self):
        self.hv_time = self.file['/hv/time']
        self.hv_ch1 = self.file['/hv/ch1']
        self.hv_ch3 = self.file['/hv/ch3']
        self.hv_ch5 = self.file['/hv/ch5']
        self.hv_ch6 = self.file['/hv/ch6']
        self.hv_ch7 = self.file['/hv/ch7']
        self.hv_ch8 = self.file['/hv/ch8']
        self.hv_ch9 = self.file['/hv/ch9']
        self.hv_ch10 = self.file['/hv/ch10']
        self.hv_ch11 = self.file['/hv/ch11']
        self.hv_ch12 = self.file['/hv/ch12']
        self.hv_ch13 = self.file['/hv/ch13']
        self.hv_ch15 = self.file['/hv/ch15']
        self.hv_power = self.file['/hv/power']

    def __load_daq_v2__(self):
        self.daq_frequency_readout = self.file['/daq/frequency_readout']
        self.daq_state = self.file['/daq/state']
        self.daq_time = self.file['/daq/time']
        self.daq_trb = self.file['/daq/trb']

    def __load_daq_v1__(self):
        self.daq_frequency_readout = self.file['/daq/rate_readout']
        self.daq_state = self.file['/daq/state']
        self.daq_time = self.file['/daq/time']
        self.daq_trb = self.file['/daq/trb']

    # Define pandas DataFrame export helpers
    def get_pandas_daq(self):
        return pandas.DataFrame(dict(time=self.daq_time.asdatetime()[:],
                                     daq_frequency_readout=self.daq_frequency_readout,
                                     state=self.daq_state,
                                     trb=self.daq_trb))

    def get_pandas_padiwa(self):
        return pandas.DataFrame(dict(time=self.padiwa_time.asdatetime()[:],
                                     th1=self.padiwa_th1,
                                     th3=self.padiwa_th3,
                                     th5=self.padiwa_th5,
                                     th6=self.padiwa_th6,
                                     th7=self.padiwa_th7,
                                     th8=self.padiwa_th8,
                                     th9=self.padiwa_th9,
                                     th10=self.padiwa_th10,
                                     th11=self.padiwa_th11,
                                     th12=self.padiwa_th12,
                                     th13=self.padiwa_th13,
                                     th15=self.padiwa_th15,
                                     offset=self.padiwa_offset,
                                     power=self.padiwa_power,
                                     ))

    def get_pandas_hv(self):
        return pandas.DataFrame(dict(time=self.hv_time.asdatetime()[:],
                                     ch1=self.hv_ch1,
                                     ch3=self.hv_ch3,
                                     ch5=self.hv_ch5,
                                     ch6=self.hv_ch6,
                                     ch7=self.hv_ch7,
                                     ch8=self.hv_ch8,
                                     ch9=self.hv_ch9,
                                     ch10=self.hv_ch10,
                                     ch11=self.hv_ch11,
                                     ch12=self.hv_ch12,
                                     ch13=self.hv_ch13,
                                     ch15=self.hv_ch15,
                                     power=self.hv_power,
                                     ))

    def get_pandas_counts(self):
        return pandas.DataFrame(dict(time=self.counts_time.asdatetime()[:],
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
