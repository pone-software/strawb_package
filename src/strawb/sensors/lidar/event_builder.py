import numpy as np
import pandas


class EventBuilder:
    def __init__(self, file_handler, generate_dataframe=False, verbose=10):
        self.verbose = verbose
        self.file_handler = file_handler

        self._dataframe_ = None

        if generate_dataframe:
            # can take some seconds
            self._dataframe_ = self.event_builder()

    def __del__(self):
        self.file_handler = None
        del self._dataframe_

    @property
    def dataframe(self):
        """The dataframe for the events.
        COLUMNS
        -------
        time    : datetime
            time in UTC
        time_ns : float
            time in seconds starting at 0 (the ns is misleading here). It's there in addition to the `time` to have
            sub-nanosecond precision, the absolut can handle with the 64bit.
        dt_pmt  : float
            delta time in nanoseconds between laser emission and PMT light detection (signal went over the threshold)
        label   : int
            labels with the same number came from the same laser pulse.
        hit_index: int
            based on the labels, and it's the nth hit for a laser pulse
        dt_index: float
            the delta time in nanoseconds between hits of the same laser flash
        """
        if self._dataframe_ is None:
            self.event_builder(inplace=True)
        return self._dataframe_

    @dataframe.setter
    def dataframe(self, dataframe):
        self._dataframe_ = dataframe

    def event_builder(self, inplace=True):
        """Combines all the different steps to generate the events from the raw data.
        That includes:
        - remove invalid entries & correct TRB overflow
        - add label events with same laser trigger time
        - add hit order for each label. The first hit per label is 0, the second 1, ...
        PARAMETER
        ---------
        inplace: bool, optional
            if the dataframe should be stored in the class
        """
        dataframe = self.get_dataframe()

        # # detect if there are two or more entries within a dt of some ns
        # dataframe = self.add_labels(dataframe)

        # add the hit order for each label. The first hit per label is 0, the second 1, ...
        dataframe = self.add_label_and_hit_index(dataframe)

        # Adds the delta time between hits of the same laser flash
        dataframe = self.add_dt_index(dataframe)

        if inplace:
            self._dataframe_ = dataframe
        return dataframe

    def get_dataframe(self, trb_overflow=2 ** 38 * 1e-8):
        """ Load data and do first cleaning.
        removes: tot_time_ns!=1e-9 <-> there are some events with 1ns
        removes the TRB overflow in the timestamp - trb_overflow
        trb_overflow seems to be 2**38*1e-8s, the FPGA runs with 100Mhz -> 1e-8s and numbers are stored as ints usually
        for performance reasons. More information must be provided by the TRB group!"""
        tot = self.file_handler.tot_tot[:]  # [ns]
        tot_time_ns = self.file_handler.tot_time_ns[:]  # [s]

        # some values are 1ns, exclude them
        mask_valid = tot_time_ns != 1e-9

        # some tot values are very high ~1e12, exclude them here
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
        df_base['time'] = pandas.to_datetime(df_base['time'] * 1e9, utc=True)

        # the time isn't sorted correctly, do it here
        # df_base.sort_values(['time', 'time_ns', 'dt_pmt'], inplace=True)

        # free RAM - parameter not needed
        del tot_time_ns, mask_valid, tot
        return df_base

    @staticmethod
    def add_label_and_hit_index(dataframe):
        """add the label and the hit order for each unique time_ns. dataframe needs the `time_ns` column."""
        gb = dataframe.groupby('time_ns')
        dataframe['hit_index'] = gb.cumcount()
        # dataframe.loc[dataframe.label == 0, 'hit_index'] = 0
        dataframe['label'] = gb.ngroup()
        return dataframe

    @staticmethod
    def add_dt_index(dataframe):
        """Adds the delta time between hits of the same laser flash, i.e. dt between hit index i and i+1.
        Needs a dataframe with 'dt_pmt' and 'hit_index'."""
        m = dataframe.hit_index > 0
        m_previous = m.shift(periods=-1, fill_value=False)
        dataframe.loc[m_previous, 'dt_index'] = 0
        dataframe.loc[m, 'dt_index'] = dataframe.loc[m, 'dt_pmt'].to_numpy()
        dataframe.loc[m, 'dt_index'] -= dataframe.loc[m_previous, 'dt_pmt'].to_numpy()
        return dataframe
