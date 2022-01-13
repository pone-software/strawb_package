import h5py
import numpy as np

from strawb import tools


class TRBTools:
    def __init__(self):
        # define interfaces which need to be set in child classes, i.e. to link file handler variables
        # __counts_arr__ are the counter arrays where __counts_arr__[0] must be the time counter of the TRB aka ch0.
        # Each array (counts_ch0, counts_ch1,...) must be from the same length and must have the same length as
        # self.__time__.
        # e.g.: self.__counts_arr__ = [file_handler.counts_ch0, file_handler.counts_ch1, file_handler.counts_ch2]
        # __daq_frequency_readout__ is the frequency TRB counts up the time counter (ch0)
        self.__counts_arr__ = None  # list, needs to be set in the child class
        self.__daq_frequency_readout__ = (
            None  # array or float, needs to be set in the child class
        )
        self.__time__ = None  # array with absolute time stamps

        self._dcounts_arr_ = None  # stores result of self.diff_counts()
        self._rate_delta_time = None
        self._rate = None  # stores result of self.calculate_counts() (needs `self._dcounts_arr_`)

    # Properties prevent here to load data directly at initialisation and to prevent setting the variables
    # ---- absolute Measurement Timestamp ----
    @property
    def time(self):
        """The absolute timestamp when the counter are recorded. This time isn't very precise as it comes from the CPU
        clock, therefore its absolute. See `rate_time` for a very precise but not absolute timestamps from the TRB."""
        return self.__time__.asdatetime()[:]

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
    def dcounts(self):
        """Returns all delta counts as a 2D array with the axes [channel_j, time_i]. dcounts[0] is the time channel
        aka. dcounts_time."""
        if self._dcounts_arr_ is None:
            self.diff_counts()
        return self._dcounts_arr_[1:]  # [0] is dcounts_time

    @property
    def dcounts_time(self):
        """Channel which counts up at a constant frequency. The frequency is stored in `self.daq_frequency_readout`.
        1darray with axes [time_i].
        """
        if self._dcounts_arr_ is None:
            self.diff_counts()
        return self._dcounts_arr_[0]  # [1:] is dcounts

    # ---- TRB Rates ----
    @property
    def rate_time(self):
        """Rate time is a timestamp since the start of the measurement in seconds. It represents the times when the
        counters are read. It starts with 0. Attention: len(rate_time) = len(rate) + 1!"""
        return np.append([0], np.cumsum(self.rate_delta_time))

    @property
    def rate_time_middle(self):
        """Rate time is a timestamp since the start of the measurement in seconds. It represents the middle of the
        interval when two counters are read."""
        return np.cumsum(self.rate_delta_time) - self.rate_delta_time * 0.5

    @property
    def rate_delta_time(self):
        """The time delta (in seconds) which corresponds to the rates. The time delta is calculated from the TRB
        channel_0 counts and the counting frequency, which is usually 10 kHz, see
        self.file_handler.daq_frequency_readout. This delivers a more precise time because it is based on the raw
        delta_t from the TRB and its more than the np.datetime64 can deliver. However, it's not an absolute timestamp.
        """
        if self._rate_delta_time is None:
            self.calculate_counts()
        return self._rate_delta_time

    @property
    def rate(self):
        """The rate (in Hz) per channel. It is calculated from: dcounts/rate_delta_t."""
        # counts time is the middle of the interval and starts with 0
        if self._rate is None:
            self.calculate_counts()
        return self._rate

    def diff_counts(self):
        if self.__counts_arr__ is not None:
            self._dcounts_arr_ = self._diff_counts_(*self.__counts_arr__)
            return self._dcounts_arr_
        return None

    def calculate_counts(self):
        if self.__counts_arr__ is not None:
            self._rate_delta_time, self._rate = self._calculate_rates_(
                daq_frequency_readout=self.__daq_frequency_readout__,
                dcounts_time=self.dcounts_time,
                dcounts_arr=self.dcounts,
            )
        return None

    @staticmethod
    def _diff_counts_(*args, **kwargs):
        """
        Calculates the delta counts of the raw counts readings, similar to np.diff with overflow correction and it
        takes care of the special TRB integer type. To calculate the absolute counts readings, do
        >>> counts = TRBTools._diff_counts_(*args, **kwargs)
        >>> np.cumsum(counts.astype(np.int64))

        PARAMETER
        ---------
        *args, **kwargs: ndarray, Datasets
            1d raw counts arrays with the same length
        """
        # Prepare parameter
        # Check type and shape of counts arrays
        args = list(args)
        for i in kwargs:
            args.append(kwargs[i])

        counts_arr = np.array([*args], dtype=np.int64)
        # Prepare parameter done

        # TRB use the leading bit to show if the channel is active while reading. Correct it here.
        counts_arr[counts_arr < 0] += 2 ** 31  # In int32 this leads to negative values.

        # correct overflow; cal. difference, if negative=overflow, add 2 ** 31
        # prepend to start a 0 and get same shape
        counts_arr = np.diff(counts_arr)  # , prepend=counts[:, 0].reshape((-1, 1)))
        counts_arr[counts_arr < 0] += (
            2 ** 31
        )  # delta<0 when there is an overflow 2**31 (TRBint)
        return counts_arr.astype(np.int32)

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
        if isinstance(daq_frequency_readout, (np.ndarray, h5py.Dataset)):
            if np.unique(
                daq_frequency_readout[daq_frequency_readout[:] != -1]
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
        dcounts_arr = np.array(dcounts_arr, dtype=np.int64)  # must be of int64

        # Calculate Rates
        delta_time = dcounts_time / daq_frequency_readout  # seconds
        rate_arr = dcounts_arr.astype(float) / delta_time

        return delta_time, rate_arr
