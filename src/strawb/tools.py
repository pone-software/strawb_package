import sys
import threading
import time

import numpy as np
import scipy.stats
from matplotlib import pyplot as plt
#  ---- HDF5 Helper ----
# add new asdatetime to h5py Dataset similar to asdtype for datetime64 when time is given as float in seconds
import tqdm


class AsDatetimeWrapper(object):
    def __init__(self, dset, precision='us'):
        """Wrapper to convert data on reading from a dataset. 'asdatetime' is similar to asdtype of h5py Datasets for
        and can handle datetime64 when time is given as float in seconds.
        a = np.array([1624751981.4857635], float)  # time in seconds since epoch
        a.asdatetime('ms')
        -> np.array('2021-06-26T23:59:41.485763', datetime64[ms])
        """
        self._dset = dset

        self.unit_dict = {'s': 1, 'ms': 1e3, 'us': 1e6, 'ns': 1e9}
        if precision.lower() not in self.unit_dict:
            raise ValueError(f'precision not in unit_dict (unit_dict), got: {precision}')

        self._dtype = np.dtype(f'datetime64[{precision.lower()}]')
        self.scale = float(self.unit_dict[precision.lower()])

    def __getitem__(self, args):
        return (self._dset.__getitem__(args, ) * self.scale).astype(self._dtype)

    # @staticmethod
    def asdatetime(self, unit='us'):
        return AsDatetimeWrapper(dset=self, precision=unit)


def asdatetime(array, precision='us', date_type='datetime'):
    """Converts timestamps of floats with precision seconds to numpy.datetime of the defined precision.
    PARAMETER
    ---------
    array: ndarray
        input array of timestamp as floats in the precision seconds.
    precision: str, optional
        defines the precision of the timestamp. Valid precisions are: 's', 'ms', 'us', 'ns' and 'ps'
    date_type: str, optional
        either `datetime` or `timedelta`
    RETURNS
    -------
    array: ndarray
        numpy array with as dtype=datetime64 and the defined precision
    """
    unit_dict = {'s': 1, 'ms': 1e3, 'us': 1e6, 'ns': 1e9, 'ps': 1e12}
    if precision.lower() not in unit_dict:
        raise ValueError(f'precision not in unit_dict (unit_dict), got: {precision}')
    if date_type.lower() not in ['datetime', 'timedelta']:
        raise ValueError(f'date_type has to be out of: `datetime` or `timedelta`. Got: {date_type}')

    dtype = np.dtype(f'{date_type.lower()}64[{precision.lower()}]')
    scale = float(unit_dict[precision.lower()])

    return (array * scale).astype(dtype)


def datetime2float(array):
    """Converts a datetime64 array into seconds (as float) since epoch."""
    unit_dict = {'D': 3600 * 24, 'h': 3600, 'm': 60, 's': 1, 'ms': 1e-3, 'us': 1e-6, 'ns': 1e-9, 'ps': 1e-12}
    dtype = array.dtype
    if not (np.issubdtype(dtype, np.timedelta64) or np.issubdtype(dtype, np.datetime64)):
        raise TypeError(f'Supports only datetime64 or timedelta64. Got {dtype}')
    else:
        for i in unit_dict:
            if dtype == f'datetime64[{i}]' or dtype == f'timedelta64[{i}]':
                return array.astype(float) * unit_dict[i]
        raise TypeError(f'Supports only specific datetime64 and timedelta64. Got {dtype}')


