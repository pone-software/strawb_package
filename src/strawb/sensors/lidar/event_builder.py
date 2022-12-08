import numpy as np

import pandas
import scipy.ndimage


class EventBuilder:
    def __init__(self, file_handler, generate_dataframe=False, verbose=10):
        self.verbose = verbose
        self.file_handler = file_handler

        self.dataframe = None

        if generate_dataframe:
            # can take some seconds
            self.dataframe = self.event_builder()

    def __del__(self):
        self.file_handler = None
        del self.dataframe

    def event_builder(self, inplace=True):
        """Combines all the different steps to generate the events from the raw data.
        That includes:
        - remove invalid entries & correct TRB overflow
        - label events with same laser trigger time
        - hit order for each label. The first hit per label is 0, the second 1, ...
        PARAMETER
        ---------
        inplace: bool, optional
            if the dataframe should be stored in the class
        """
        dataframe = self.get_dataframe()

        # detect if there are two or more entries within a dt of some ns
        dataframe = self.add_labels(dataframe)

        # add the hit order for each label. The first hit per label is 0, the second 1, ...
        dataframe = self.add_hit_order(dataframe)
        if inplace:
            self.dataframe = dataframe
        return dataframe

    def get_dataframe(self, trb_overflow=2**38*1e-8):
        """ Load data and do first cleaning.
        removes: tot_time_ns!=1e-9 <-> there are some events with 1ns
        removes the TRB overflow in the timestamp - trb_overflow
        trb_overflow seems to be 2**38*1e-8s, the FPGA runs with 100Mhz -> 1e-8s and numbers are stored as ints usually
        for performance reasons. More information must be provided by the TRB group!"""
        tot = self.file_handler.tot_tot[:]  # [ns]
        tot_time_ns = self.file_handler.tot_time_ns[:]  # [s]

        # some values are 1ns, exclude them
        mask_valid = tot_time_ns != 1e-9

        # some tot values are very high ~1e12, exclude them here or not
        max_tot = 1 * 1e6  # cut at 1ms - [ns]
        mask_valid &= (tot < max_tot) & (tot > 0)

        if self.verbose < 10:
            print(f'exclude {np.sum(~mask_valid)} events')

        # time in seconds, time_masked since epoch (1.1.1970); remove the overflow,
        # but don't do it at tot_time_ns as it can cause precision loss
        # old: time_masked = np.unwrap(self.file_handler.tot_time[mask_valid], period=trb_overflow)
        tot_time_ns = np.unwrap(tot_time_ns[mask_valid], period=trb_overflow)
        tot_time_ns -= tot_time_ns[0]

        df_base = pandas.DataFrame({
            # time_masked since epoch (1.1.1970)
            'time': self.file_handler.tot_time[0] + tot_time_ns,
            # time_ns TRB internal in nanoseconds
            'time_ns': tot_time_ns,
            # tot in nanoseconds
            'dt_pmt': tot[mask_valid]})
        df_base['time'] = pandas.to_datetime(df_base['time']*1e9, utc=True)

        # the time isn't sorted correctly, do it here
        df_base.sort_values(['time', 'time_ns', 'dt_pmt'], inplace=True)

        # free RAM - parameter not needed
        del tot_time_ns, mask_valid, tot
        return df_base

    # define the label function
    @staticmethod
    def label_intermediate(input):
        """ Label features in an array based on a second intermediate array, which length is shorter by one.
        input                     =  [1,0,1,1,0,0,0,1]
        scipy.ndimage.label(input)=  [1,0,2,2,0,0,0,3]
        label_intermediate(input) = [1,1,2,2,2,0,0,3,3]
        Parameters
        ----------
        input : array_like
            The intermediate array-like object to be labeled. Any non-zero values in `input` are
            counted as features and zero values are considered the background.

        Returns
        -------
        label : ndarray or int
            An integer ndarray where each unique feature in `input` has a unique
            label in the returned array. And each label is extended by one item.
        num_features : int

        Example
        -------
        >>> d_a = np.diff(a)
        >>> labels = EventBuilder.label_intermediate(d_a<1.)
        >>> assert len(labels) == len(a)

        Test
        ----
        >>> a = np.array([1,0,2,2,0,0,0,3])
        >>> l, _ = EventBuilder.label_intermediate(a)
        >>> print(f'input         :  {a}')
        >>> print(f'l_intermediate: {l}')
        """
        label, num_features = scipy.ndimage.label(input, structure=None)
        label = np.append(label, [0])  # add one item
        label[1:][label[:-1] != 0] = label[:-1][label[:-1] != 0]  # add the shifted labels `if label!=0`
        return label, num_features

    def add_labels(self, dataframe):
        # event selection
        dt = np.diff(dataframe['time_ns'])
        dataframe['label'], _ = self.label_intermediate(dt == 0)

        return dataframe

    @staticmethod
    def add_hit_order(dataframe):
        """add the hit order for each label. dataframe needs the label column."""
        dataframe['hit_order'] = dataframe.groupby('label').cumcount()
        dataframe.loc[dataframe.label == 0, 'hit_order'] = 0
        return dataframe
