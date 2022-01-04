import h5py
import numpy as np


class TRBTools:
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
        counts_arr[counts_arr < 0] += 2 ** 31  # delta<0 when there is an overflow 2**31 (TRBint)
        return counts_arr.astype(np.int32)

    @staticmethod
    def _calculate_rates_(daq_frequency_readout, dcounts_time, *args, **kwargs):
        """ Converts the cleaned counts readings from the TRB into rates.
        PARAMETER
        ---------
        daq_frequency_readout: Union[int, float, list, np.ndarray, h5py.Dataset]
            the TRB readout frequency in Hz. If a list, np.ndarray, or h5py.Dataset is provided. Cut -1 values
            (TRB inactive) and check if the array is unique. Take the unique value or raise and RuntimeError.
        dcounts_time:
            The delta counts (s. _diff_counts_) of channel 0. The TRB counts channel 0 up with the frequency
            from daq_frequency_readout.
        args or kwargs: Union[list, np.ndarray, h5py.Dataset], optional
            Each entry is handled as a separated channel of dcounts (delta counts, s. _diff_counts_).

        RETURN
        ------
        counts_ch0_time: np.ndarray
            the timedelta corresponding to each count. Calculated from channel 0 in seconds.
        rate_arr: np.ndarray
            the rates in Hz of the provided channels defined in args or kwargs as one ndarray.
        """
        # Prepare parameter
        # Check type and shape of counts arrays
        if isinstance(daq_frequency_readout, list):  # convert to array
            daq_frequency_readout = np.array(daq_frequency_readout)
        if isinstance(daq_frequency_readout, (np.ndarray, h5py.Dataset)):
            if np.unique(daq_frequency_readout[daq_frequency_readout[:] != -1]).shape != (1,):
                raise RuntimeError('More than 1 unique value exits in daq_frequency_readout.')
            else:
                # if the daq_frequency_readout failed reading from thte TRB it logs -1, correct here
                daq_frequency_readout = daq_frequency_readout[daq_frequency_readout[:] != -1][0]

        daq_frequency_readout = float(daq_frequency_readout)  # must be a float

        # Check type and shape of counts arrays
        args = list(args)
        for i in kwargs:
            args.append(kwargs[i])

        dcounts_arr = np.array([*args], dtype=np.int64)

        # Calculate Rates
        delta_time = dcounts_time / daq_frequency_readout # seconds
        rate_arr = dcounts_arr.astype(float) / delta_time

        return delta_time, rate_arr