class ShareJobThreads:
    def __init__(self, thread_n=3, fmt=None, unit='items', buffer_type=list):
        """ A Class which spreads a iterable job defined by a function f to n threads. It is basically a Wrapper for:
        for i in iterable:
            f(i)

        The above example translates to:
        sjt = ShareJobThreads(4)  # for 4 threads
        sjt.do(f, iterable)

        In addition it provides a progress bar.

        PARAMETER
        ---------
        thread_n: int, optional
            the number of threads which will be used to execute the functions
        fmt: str, optional
            formatter for the bar, if not None, the iterable has to be a dict, i.e. iterable=[{'a':1, 'b':2},...], and
            the fmt: '{a}-{b}'.
        unit: str, optional
            the unit shows up in the progress bar as '<unit>/s'. Default: 'items'
        buffer_type: type, optional
            defines the buffer type which stores the return of f(iterable[i]). Either a list (default) or a dict. The
            dict stores in the format: {iterable[i]: f(iterable[i])}.
        """
        self.thread_n = thread_n
        self.lock = threading.Lock()
        self.thread_bar = None
        self.active = False
        self.event = threading.Event()

        if buffer_type in [list, dict]:
            self.buffer_type = buffer_type
        else:
            raise TypeError(f"buffer_type must be 'list' or 'dict'. Got: {buffer_type}")
        self.return_buffer = None  # to store all returns from the functions

        self.threads = None  # the _worker_ threads
        self.iterable = None  # the iterable
        self.kwargs = {}  # kwargs for the f -> f(i, **self.kwargs)
        self.i = None  # the actual index of the next item
        self.i_bar = None  # the actual index of the done items
        self.f = None  # the function

        # formatter for the bar, if not None, the iterable has to be a dict, i.e. {'a':1, 'b':2}, and the fmt: '{a}-{b}'
        self.fmt = fmt  # formatter for the bar
        self.unit = unit

    def do(self, f, iterable, unit=None, **kwargs):
        """Start the iterable job defined by a function f, an iterable and **kwargs on multiple threads. Each thread
        does f(iterable[i], **kwargs) until there is no iterable left. The number of threads is defined at the
        initialization of ShareJobThreads.

        PARAMETER
        ---------
        f: executable
            the function which is executed simultaneously on several threads. It has to take at least one argument.
        iterable: iterable
            the iterable the threads takes the items and execute the function with it
        kwargs: dict, optional
            kwargs are parsed to all function calls and don't change. It uses f(iterable[i], **kwargs).
        unit: str, optional
            the unit shows up in the progress bar as '<unit>/s'. Default: None, takes the value from the class
            initialisation.
        """
        self.active = True
        self.iterable = iterable
        self.kwargs = kwargs
        self.i = 0
        self.i_bar = 0
        self.f = f

        self.return_buffer = self.buffer_type()

        if unit is not None:
            self.unit = unit

        self.threads = []

        for i in range(self.thread_n):
            thread_i = threading.Thread(target=self._worker_)
            thread_i.start()
            self.threads.append(thread_i)

        self.thread_bar = threading.Thread(target=self._update_bar_)
        self.thread_bar.start()
        self.thread_bar.join()

        if self.return_buffer not in [list(), dict()]:
            return self.return_buffer

    def _update_bar_(self, ):
        """The function for the thread 'thread_bar' which takes care of the bar updates."""
        last_i = 0

        with tqdm.tqdm(self.iterable,
                       file=sys.stdout,
                       unit=self.unit) as bar:
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
        """Stop the Job."""
        self.active = False

    def _worker_(self, ):
        """The worker function for the worker threads. It takes care of executing the target function 'f' with the next
        item of the iterable list and the kwargs. """
        active = True
        while self.active and active:
            iterable_i, active = self._get_next_()
            if active:
                try:
                    buffer = self.f(iterable_i, **self.kwargs)
                except (RuntimeError, Exception) as err:
                    print(f'Error occurred at {iterable_i}: {err}')
                    buffer = None
                with self.lock:
                    if buffer is not None:
                        self.return_buffer.append(buffer)
                    self.i_bar += 1

    def _get_next_(self, ):
        """ Get the next item of the iterable with a lock."""
        with self.lock:
            if len(self.iterable) > self.i:
                iterable_i = self.iterable[self.i]
                self.i += 1
                return iterable_i, True
            else:
                return None, False


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
    """Plot the binned mean as line and the std (standard deviation) as filled area for the given data."""
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


# From: https://stackoverflow.com/questions/1094841/get-human-readable-version-of-file-size
def human_size(size_bytes, units=None, base=1024, precision=2):
    """ Returns a human readable string representation of bytes
    PARAMETER
    ---------
    size_bytes: int, float
        the file size as number
    units: list, optional
        the units to take as a list starting from small to big. Units are separated by the factor defined in base.
        Default: [' bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB'].
    base: float, optional
        defines the base which defines the factor between units, i.e. base=1024; 1024 -> 1 KB. Default: 1024
    precision: int, optional
        the precision the returned string has. I.e.: precision=2 -> `XXX.XX ...`
    """
    if units is None:
        units = [' bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB']
    return f'{size_bytes:.{precision}f} {units[0]}' if size_bytes < base else human_size(size_bytes / base, units[1:])


