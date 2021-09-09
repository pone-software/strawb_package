import sys
import threading
import time

import numpy as np
import scipy.stats
from matplotlib import pyplot as plt

#  ---- HDF5 Helper ----
# add new asdatetime to h5py Dataset similar to asdtype for datetime64 when time is given as float in seconds
from tqdm import tqdm


class AsDatetimeWrapper(object):
    def __init__(self, dset, unit='us'):
        """Wrapper to convert data on reading from a dataset. 'asdatetime' is similar to asdtype of h5py Datasets for
        and can handle datetime64 when time is given as float in seconds.
        a = np.array([1624751981.4857635], float)  # time in seconds since epoch
        a.asdatetime('ms')
        -> np.array('2021-06-26T23:59:41.485763', datetime64[ms])
        """
        self._dset = dset

        self.unit_dict = {'s': 1, 'ms': 1e3, 'us': 1e6, 'ns': 1e9}
        if unit.lower() not in self.unit_dict:
            raise ValueError(f'unit not in unit_dict (unit_dict), got: {unit}')

        self._dtype = np.dtype(f'datetime64[{unit.lower()}]')
        self.scale = float(self.unit_dict[unit.lower()])

    def __getitem__(self, args):
        return (self._dset.__getitem__(args, ) * self.scale).astype(self._dtype)

    @staticmethod
    def asdatetime(self, ):
        return AsDatetimeWrapper(self, )


class ShareJobThreads:
    def __init__(self, thread_n=3, fmt=None):
        """ A Class which spreads a iterable job defined by a function f to n threads. It is basically a Wrapper for:
        for i in iterable:
            f(i)

        The above example translates to:
        sjt = ShareJobThreads(4)  # for 4 threads
        sjt.do(f, iterable)
        """
        self.thread_n = thread_n
        self.lock = threading.Lock()
        self.thread_bar = None
        self.active = False
        self.event = threading.Event()

        self.return_buffer = None  # to store all returns from the functions

        self.threads = None  # the _worker_ threads
        self.iterable = None  # the iterable
        self.i = None  # the actual index of the next item
        self.i_bar = None  # the actual index of the done items
        self.f = None  # the function

        # formatter for the bar, if not None, the iterable has to be a dict, i.e. {'a':1, 'b':2}, and the fmt: '{a}-{b}'
        self.fmt = fmt  # formatter for the bar

    def do(self, f, iterable, ):
        self.active = True
        self.iterable = iterable
        self.i = 0
        self.i_bar = 0
        self.f = f
        self.return_buffer = []

        self.threads = []

        for i in range(self.thread_n):
            thread_i = threading.Thread(target=self._worker_)
            thread_i.start()
            self.threads.append(thread_i)

        self.thread_bar = threading.Thread(target=self._update_bar_)
        self.thread_bar.start()
        self.thread_bar.join()

        if self.return_buffer is not []:
            return self.return_buffer

    def _update_bar_(self, ):
        last_i = 0

        with tqdm(self.iterable,
                  file=sys.stdout,
                  unit='file') as bar:
            while any([thread_i.is_alive() for thread_i in self.threads]) or last_i != self.i_bar:
                with self.lock:
                    # print(self.i, self.active)
                    if last_i != self.i_bar:
                        for i in range(self.i_bar - last_i):
                            str_i = self.iterable[self.i - 1 - i]
                            if self.fmt is not None and isinstance(self.iterable[self.i - 1 - i], dict):
                                str_i = self.fmt.format(**self.iterable[self.i - 1 - i])

                            bar.set_postfix({'i': str_i})
                            bar.update()

                        last_i = self.i_bar
                time.sleep(0.1)  # delay a bit

    def stop(self, ):
        self.active = False

    def _worker_(self, ):
        iterable_i = True
        while self.active and iterable_i:
            iterable_i = self._get_next_()
            if iterable_i is not False:
                try:
                    buffer = self.f(iterable_i)
                except (RuntimeError, Exception) as err:
                    print(f'Error occurred at {iterable_i}: {err}')
                    buffer = None
                with self.lock:
                    if buffer is not None:
                        self.return_buffer.append(buffer)
                    self.i_bar += 1

    def _get_next_(self, ):
        with self.lock:
            if len(self.iterable) > self.i:
                iterable_i = self.iterable[self.i]
                self.i += 1
                return iterable_i
            else:
                return False


def hdf5_getunsorted(self, index):
    """Access a items of hdf5 dataset in an unsorted way. Indexes can also occur multiple times.
    If 'dset' is a dataset with the data [.1,.2]; dset.getunsorted([0,1,0]) -> [.1,.2,.1]"""
    unique, inv_index = np.unique(index, return_inverse=True)
    return self[unique][inv_index]


# ---- statistic and plotting ----
def binned_mean_std(x, y, bins=100, min_count=.1):
    """Calculate the binned mean and std (standard deviation) for the given data."""
    bin_means, bin_edges, binnumber = scipy.stats.binned_statistic(x, y, statistic='mean', bins=bins)
    bin_std, bin_edges, binnumber = scipy.stats.binned_statistic(x, y, statistic='std', bins=bins)
    bin_counts, bin_edges, binnumber = scipy.stats.binned_statistic(x, y, statistic='count', bins=bins)

    # cal. bin middle points
    bin_centers = bin_edges[:-1] + (bin_edges[1] - bin_edges[0]) / 2.

    # cal. min. count threshold
    if min_count < 0:
        min_count = np.max(bin_counts) * min_count

    # create masked arrays
    bin_means = np.ma.array(bin_means, mask=bin_counts < min_count)
    bin_std = np.ma.array(bin_std, mask=bin_means.mask)

    return bin_means, bin_std, bin_centers


def plot_binned_mean(x, y, bins=10000, ax=None, *args, **kwargs):
    """Plot the binned mean as line and the std (standard deviation) as filled aread for the given data."""
    # cal. moving average with std
    bin_means, bin_std, bin_mid = binned_mean_std(x, y, bins=bins)

    if ax is None:  # use 'plt' if ax isn't set
        ax = plt

    lin, = ax.plot(AsDatetimeWrapper.asdatetime(bin_mid)[:],
                   bin_means, *args, **kwargs)
    ax.fill_between(AsDatetimeWrapper.asdatetime(bin_mid)[:],
                    y1=bin_means + bin_std, y2=bin_means - bin_std,
                    color=lin.get_color(), alpha=.2)


def add_docs(org_func):
    """A decorator which forwards a docstring from a function to another, i.e. at overloading a function.
    Usage:
    def function():
        '''Docstring'''
        ...

    @add_docs(function)
    def function_2():
        '''This docstring is overwritten/ignored!'''
        ...

    help(function)
    -> Docstring
    """

    def desc(func):
        func.__doc__ = org_func.__doc__
        return func

    return desc
