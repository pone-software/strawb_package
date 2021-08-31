# Author: Kilian Holzapfel <kilian.holzapfel@tum.de>

import os

import numpy as np
import tables


class FileHandler:
    def __init__(self, filename, read_until_index=None):
        self.filename = os.path.abspath(filename)

        # Def. variables
        self.time_read = np.array([], dtype=float)  # time when the STDOUT was read

        self.channel_id = np.array([], dtype=int)
        self.counts_raw = np.array([[]], dtype=np.int32)

        # Load data from file
        self.load_from_file(read_until_index=read_until_index)  # loads: time_read, rate_readout, counts_raw, channel_id

        # apply corrections
        self.solve_leading_invalid_data()
        self.solve_unsorted_in_time()

    def load_from_file(self, read_until_index=None):
        """Load data from file. Loads: self.rate_readout, self.counts_raw, self.channel_id
        PARAMETER
        ---------
        read_until_index: int, optional
            Loads only the first items until read_until_index; None (defualt) loads all
        """
        if read_until_index is not None:
            read_until_index = int(read_until_index)

        data_dict = {}  # key= channel_id; value= counts

        with tables.open_file(self.filename) as f:
            # shouldn't change -> select the first value
            try:  # old file
                self.rate_readout = f.get_node('/daq/rate_readout')[-1]
            except:
                self.rate_readout = f.get_node('/daq/frequency_readout')[-1]

            for i in f.get_node('/counts'):
                if i.name == 'time':
                    self.time_read = f.get_node(i)[:read_until_index]

                else:
                    data_dict[int(i.name.replace('ch', ''))] = f.get_node(i)[:read_until_index]

        # data to 2d numpy array
        channel_id = np.array(list(data_dict.keys()))
        self.counts_raw = np.array(list(data_dict.values()), dtype=np.int32)

        # sort data by channel name; ch0, ch1,...
        self.counts_raw = self.counts_raw[np.argsort(channel_id)]
        self.channel_id = channel_id[np.argsort(channel_id)]

    def calibrate_time(self, offset):
        """offset: int
            Offset in seconds"""
        self.time_read += offset

    def solve_leading_invalid_data(self, ):
        counts = np.copy(self.counts_raw)

        # sometime the TRB shows at the beginning 0 with single values !=0
        # e.g. [0,0,0,4382,0] -> diff [-4382] -> +2 ** 31
        # solution, get single values surrounded by 0 also to 0 and replace this values with the first real counter
        mask_0 = counts == 0
        mask_0_sur = ~mask_0[:, 1:-1] & mask_0[:, :-2] & mask_0[:, 2:]
        counts[:, 1:-1][mask_0_sur] = 0

        # detect the positions in each channel where the 0-series ends
        index_leading_0 = []
        for i, counts_i in enumerate(counts):
            if counts_i[0] == 0:
                index_leading_0.append(np.argwhere(np.diff(counts[i], axis=-1)).flatten()[0] + 1)

        # delete those leading elements
        if len(index_leading_0) > 0:
            print(np.unique(index_leading_0))
            self.counts_raw = self.counts_raw[:, np.max(index_leading_0):]
            self.time_read = self.time_read[np.max(index_leading_0):]

    def solve_unsorted_in_time(self, ):
        """ This happend at some versions of the SDAQJob. Should be fixed."""
        if np.any(np.diff(self.time_read) < 0):
            print("The entries are not sorted in time, fix it here")
            index_sort = np.argsort(self.time_read)
            self.counts_raw = self.counts_raw[:, index_sort]
            self.time_read = self.time_read[index_sort]

    def get_datetime64(self, precision='us'):
        unit_dict = {'Y': 0, 'M': 0, 'D': 0, 'h': 0, 'm': 0, 's': 0, 'ms': -3, 'us': -6, 'ns': -6, 'as': -9}
        if precision in unit_dict:
            return (self.time_read / 10 ** unit_dict[precision]).astype(f'datetime64[{precision}]')
        else:
            raise KeyError(f'precision:{precision} not in {unit_dict.keys()}')