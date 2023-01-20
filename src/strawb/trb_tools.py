import os

import h5py
import numpy as np
import scipy.stats

from strawb import tools


class TRBTools:
    def __init__(self, file_handler=None, frequency_interp=33.):
        """Base Class for the TRB. It takes care about the counter readings and calculates the rates based on the
        counts. In addition, it can also calculate an interpolated rate based on the counts. To open and close a file
        can cause corrupt links. Therefore, the following properties must be set in the child class which inherits from
        TRBTools, and they should set the link to the data source:
        - raw_counts_arr; __daq_frequency_readout__; __time__

        PARAMETER
        ---------
        frequency_interp: float or int
            sets the default frequency for the rates' interpolation. Is only set, if there is no frequency_interp in
            the file set. To overwrite, set frequency_interp (i.e. `frequency_interp=24`) after the initialisation.
        """
        self.__dcounts_arr__ = None  # stores result of self.diff_counts()
        self.__counts_arr__ = None  # stores 'absolute' counts as a 2D array,
        self._active_read_arr_ = None  # stores if the counter read happens at an event (1) or not (0)
        self._rate_delta_time = None
        self._rate = None  # stores result of self.calculate_rates() (needs `self._dcounts_arr_`)

        # in some version of the SDAQ there was a bug which leads to a corrupt start of n indexes.
        # where n is the length of the SDAQ buffer
        self._index_start_valid_data_ = None

        # interpolated rates. Based on the `counts` and interpolated to fit an artificial readout frequency.
        self._interp_frequency_ = None  # artificially readout frequency
        self._interp_time_ = None  # absolute timestamps. Shape: [time_j]
        self._interp_rate_ = None  # rate as a 2d array. Shape: [channel_i, time_j]
        self._interp_active_ratio_ = None  # rate as a 2d array. Shape: [channel_i, time_j]

        # link to file_handler
        self.file_handler = file_handler
        if file_handler is not None:
            try:
                self.__load_interp_rate__()
            except KeyError:
                pass

        # if the frequency is not loaded from the file, set default frequency
        if self._interp_frequency_ is None:
            self._interp_frequency_ = frequency_interp

    def __del__(self):
        self.file_handler = None  # unlink
        del self.__dcounts_arr__
        del self.__counts_arr__
        del self._active_read_arr_
        del self._rate_delta_time
        del self._rate

    # ---- MANDATORY properties ----
    # define interfaces which need to be set in child classes, i.e. to link file handler variables
    # raw_counts_arr are the counter arrays where raw_counts_arr[0] must be the time counter of the TRB aka
    # ch0.
    # Each array (counts_ch0, counts_ch1,...) must be from the same length and must have the same length as
    # self.__time__.
    # e.g.: self.raw_counts_arr: return [file_handler.counts_ch0, file_handler.counts_ch1, file_handler.counts_ch2]
    # __daq_frequency_readout__ is the frequency TRB counts up the time counter (ch0)
    @property
    def __time__(self):
        return None  # array with absolute time stamps, needs to be set in the child class

    @property
    def __daq_frequency_readout__(self):
        """Array or float of the TRB daq frequency, needs to be set in the child class"""
        return None

    @property
    def raw_counts_arr(self):
        """List of arrays of raw counts, needs to be set in the child class. raw_counts_arr[0] must be the time
        counter of the TRB aka ch0."""
        return None

    # ---- END MANDATORY properties ----

    # Properties prevent here to load data directly at initialisation and to prevent setting the variables
    @property
    def _time_(self):
        """The absolute timestamp in seconds since epoch when the counter are recorded. This time isn't very
        precise as it comes from the CPU clock, therefore its absolute. See `rate_time` for a very precise but
        not absolute timestamps from the TRB."""
        if self.__time__ is None:
            return None

        return self.__time__[self.index_start_valid_data:]

    @property
    def time(self):
        """The absolute timestamp as datetime when the counter are recorded. This time isn't very
        precise as it comes from the CPU clock, therefore its absolute. See `rate_time` for a very precise but
        not absolute timestamps from the TRB."""
        if self.__time__ is None:
            return

        # if isinstance(self.__time__, h5py.Dataset):
        #     # noinspection PyUnresolvedReferences
        #     return self.__time__.asdatetime()[self.index_start_valid_data:]
        # else:
        return tools.asdatetime(self._time_)

    @property
    def index_start_valid_data(self):
        """ Workaround for a bug in SDAQ, which writes at initialisation the buffer size to the file.
        This means, the first n (=buffer size) entries are corrupt, which can be detected by sorting the time
        """
        if self.__time__ is None:
            return None
        elif self._index_start_valid_data_ is None:
            # noinspection PyTypeChecker
            sort_args = np.argsort(self.__time__)
            unordered_indexes = np.argwhere(np.diff(sort_args) != 1).flatten()
            if len(unordered_indexes) != 0:
                self._index_start_valid_data_ = unordered_indexes[-1] + 1
            else:
                self._index_start_valid_data_ = 0
        return self._index_start_valid_data_

    @property
    def time_middle(self):
        """The absolute timestamp corresponding to the middle of the counter read interval. This time isn't very precise
        as it comes from the CPU clock, therefore its absolute. See `rate_time_middle` for a very precise but not
        absolute timestamps from the TRB."""
        return tools.asdatetime((self.__time__[1:] + self.__time__[:-1]) * 0.5)

    # ---- TRB Settings ----
    @property
    def daq_frequency_readout(self):
        """The frequency ([Hz]) at which counter channel 0 counts up."""
        return self.__daq_frequency_readout__

    # ---- cleaned TRB Delta Counts ----
    @property
    def _counts_arr_(self):
        if self.__counts_arr__ is None:
            self.cum_sum_dcounts()
        return self.__counts_arr__

    @property
    def _dcounts_arr_(self):
        if self.__dcounts_arr__ is None:
            self.diff_counts()
        return self.__dcounts_arr__

    @property
    def dcounts(self):
        """Returns all delta counts as a 2D array with the axes [channel_j, time_i]."""
        return self._dcounts_arr_[1:]  # [0] is dcounts_time

    @property
    def counts(self):
        """Returns all 'absolute' counts as a 2D array with the axes [channel_j, time_i+1]. The counts start at 0."""
        return self._counts_arr_[1:]

    @property
    def dcounts_time(self):
        """Channel which counts up at a constant frequency. The frequency is stored in `self.daq_frequency_readout`.
        1d-array with axes [time_i].
        """
        return self._dcounts_arr_[0]  # [1:] is dcounts

    @property
    def counts_time(self):
        """Channel which counts up at a constant frequency. The frequency is stored in `self.daq_frequency_readout`.
        1d-array with axes [time_i].
        """
        return self._counts_arr_[0]

    @property
    def time_counts(self):
        """Channel which counts up at a constant frequency. The frequency is stored in `self.daq_frequency_readout`.
        1d-array with axes [time_i].
        """
        if self.daq_frequency_readout is not None:
            # noinspection PyTypeChecker
            return self._counts_arr_[0] / float(self.daq_frequency_readout)

    # ---- TRB Rates ----
    @property
    def rate_time(self):
        """Rate time is a timestamp since the start of the measurement in seconds. It represents the times when the
        counters are read. It starts with 0. Attention: len(rate_time) = len(rate) + 1!
        The time is calculated from the TRB channel_0 counts and the counting frequency, which is usually 10 kHz, see
        self.file_handler.daq_frequency_readout. This delivers a more precise time because it is based on the raw
        delta_t when the counters are read. In contrast, the absolute time is CPU time which can have some delay.
        However, it's not an absolute timestamp.
        """
        return np.append([0], np.cumsum(self.rate_delta_time))

    @property
    def rate_time_middle(self):
        """Rate time is a timestamp since the start of the measurement in seconds. It represents the middle of the
        interval when two counters are read.
        The time is calculated from the TRB channel_0 counts and the counting frequency, which is usually 10 kHz, see
        self.file_handler.daq_frequency_readout. This delivers a more precise time because it is based on the raw
        delta_t when the counters are read. In contrast, the absolute time is CPU time which can have some delay.
        However, it's not an absolute timestamp.
        """
        return np.cumsum(self.rate_delta_time) - self.rate_delta_time * 0.5

    @property
    def rate_delta_time(self):
        """The time delta (in seconds) which corresponds to the rates. The time delta is calculated from the TRB
        channel_0 counts and the counting frequency, which is usually 10 kHz, see
        self.file_handler.daq_frequency_readout. This delivers a more precise time because it is based on the raw
        delta_t when the counters are read. In contrast, the absolute time is CPU time which can have some delay.
        However, it's not an absolute timestamp.
        """
        if self._rate_delta_time is None:
            self.calculate_rates()
        return self._rate_delta_time

    @property
    def rate(self):
        """The rate (in Hz) per channel. It is calculated from: dcounts/rate_delta_t."""
        # counts time is the middle of the interval and starts with 0
        if self._rate is None:
            self.calculate_rates()
        return self._rate

    @property
    def active_read(self):
        """A bool array which signalise, that the TRB read a counter when there was an event ongoing at this channel.
        """
        if self._active_read_arr_ is None:
            self.diff_counts()
        return self._active_read_arr_

    def cum_sum_dcounts(self):
        # self.__counts_arr__ will be set if not None, and self._dcounts_arr_ must be not None.
        if self.__counts_arr__ is None and self._dcounts_arr_ is not None:
            # prepend 0 for all channels and use uint64 for higher overflow
            counts = np.append(np.zeros((self._dcounts_arr_.shape[0], 1), dtype=np.uint64),
                               self._dcounts_arr_.astype(np.uint64),
                               axis=-1)

            # calculate the 'absolut'-counts
            self.__counts_arr__ = np.cumsum(counts, axis=1)
            return self._counts_arr_
        return None

    def diff_counts(self):
        if self.raw_counts_arr is not None:
            # noinspection PyTypeChecker
            raw_counts_arr = np.array(self.raw_counts_arr)[:, self.index_start_valid_data:]

            # noinspection PyArgumentList
            self.__dcounts_arr__, self._active_read_arr_ = self._diff_counts_(*raw_counts_arr)
            self._active_read_arr_ = self._active_read_arr_[1:]  # ch0 can't be active

            return self._dcounts_arr_
        return None

    def calculate_rates(self):
        if self.raw_counts_arr is not None:
            self._rate_delta_time, self._rate = self._calculate_rates_(
                daq_frequency_readout=self.__daq_frequency_readout__,
                dcounts_time=self.dcounts_time,
                dcounts_arr=self.dcounts,
            )
        return None

    @staticmethod
    def _diff_counts_(*args, **kwargs):
        """
        Calculates the delta counts of the raw counts readings, similar to 'np.diff' with overflow correction, and it
        takes care of the special TRB integer type. To calculate the absolute counts readings, do
        >>> counts, active_read = TRBTools._diff_counts_(*args, **kwargs)
        >>> np.cumsum(counts.astype(np.int64))

        PARAMETER
        ---------
        *args, **kwargs: ndarray, Datasets
            1d raw counts arrays with the same length. It does something like: np.array([*args, *kwargs.values()]).

        RETURNS
        -------
        counts: ndarray[int32]
            the counts as a 2d array, with the shape of np.array([*args, *kwargs.values()])
        active_read: ndarray[bool]
            the active reads of the counters as the 2d array with the same shape as `counts`
        """
        # Prepare parameter
        # Check type and shape of counts arrays
        args = list(args)
        for i in kwargs:
            args.append(kwargs[i])

        counts_arr = np.array([*args], dtype=np.int64)
        # Prepare parameter done

        # TRB use the leading bit to show if the channel is active while reading. Correct it here.
        mask_active_read = counts_arr < 0
        counts_arr[mask_active_read] += 2 ** 31  # In int32 this leads to negative values.

        # correct overflow; cal. difference, if negative=overflow, add 2 ** 31
        # prepend to start a 0 and get same shape
        counts_arr = np.diff(counts_arr)  # , prepend=counts[:, 0].reshape((-1, 1)))
        counts_arr[counts_arr < 0] += (
                2 ** 31
        )  # delta<0 when there is an overflow 2**31 (TRBint)
        return counts_arr.astype(np.int32), mask_active_read

    @staticmethod
    def _calculate_rates_(daq_frequency_readout, dcounts_time, dcounts_arr):
        """Converts the cleaned counts readings from the TRB into rates.
        PARAMETER
        ---------
        daq_frequency_readout: Union[int, float, list, np.ndarray, h5py.Dataset]
            the TRB readout frequency in Hz. If a list, np.ndarray, or h5py.Dataset is provided. Cut -1 values
            (TRB inactive) and check if the array is unique. Take the unique value or raise and RuntimeError.
        dcounts_time:
            The delta counts (s. _diff_counts_) of channel 0. The TRB counts channel 0 up with the frequency
            from daq_frequency_readout.
        dcounts_arr: Union[list, np.ndarray, h5py.Dataset], optional
            A 2d array of the counters with axes [channel_j, time_i].

        RETURN
        ------
        delta_time: np.ndarray
            the timedelta corresponding to each count. Calculated from channel 0 in seconds.
        rate_arr: np.ndarray
            the rates in Hz of the provided channels defined in args or kwargs as one ndarray.
        """
        # Prepare parameter
        # Check type and shape of counts arrays
        if isinstance(daq_frequency_readout, list):  # convert to array
            daq_frequency_readout = np.array(daq_frequency_readout)
        if isinstance(daq_frequency_readout, h5py.Dataset):
            daq_frequency_readout = daq_frequency_readout[:]  # need [:] here
        if isinstance(daq_frequency_readout, np.ndarray):
            # check if there is only one value (exclude -1: daq inactive)
            if np.unique(
                    daq_frequency_readout[daq_frequency_readout != -1]
            ).shape == (0,):
                daq_frequency_readout = 10000  # the default frequency
            elif np.unique(
                    daq_frequency_readout[daq_frequency_readout != -1]
            ).shape != (1,):
                raise RuntimeError(
                    "More than 1 unique value exits in daq_frequency_readout."
                )
            else:
                # if the daq_frequency_readout failed reading from the TRB it logs -1, correct here
                daq_frequency_readout = daq_frequency_readout[
                    daq_frequency_readout[:] != -1
                    ][0]

        daq_frequency_readout = float(daq_frequency_readout)  # must be a float
        dcounts_arr = np.array(dcounts_arr, dtype=float)  # must be of int64

        # Calculate Rates
        delta_time = dcounts_time.astype(float) / daq_frequency_readout  # seconds
        rate_arr = dcounts_arr.astype(float) / delta_time

        return delta_time, rate_arr

    # interpolated rates
    @property
    def interp_frequency(self):
        return self._interp_frequency_

    @interp_frequency.setter
    def interp_frequency(self, value):
        """Sets the frequency for the interpolation in Hz."""
        if not isinstance(value, (int, float)):
            raise TypeError(f'frequency_interp must a int or float. Got {type(value)}')
        # set it and calculate the new rates
        if self._interp_frequency_ != value:
            self._interp_time_, self._interp_rate_, self._interp_active_ratio_ \
                = self.interpolate_rate(value)
            self._interp_frequency_ = value

    @property
    def interp_time(self):
        """The time array for the interpolated rates as np.ma.array(). shape: [time_i]
        The masked entries are period, where no counts are stored/available."""
        if self._interp_time_ is None:
            self._interp_time_, self._interp_rate_, self._interp_active_ratio_ \
                = self.interpolate_rate(self._interp_frequency_)
        return self._interp_time_

    @property
    def interp_rate(self):
        """The rate array for the interpolated rates as np.ma.array(). shape: [channel_i, interp_time.shape]
        The masked entries are period, where no counts are stored/available."""
        if self._interp_rate_ is None:
            self._interp_time_, self._interp_rate_, self._interp_active_ratio_ \
                = self.interpolate_rate(self._interp_frequency_)
        return self._interp_rate_

    @property
    def interp_active_ratio(self):
        """The active read ratio array for the interpolated rates. shape: [channel_i, interp_time.shape].
        The TRB counter, signalise if a counter was read in active mode. This array gives, the ratio of counter reads,
        which have been active.
        The masked entries are period, where no counts are stored/available."""
        if self._interp_active_ratio_ is None:
            self._interp_time_, self._interp_rate_, self._interp_active_ratio_ \
                = self.interpolate_rate(self._interp_frequency_)
        return self._interp_active_ratio_

    def interpolate_rate(self, frequency=333., time_probe=None):
        """Interpolates the rate and timestamps to a given 'readout' frequency. It is based on the raw counts from TRB.
        The process is the following. It interpolates the cumulative counts and calculates the rate based on it.
        PARAMETER
        ---------
        frequency: float, optional
            the frequency to which the data is interpolated in Hz. Default is 333 Hz. `time_probe` must be None.
        time_probe: ndarray, optional
            the timestamps in seconds since the file start and at which the counts should be interpolated to calculate
            the rates. For absolute timestamps subtract: strawb.tools.datetime2float(pmt.trb_rates.time)[0].
        RETURN
        ------
        time_inter: ndarray
            the interpolated absolute timestamp in seconds since the epoch. It corresponds to the middle of time_probe.
            Therefore, len(time_probe) -1 == len(time_inter)
        rate_inter: ndarray
            the interpolated rate as a 2d array with shape [channel_i, rate_j] and len(rate_j) == len(time_inter).
        active: ndarray
            active read ratio. For how many reads, the TRB read during the signal was active (stored as an extra bit
            in the raw data). Active is 'np.nan' when there is no data (counter read) in the interval
        """
        def interp_np(x, xp, fp):
            y = np.zeros((fp.shape[0], x.shape[0]), dtype=float)
            for i in range(y.shape[0]):
                y[i] = np.interp(x, xp, fp[i])
            return y

        timestamps = self.rate_time  # seconds since file started
        if time_probe is None:
            if timestamps[-1] - timestamps[0] > 0:
                # if counters are not growing over the time
                time_probe = np.arange(timestamps[0], timestamps[-1], 1./frequency)
            else:
                # use the CPU time when the counters are read with the pearl script
                time_probe = np.arange(self._time_[0] - self._time_[0],
                                       self._time_[-1] - self._time_[0],
                                       1./frequency)
        # check if there are entries in time_probe
        if len(time_probe) == 0:
            raise ValueError('File has corrupt time data in `file_handler.counts_ch0` and `file_handler.counts_time`.')

        active, b, n = scipy.stats.binned_statistic(timestamps,
                                                    self.active_read,
                                                    statistic='sum',
                                                    bins=time_probe)

        reads, b, n = scipy.stats.binned_statistic(timestamps,
                                                   None,
                                                   statistic='count',
                                                   bins=time_probe)
        # transform active to active read ratio, active is np.nan when there is no data (counter read) in the interval
        mask = reads != 0
        active = active.astype(float)
        active[:, mask] = active[:, mask] / reads[mask]
        active[:, ~mask] = np.nan

        counts = interp_np(x=time_probe, xp=timestamps, fp=self.counts.astype(float))

        abs_time = np.interp(x=time_probe,
                             xp=timestamps,
                             fp=self.time.astype(float),  # np.interp works only with float, int
                             ).astype(self.time.dtype)

        rate_inter = np.diff(counts) / np.diff(time_probe)
        time_inter = abs_time[:-1] + np.diff(abs_time) * .5

        # mask the arrays, keep in mind: active and rate_inter are 2D-arrays and time_inter is 1D
        active = np.ma.masked_invalid(active)  #
        rate_inter = np.ma.array(rate_inter, mask=active.mask)
        time_inter = np.ma.array(time_inter, mask=~mask)
        return time_inter, rate_inter, active

    def __load_interp_rate__(self):
        """Moved to InterpolatedRatesFile"""
        group = self.file_handler.file['rates_interpolated']
        self._interp_frequency_ = group.attrs['interpolated_frequency']

        self._interp_time_ = group['time']
        if 'mask' in group:
            self._interp_mask_ = group['mask']
        self._interp_rate_ = np.array(group['rate'])

    def write_interp_rate(self, force_write=False, compression_dict=None):
        """Moved to InterpolatedRatesFile
        Write the interpolated rates and time to the file.
        PARAMETER
        ---------
        force_write: bool, optional
            if existing data with the same frequency should be overwritten.
        compression_dict: dict, optional
            parameters parsed to h5py.create_dataset. 'None' (default) use:
            compression_dict = {'compression': 'gzip', 'compression_opts': 9, 'shuffle': True, 'fletcher32': True}
        """
        if self.file_handler is None:
            return

        if compression_dict is None:
            compression_dict = {'compression': 'gzip', 'compression_opts': 9, 'shuffle': True, 'fletcher32': True}

        # close file as open in read mode and open it with 'r+'
        try:
            self.file_handler.close()
            self.file_handler.open(mode='r+')  # r+ : Read/write, file must exist

            # write data to file, first check if data have to be updated or written
            group = self.file_handler.file.require_group('counts_interpolated')
            if 'interpolated_frequency' in group.attrs and not force_write:
                if group.attrs['interpolated_frequency'] == self.interp_frequency:
                    return  # don't write the data again

            # write data
            if 'time' in group:
                del group['time']
            group.create_dataset('time', data=tools.datetime2float(self.interp_time), **compression_dict)

            if 'rate' in group:
                del group['rate']
            group.create_dataset('rate', data=self.interp_rate, **compression_dict)
            group.attrs.update({'interpolated_frequency': self.interp_frequency})
        finally:
            self.file_handler.close()  # close write mode
            self.file_handler.open()  # open in read only mode

    def remove_interp_rate(self, ):
        """Moved to InterpolatedRatesFile"""
        if self.file_handler is None:
            return

        try:
            # close file as open in read mode and open it with 'r+'
            self.file_handler.close()
            self.file_handler.open(mode='r+', load_data=False)  # r+ : Read/write, file must exist

            if 'counts_interpolated' in self.file_handler.file:
                del self.file_handler.file['/counts_interpolated']

        finally:
            self.file_handler.close()  # close write mode
            self.file_handler.open()  # open in read only mode


