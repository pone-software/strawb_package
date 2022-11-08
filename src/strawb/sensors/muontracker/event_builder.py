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

    def event_builder(self, threshold_ns=20e-9, reduce_dataframe=True):
        """Combines all the different steps to generate the events from the raw data.
        That includes:
        - remove invalid entries
        - label events where at least two entries are in a specified time range (threshold_ns)
        - calculate in event timing
        - remove the invalid duplicate entries
        - label the scintillator for each entries and count how many different scintillator
          got hit per event and if a entries is part of a double scintillator hit
          (both SiPMs of the scintillator are present in the event)
        - reduce to events with at least one double scintillator hit
        """
        dataframe = self.get_dataframe()

        # detect if there are two or more entries within a dt of some ns
        dataframe = self.add_labels(dataframe, threshold_ns=threshold_ns)

        # remove all entries with no close by neighbour (add_labels)
        base_length = len(dataframe)
        if reduce_dataframe:
            dataframe = dataframe[dataframe['label'] > 0]
            if self.verbose < 10:
                print(f'events reduced from: {base_length} to {len(dataframe)} - '
                      f'or {len(dataframe) / base_length * 100:.2f}% of df_base')

        # add label timing, important for a proper event ordering
        dataframe = self.add_label_timing(dataframe)

        # some channels appear two time with the same timing in one event (label), remove it
        base_length_2 = len(dataframe)
        if reduce_dataframe:
            dataframe = self.remove_duplicate(dataframe)
            if self.verbose < 10:
                print(f'events reduced from: {base_length_2} to {len(dataframe)} - '
                      f'or {len(dataframe) / base_length * 100:.2f}% of df_base')

        dataframe = self.add_scintillator(dataframe)
        dataframe = self.add_scintillator_counts(dataframe)

        base_length_3 = len(dataframe)
        if reduce_dataframe:
            dataframe = dataframe[dataframe.scintillator_double_count > 0].copy()
            if self.verbose < 10:
                print(f'events reduced from: {base_length_3} to {len(dataframe)} - '
                      f'or {len(dataframe) / base_length * 100:.2f}%  of df_base')

        dataframe.reset_index(drop=True, inplace=True)
        return dataframe

    def get_dataframe(self, trb_overflow=2750.):
        """ Load data and do first cleaning.
        removes: tot_time_ns!=1e-9 <-> there are some events with 1ns
        removes the TRB overflow in the timestamp but don't do it at tot_time_ns as it can cause precision loss"""
        tot = self.file_handler.tot_tot[:]

        tot_time_ns = self.file_handler.tot_time_ns[:]

        # some values are 1ns, exclude them
        mask_valid = tot_time_ns != 1e-9

        # some tot values are very high ~1e12, exclude them here or not
        max_tot = 1 * 1e3  # cut at 1us - [ns]
        mask_valid &= (tot < max_tot) & (tot > 0)

        if self.verbose < 10:
            print(f'exclude {np.sum(~mask_valid)} events')

        # time in seconds, time_masked since epoch (1.1.1970); remove the overflow,
        # but don't do it at tot_time_ns as it can cause precision loss
        time_masked = np.unwrap(self.file_handler.tot_time[mask_valid], period=trb_overflow)

        df_base = pandas.DataFrame({
            # time_masked since epoch (1.1.1970)
            'time': time_masked,
            # time_ns TRB internal
            'time_ns': tot_time_ns[mask_valid],
            # channel id
            'channel': self.file_handler.tot_channel[mask_valid],
            # tot in nano-seconds
            'tot': tot[mask_valid]})

        # the time isn't sorted correctly, do it here
        df_base.sort_values(['time', 'time_ns', 'tot'], inplace=True)

        # free RAM - parameter not needed
        del tot_time_ns, time_masked, mask_valid, tot
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
        label[1:][label[:-1] != 0] = label[:-1][label[:-1] != 0]  # add the shifted labels if label!=0
        return label, num_features

    def add_labels(self, dataframe, threshold_ns=20e-9):
        # event selection
        dt = np.diff(dataframe['time_ns'])
        dataframe['label'], _ = self.label_intermediate((dt >= 0) & (dt < threshold_ns))

        return dataframe

    @staticmethod
    def add_label_timing(dataframe):
        # add label count, but only if it doesn't exists
        if 'label_count' in dataframe:
            dataframe.pop('label_count')
        dataframe = pandas.merge(dataframe, dataframe.groupby('label')['label'].count(), how='left',
                                 right_index=True, left_on='label',
                                 suffixes=(None, '_count'))

        if 'time_ns_label' in dataframe:
            dataframe.pop('time_ns_label')
        dataframe = pandas.merge(dataframe, dataframe.groupby('label')['time_ns'].min(), how='left',
                                 right_index=True, left_on='label',
                                 suffixes=(None, '_label'))
        dataframe['time_ns_label'] = dataframe.time_ns - dataframe.time_ns_label

        return dataframe

    @staticmethod
    def remove_duplicate(dataframe):
        """most of the events don't show duplicate entries per channel
        - duplicate show a tot of ~25ns and ~58ns, whereas non duplicate have ~25ns
        - therefore -> the long TOT seem to be incorrect
        - it is sorted by tot and we want only the shortest
        - we get it with: aggfunc='first'

        """
        # the time isn't sorted correctly, do it here, to get keep='first'
        # keeping the ~25ns and not the ~58ns
        dataframe.sort_values(['label', 'time_ns_label', 'tot'], inplace=True)

        # mask duplicate per label and channel
        mask_duplicate = dataframe.duplicated(['label', 'channel'], keep='first')
        # get a dataframe with non duplicates
        return dataframe[~mask_duplicate].copy()

    @staticmethod
    def add_scintillator(dataframe, inplace=False):
        """Adds the scintillator number"""
        if not inplace:
            dataframe = dataframe.copy()

        # create the mapping between channel and scintillator
        trans_ch = np.array([[1, 11], [2, 12], [3, 9], [4, 10], [5, 15], [8, 14], [7, 13], [6, 16]]).flatten()
        trans_scintillator = np.array([[1, 1], [2, 2], [3, 3], [4, 4], [5, 5], [6, 6], [7, 7], [8, 8]]).flatten()

        # add a new column with the scintillator number; replace needs the same dtype
        dataframe['scintillator'] = dataframe.channel.replace(
            trans_ch.flatten().astype(dataframe.channel.dtype),
            trans_scintillator.flatten().astype(dataframe.channel.dtype))

        return dataframe

    @staticmethod
    def add_scintillator_counts(dataframe):
        # scintillator_double
        scintillator_count = dataframe.groupby('label')['scintillator'].count()
        scintillator_count.name = 'scintillator_count'

        # groupby(['label', 'scintillator']).scintillator.count() results in 1,
        # if there is only one SiPM involved or 2 if both SiPMs for one scintillator are involved.
        # True if both are involved: == 2
        scintillator_double = dataframe.groupby(['label', 'scintillator']).scintillator.count() == 2
        scintillator_double.name = 'scintillator_double'

        # now count the scintillator_double for each label to get or the counts of
        # full scintillator hits
        scintillator_double_count = scintillator_double.groupby('label').sum()
        scintillator_double_count.name = 'scintillator_double_count'

        df_sci = pandas.DataFrame(scintillator_double)
        df_sci = df_sci.merge(scintillator_double_count, how='left', left_on='label', right_index=True)

        # remove the names, otherwise, merge will add a suffix
        if 'scintillator_double' in dataframe:
            dataframe.pop('scintillator_double')
        if 'scintillator_double_count' in dataframe:
            dataframe.pop('scintillator_double_count')
        if 'scintillator_count' in dataframe:
            dataframe.pop('scintillator_count')

        dataframe = pandas.merge(dataframe, scintillator_count, how='left', right_index=True,
                                 left_on='label')
        dataframe = pandas.merge(dataframe, df_sci, how='left', right_index=True,
                                 left_on=['label', 'scintillator'])

        # only count a scintillator once
        dataframe['scintillator_count'] -= dataframe['scintillator_double_count']
        return dataframe