def wavelength_to_rgb(channel, gamma=0.8):
    """This converts a given wavelength of light to an
    approximate RGB color value. The wavelength must be given
    in nanometers in the range from 380 nm through 750 nm
    (789 THz through 400 THz).
    Based on code by Dan Bruton
    http://www.physics.sfasu.edu/astro/color/spectra.html
    """

    try:
        wavelength = float(channel["wavelength"])
        alt_color = channel["color"]
    except:
        wavelength = channel
        alt_color = "red"

    if 380 <= wavelength <= 440:
        attenuation = 0.3 + 0.7 * (wavelength - 380) / (440 - 380)
        R = ((-(wavelength - 440) / (440 - 380)) * attenuation) ** gamma
        G = 0.0
        B = (1.0 * attenuation) ** gamma
        return_this = (R, G, B)
    elif 440 <= wavelength <= 490:
        R = 0.0
        G = ((wavelength - 440) / (490 - 440)) ** gamma
        B = 1.0
        return_this = (R, G, B)
    elif 490 <= wavelength <= 510:
        R = 0.0
        G = 1.0
        B = (-(wavelength - 510) / (510 - 490)) ** gamma
        return_this = (R, G, B)
    elif 510 <= wavelength <= 580:
        R = ((wavelength - 510) / (580 - 510)) ** gamma
        G = 1.0
        B = 0.0
        return_this = (R, G, B)
    elif 580 <= wavelength <= 645:
        R = 1.0
        G = (-(wavelength - 645) / (645 - 580)) ** gamma
        B = 0.0
        return_this = (R, G, B)
    elif 645 <= wavelength <= 750:
        attenuation = 0.3 + 0.7 * (750 - wavelength) / (750 - 645)
        R = (1.0 * attenuation) ** gamma
        G = 0.0
        B = 0.0
        return_this = (R, G, B)
    else:
        return_this = alt_color
    return return_this


def unique_steps(t, state, ratio_steps_len_1=.75, plot=False):
    """ Each step (same state in a row) get a start and end time if there is only one time for one step,
    the end is calculated as a ratio (ratio_steps_len_1)
    PARAMETERS
    ----------
    t: ndarray
        the time series of len N
    state: ndarray
        the state series of len N
    ratio_steps_len_1: float, optional
        if a step has only one point and not start + end, the one point is defined as starting point and the end is
        defined by the ratio to the next step. [..., t_0, t_1,...] -> [..., t_0, (t_1-t_0)*ratio_steps_len_1, t_1,...]
    plot: bool, optional
        if a plot t vs state should be plotted to show how it works.

    RETURNS
    --------
    t_steps: ndarray
        [[t_0, t_1], [t_2, t_3],...,[t_(2*i),t_(2*i+1)]]
    state: ndarray
        [[s_0, s_0], [s_1, s_1],...,[s_i,s_i]]
    """
    # cumsum over the bool array of changes
    change_cumsum = np.cumsum([0, *np.diff(state).astype(bool)])

    mask_changes = np.ones_like(change_cumsum, dtype=bool)
    mask_changes[-1] = change_cumsum[-1] != change_cumsum[-2]
    mask_changes[1:-1] = np.diff(change_cumsum[:-1]) != 0

    index_steps = np.array([np.argwhere(mask_changes), np.argwhere(mask_changes)]).T.reshape(-1, 2)
    index_steps[:-1, 1] = index_steps[1:, 0] - 1
    index_steps[-1, 1] = len(state) - 1

    t_steps = t[index_steps].astype(float)

    step_len_1 = np.argwhere(t_steps[:, 0] == t_steps[:, 1]).flatten()
    t_steps[step_len_1[:-1], 1] += (t_steps[step_len_1[:-1] + 1, 0] - t_steps[step_len_1[:-1], 0]) * ratio_steps_len_1

    if plot:
        plt.figure()
        plt.plot(t, state, 'o-', label='raw')
        plt.plot(t[mask_changes], state[mask_changes], 'o-', label='mask changes')
        plt.plot(t[index_steps.flatten()], state[index_steps.flatten()], 's', label='index_steps')
        plt.plot(t_steps.flatten(), state[index_steps.flatten()], 'x-', label='t_steps')
        # plt.plot(tt.T, state[mm].T, 'o--')-
        # tt, state[mm].T, m, mm
        plt.legend()

    return t_steps, state[index_steps]