class InterpolatedRatesFile:
    def __init__(self, file_name, read_data=True):
        """Loads or write the interpolated rate data to a hdf5 file. Interpolated rates are processed rates in order
        to transform the raw rates with unequal readout frequency to a fixed artificial readout frequency by
        interpolation. To handle periods where no raw rates are available, the interpolated rates come with a mask
        that flags the artificial readout intervals where no raw rates are recorded. Consequently, interpolated
        rates intervals are not masked when at least one raw rate is recorded.

        EXAMPLE
        -------
        Legend: artificial intervals: '|', interpolated rater: 'i', raw rates data: 'x'
        Time         : ->
        RAW          : | x    | x    |  x  x|  x   |   x  |      |x x  x|  x   | x  x |  x x | x    |   x  |
        Interpolated : |  i   |  i   |  i   |  i   |  i   |  i   |  i   |  i   |  i   |  i   |  i   |  i   |
        mask         : |  0   |  0   |  0   |  0   |  0   |  1   |  0   |  0   |  0   |  0   |  0   |  0   |
        """

        self.file_name = os.path.abspath(file_name)

        self.__time__ = None
        self.__rate__ = None
        self.__mask__ = None

        self.file_start = None
        self.file_end = None

        self._t_probe_, self._active_ = None, None

        if read_data and os.path.exists(self.file_name):
            self.read()
        elif read_data and not os.path.exists(self.file_name):
            print(f"WARNING: file doesn't exist {self.file_name}")

    @property
    def time(self):
        """Interpolated (artificial) readout time of the rates.
        RETURN
        ------
        time: np.ma.ndarray
            time in seconds with fixed frequency. Periods where no RAW rates are available, are masked.
            However, the time is still available for these periods with `time.data`.
        """
        if self.__time__ is None:
            self.read()
        if self.__mask__ is None:
            self.read()
            return np.ma.array(self.__time__)
        else:
            return np.ma.array(self.__time__, mask=self.self.__mask__)

    @property
    def rate(self):
        """Interpolated (artificial) readout rates.
        RETURN
        ------
        mask: np.ndarray
            interpolated rate in Hz as a 2D array with the shape : [channel_i, time_i]. Periods where no RAW rates are
            available, are masked. However, the interpolated is still available for these periods with `rate.data`.
        """
        if self.__rate__ is None:
            self.read()
        if self.mask is None:
            return np.ma.array(self.__rate__)
        else:
            return np.ma.array(self.__rate__, mask=np.ones_like(self.__rate__, dtype=bool) * self.__mask__)

    @property
    def mask(self):
        """Interpolated (artificial) readout mask. A flag for period where no RAW data is recorded.
        RETURN
        ------
        maks: np.ndarray
            interpolated rate in Hz. Periods where no RAW rates are available, are True (np.ma.array logic)
        """
        if self.__time__ is None:  # check if file is loaded
            self.read()  # read sets __time__
        return self.__mask__

    def _write_to_file_(self, interp_time, interp_rate, interp_mask, file_attrs=None, group_attrs=None):
        """Write interpolated data of PMT to the file. It generates a hdf5 file and adds the data as follows:
        group: /rates_interpolated
        data_Set: /rates_interpolated/rate - with shape [channels, time]
                  /rates_interpolated/time - with shape time
                  /rates_interpolated/mask - with shape time
        If a dataset exists, it adds the data to the dataset.

        PARAMETER
        ---------
        interp_time: ndarray
        interp_rate: ndarray
        interp_mask: ndarray
        file_attrs: dict, optional
            hdf5 file attributes
        group_attrs: dict, optional
            hdf5 group attributes
        """
        if group_attrs is None:
            group_attrs = {}
        if file_attrs is None:
            file_attrs = {}

        h5py_dataset_options = {'compression': 'gzip',
                                'compression_opts': 6,
                                'shuffle': True,
                                'fletcher32': True,
                                'chunks': (2, 2 ** 13)}

        with h5py.File(self.file_name, 'a') as f:  # libver='latest'
            for i in set(file_attrs).difference(f.attrs):
                f.attrs.update({i: file_attrs[i]})

            group = f.require_group('rates_interpolated')
            for i in set(group_attrs).difference(group.attrs):
                group.attrs.update({i: group_attrs[i]})

            tools.append_hdf5(f, '/rates_interpolated/rate',
                              data=interp_rate,
                              axis=1,
                              **h5py_dataset_options)

            h5py_opt_1d = h5py_dataset_options.copy()
            if 'chunks' in h5py_opt_1d:
                h5py_opt_1d['chunks'] = (h5py_opt_1d['chunks'][1],)

            tools.append_hdf5(f, '/rates_interpolated/time',
                              data=tools.datetime2float(interp_time),
                              **h5py_opt_1d)

            tools.append_hdf5(f, '/rates_interpolated/mask',
                              data=interp_mask,
                              **h5py_opt_1d)

    def write_to_file(self, trb_tools, file_attrs=None, group_attrs=None):
        """Write interpolated data of PMT to the file. It generates a hdf5 file and adds the data as follows:
        group: /rates_interpolated
        data_Set: /rates_interpolated/rate - with shape [channels, time]
                  /rates_interpolated/time - with shape time
                  /rates_interpolated/mask - with shape time
        If a dataset exists, it adds the data to the dataset.

        PARAMETER
        ---------
        trb_tools: strawb.trb_tools.TRBTools
            class which holds the TRB Data and process code. To change the interpolation frequency,
            do it before you execute this function.
        file_attrs: dict, optional
            hdf5 file attributes
        group_attrs: dict, optional
            hdf5 group attributes
        """
        self._write_to_file_(interp_time=trb_tools.interp_time.data,
                             interp_rate=trb_tools.interp_rate.data,
                             interp_mask=trb_tools.interp_time.mask,
                             file_attrs=file_attrs,
                             group_attrs=group_attrs)

    def read(self, ):
        """ Reads the file. """
        with h5py.File(self.file_name, 'r') as f:
            if '/rates_interpolated/mask' in f:
                self.__mask__ = f['/rates_interpolated/mask'][:]

            self.__time__ = f['/rates_interpolated/time'][:]
            self.__rate__ = np.array(f['/rates_interpolated/rate'][:])

            self.file_start = f.attrs['file_start']
            self.file_end = f.attrs['file_end']

    def get_active(self, step_size=3600, **kwargs):
        bins = np.arange(self.file_start, self.file_end + step_size, step_size)
        self._t_probe_, self._active_ = self._get_active_(self.time, bins=bins, **kwargs)

    @property
    def t_probe(self):
        if self._t_probe_ is None:
            self.get_active()
        return self._t_probe_

    @property
    def t_probe_middle(self):
        return .5 * (self.t_probe[:-1] + self.t_probe[1:])

    @property
    def active(self):
        if self._active_ is None:
            self.get_active()
        return self._active_

    @staticmethod
    def _get_active_(t, bins=None, step_size=None, max_delta_t=1.5):
        """Calculate the active (up-time) time of the measurement within the periods (bins). If the time between two
        measurements is greater as the `max_delta_t`, the period is counted as inactive.
        PARAMETER
        t: ndarray
            timestamps of the measurements in seconds.
        bins: float, int, list, ndarray
            sets the bins within the active ratio is calculated, directly.
        step_size:
            sets the bins with 'np.arange(t[0], t[-1] + step_size, step_size)' within the active ratio is calculated.
            bins must be None otherwise step_size is ignored.
        max_delta_t:
            the maximum between two measurements to be counted as active time. If the time between two measurements is
            greater as the `max_delta_t`, the period is counted as inactive.
        """
        t_mask = ~t.mask
        t = t.data

        if isinstance(bins, (int, float)):
            t_probe = np.linspace(t[0], t[-1], bins)
        elif isinstance(bins, (list, np.ndarray)):
            t_probe = bins
        elif isinstance(step_size, (int, float)):
            # add one step to the end. <-> .5*(t_probe[:-1]+t_probe[1:])
            t_probe = np.arange(t[0], t[-1] + step_size, step_size)
        else:
            raise ValueError('Either bins must be [int, float, list, ndarray] or steps [int, float].')

        active = np.zeros_like(t_probe[1:])

        # remove invalid entries
        t = t[t_mask]

        if t.shape[0] == 0:
            return .5 * (t_probe[:-1] + t_probe[1:]), active

        # calculate the total elapsed time
        delta_t = np.diff(t)
        tot = np.interp(t_probe, t, np.append([0], np.cumsum(delta_t)))

        # calculate the total elapsed time when the readout frequency is under 1./max_delta_t
        delta_t[delta_t > max_delta_t] = 0
        t_a = np.interp(t_probe, t, np.append([0], np.cumsum(delta_t)))

        mask_nan = np.diff(tot) == 0
        active[mask_nan] = np.nan
        active[~mask_nan] = np.diff(t_a)[~mask_nan] / np.diff(tot)[~mask_nan]
        return t_probe, active
