import sys
import threading
import time

import numpy as np
import pandas
import scipy.stats
import scipy.signal
from matplotlib import pyplot as plt
#  ---- HDF5 Helper ----
# add new asdatetime to h5py Dataset similar to asdtype for datetime64 when time is given as float in seconds
import tqdm


class AsDatetimeWrapper(object):
    def __init__(self, dset, precision='ns', date_type='datetime', scale2seconds=1.):
        """Wrapper to convert data on reading from a dataset. 'asdatetime' is similar to asdtype of h5py Datasets for
        and can handle datetime64 when time is given as float in seconds.
        PARAMETER
        ---------
        array: ndarray
            input array of timestamp as floats in the precision seconds.
        precision: str, optional
            defines the precision of the timestamp. Valid precisions are: 's', 'ms', 'us', 'ns' and 'ps'
        date_type: str, optional
            either `datetime` or `timedelta`
        scale2seconds: float, optional
            if the input array of timestamp is not in unit 'seconds', scale2seconds can correct the input.
            E.g.: if the input is in units:
            - 'hours' -> scale2seconds=3600. # seconds/hour
            - 'days' -> scale2seconds=24*3600. # seconds/days

        a = np.array([1624751981.4857635], float)  # time in seconds since epoch
        a.asdatetime('us')
        -> np.array('2021-06-26T23:59:41.485763', datetime64[us])
        """
        self._dset = dset

        self.unit_dict = {'s': 1, 'ms': 1e3, 'us': 1e6, 'ns': 1e9, 'ps': 1e12}

        if precision.lower() not in self.unit_dict:
            raise ValueError(f'precision not in unit_dict (unit_dict), got: {precision}')
        if date_type.lower() not in ['datetime', 'timedelta']:
            raise ValueError(f'date_type has to be out of: `datetime` or `timedelta`. Got: {date_type}')

        self._dtype = np.dtype(f'{date_type.lower()}64[{precision.lower()}]')
        self.scale = float(self.unit_dict[precision.lower()])
        self.scale2seconds = scale2seconds

    def __getitem__(self, args):
        return (self._dset.__getitem__(args, ) * self.scale * self.scale2seconds).astype(self._dtype)

    # @staticmethod
    def asdatetime(self, unit=None, precision='ns', date_type='datetime', scale2seconds=1.):
        """Converts timestamps of floats with precision seconds to numpy.datetime of the defined precision.
        PARAMETER
        ---------
        array: ndarray
            input array of timestamp as floats in the precision seconds.
        precision: str, optional
            defines the precision of the timestamp. Valid precisions are: 's', 'ms', 'us', 'ns' and 'ps'
        date_type: str, optional
            either `datetime` or `timedelta`
        scale2seconds: float, optional
            if the input array of timestamp is not in unit 'seconds', scale2seconds can correct the input.
            E.g.: if the input is in units:
            - 'hours' -> scale2seconds=3600. # seconds/hour
            - 'days' -> scale2seconds=24*3600. # seconds/days
        RETURNS
        -------
        array: ndarray
            numpy array with as dtype=datetime64 and the defined precision
        """
        if unit is not None:
            precision = unit
        return AsDatetimeWrapper(dset=self, precision=precision, date_type=date_type, scale2seconds=scale2seconds)


def asdatetime(array, precision='ns', date_type='datetime', scale2seconds=1.):
    """Converts timestamps of floats with precision seconds to numpy.datetime of the defined precision.
    PARAMETER
    ---------
    array: ndarray
        input array of timestamp as floats in the precision seconds.
    precision: str, optional
        defines the precision of the timestamp. Valid precisions are: 's', 'ms', 'us', 'ns' and 'ps'
    date_type: str, optional
        either `datetime` or `timedelta`
    scale2seconds: float, optional
        if the input array of timestamp is not in unit 'seconds', scale2seconds can correct the input.
        E.g.: if the input is in units:
        - 'hours' -> scale2seconds=3600. # seconds/hour
        - 'days' -> scale2seconds=24*3600. # seconds/days
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

    if not isinstance(array, np.ndarray):
        # try to convert it to a numpy array
        array = np.array(array)

    dtype = np.dtype(f'{date_type.lower()}64[{precision.lower()}]')
    scale = float(unit_dict[precision.lower()])

    return (array * scale * scale2seconds).astype(dtype)


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
    """Calculate the binned mean and std (standard deviation) for the given data.
    PARAMETER
    ----------
    x, y: ndarray, list
        input data in x and y as dtype float or int but not datetime64
    bins: int or sequence of scalars, optional
        parsed to scipy.stats.binned_statistic
    min_count: float, optional
        set the minimum count threshold as percentage of the max(bin_counts)
    """
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


def plot_binned_mean(x, y, bins=10000, ax=None, x_asdatetime=True, *args, **kwargs):
    """Plot the binned mean as line and the std (standard deviation) as filled area for the given data.
    PARAMETER
    ----------
    x, y: ndarray, list
        input data in x and y as dtype float or int but not datetime64
    bins: int or sequence of scalars, optional
        parsed to scipy.stats.binned_statistic
    ax: None or plt.Axes, optional
        the axes to add the plot. If None, default it takes plt.plot
    x_asdatetime: bool, optional
        if the x-data should be interpreted as datetime
    *args, **kwargs: list or dict, optional
        parsed to ax.plot(..., *args, **kwargs)
    """
    # cal. moving average with std
    bin_means, bin_std, bin_mid = binned_mean_std(x, y, bins=bins)

    if ax is None:  # use 'plt' if ax isn't set
        ax = plt

    if x_asdatetime:
        bin_mid = AsDatetimeWrapper.asdatetime(bin_mid)[:]
    lin, = ax.plot(bin_mid,
                   bin_means, *args, **kwargs)
    ax.fill_between(bin_mid,
                    y1=bin_means + bin_std,
                    y2=bin_means - bin_std,
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


def wavelength_to_rgb(wavelength, gamma=1., alpha_outside=.5):
    """This converts a given wavelength of light to an approximate RGB color value.
    A visible wavelength in nanometers is in the range from 350 nm through 780 nm.

    Based on code by Dan Bruton: http://www.physics.sfasu.edu/astro/color/spectra.html
    Mod. from: http://www.noah.org/wiki/Wavelength_to_RGB_in_Python

    PARAMTERS
    ---------
    wavelength: float,
        wavelength in nm
    gamma: float, optional
        Gamma correction implemented as a power law ([r,g,b]**gamma). Default: gamma=1.
    alpha_outside: float< optional
        alpha outside the visible range. In the range [380, 750]: alpha=1
        for <350 and >780: alpha=alpha_outside
        and [350, 380] & [750, 780] it linearly fades from alpha=1 to alpha=alpha_outside.

    RETURNS
    -------
    rgba: ndarray
        [[r_i, g_i, b_i, alpha_i], ...] for all given wavelengths.
    """

    wavelength_map = [350, 380, 440, 490, 510, 580, 645, 750, 780]
    # calc. alpha              wavelength_map = [350,380,440,490,510,580,645,750,780]
    alpha = np.interp(wavelength, wavelength_map, [0, 1, 1, 1, 1, 1, 1, 1, 0])
    alpha = alpha * (1 - alpha_outside) + alpha_outside

    # attenuation at visible limits, wavelength_map = [350,380,440,490,510,580,645,750,780]
    attenuation = np.interp(wavelength, wavelength_map, [0, 0, 1, 1, 1, 1, 1, 0, 0]) * .7 + .3

    # calc. colors             wavelength_map = [350,380,440,490,510,580,645,750,780]
    red = np.interp(wavelength, wavelength_map, [1, 1, 0, 0, 0, 1, 1, 1, 1]) * attenuation
    green = np.interp(wavelength, wavelength_map, [0, 0, 0, 1, 1, 1, 0, 0, 0]) * attenuation
    blue = np.interp(wavelength, wavelength_map, [1, 1, 1, 1, 0, 0, 0, 0, 0]) * attenuation

    # pack it into one np array
    rgba = np.array([red ** gamma, green ** gamma, blue ** gamma, alpha])
    return rgba.transpose()


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


def append_hdf5(file, dataset_name, data, axis=0, **kwargs):
    """Append a hdf5 dataset.
    PARAMETER
    ---------
    file: h5py.File
        must be open
    dataset_name: str
        the name of the dataset including the path
    data: ndarray
        the data to append
    axis: int, optional
        the axis which should be extended
    **kwargs: optional
        parsed to create_dataset"""
    d = file.get(dataset_name)
    if d is None:
        max_shape = list(data.shape).copy()
        max_shape[axis] = None
        init_shape = list(data.shape).copy()
        init_shape[axis] = 0

        file.create_dataset(dataset_name, data=data,
                            maxshape=max_shape,  # int(1e12),
                            #                              dtype=float, chunks=(10)
                            **kwargs
                            )
    elif data.shape[axis] != 0:
        len_append_items = data.shape[axis]
        d.resize(d.shape[axis] + len_append_items, axis=axis)

        if axis < 0:
            axis = len(d.shape) - axis

        # slice must be a tuple
        # slice(-len_append_items, None) = [-len_append_items:]
        # slice(None) = [:]
        # (slice(None), slice(-len_append_items, None)) = [:, -len_append_items:]
        slicer = (*(axis * [slice(None)]), slice(-len_append_items, None))
        d[slicer] = data

        # # TODO: is there a way to get this nicer?
        # if axis == 0:
        #     d[-len_append_items:] = data
        # elif axis == 1:
        #     d[:, -len_append_items:] = data
        # elif axis == 2:
        #     d[:, :, -len_append_items:] = data
        # elif axis == 3:
        #     d[:, :, :, -len_append_items:] = data
        # elif axis == 4:
        #     d[:, :, :, :, -len_append_items:] = data
        # elif axis == 5:
        #     d[:, :, :, :, :, -len_append_items:] = data
        # elif axis == 6:
        #     d[:, :, :, :, :, :, -len_append_items:] = data


def periodic2plot(x, y, period=(0., np.pi * 2.)):
    """A function to prepare periodic y-data for a plot. Everytime the y-data is crossing the boundary's 3 data-points
    are added to x and y. They represent the position when the data is crossing the boundary. For the y-data this means,
    [0, 0, period] or [period, 0, 0], depending on the direction. For x it's [x_i, x_i, x_i] and x_i is the position
    of the transits determined by linear interpolation. The middle datapoint in x and y are added and
    masked (np.ma.MaskedArray) to cut the plot at this position. This works for matplotlib.

    The perodicity range in y is: [0, period[

    PARAMETER
    ---------
    x: ndarray, list
        x-data as an array with same shape as y
    y: ndarray, list
        periodic data as an array with same shape as x. If it's not periodic it will be chnged to periodic data within
        the range [0, period[
    period: float, optional
        The period for the y-coordinates. The range is set to: [0, period[

    RETURNS
    -------
    x: MaskedArray
        x-data with added perioodic transitions
    y: MaskedArray
        y-data with added perioodic transitions

    EXAMPLE
    --------
    >>> import matplotlib.pyplot as plt
    >>> import numpy as np
    generate some periodic data crossing the boundaries
    >>> period = 1.
    >>> x = np.linspace(0., np.pi*4, 40)
    >>> y = (np.sin(x)+1) % period
    and plot the difference
    >>> plt.figure()
    >>> plt.plot(x, y, 'o-')
    >>> plt.plot(*periodic2plot(x,y, period=1))
    >>> plt.axhline(period, color='gray')
    >>> plt.axhline(0, color='gray')
    """
    dtype_convert_x, dtype_convert_y = None, None
    if not isinstance(x, np.ndarray):
        x = np.array(x)

    if not isinstance(y, np.ndarray):
        y = np.array(y)

    if np.issubdtype(x.dtype, np.timedelta64) or np.issubdtype(x.dtype, np.datetime64):
        dtype_convert_x = x.dtype
        x = x.astype(float)

    if np.issubdtype(y.dtype, np.timedelta64) or np.issubdtype(y.dtype, np.datetime64):
        dtype_convert_y = y.dtype
        y = y.astype(float)

    y %= period
    indexes = np.argwhere(np.abs(np.diff(y)) > .5 * period).flatten()
    index_shift = 0
    for i in indexes:
        i += index_shift
        index_shift += 3  # in every loop it adds 3 elements
        x_transit = np.interp(period, y[i:i + 2], x[i:i + 2], period=period)

        y_add = np.ma.array([period, 0., 0.] if y[i] > .5 * period else [0., 0., period], mask=[0, 1, 0])
        x_add = np.ma.array([x_transit] * 3, mask=[0, 1, 0])

        x = np.ma.hstack((x[:i + 1], x_add, x[i + 1:]))
        y = np.ma.hstack((y[:i + 1], y_add, y[i + 1:]))

    if dtype_convert_x is not None:
        x = x.astype(dtype_convert_x)
    if dtype_convert_y is not None:
        y = y.astype(dtype_convert_y)
    return x, y


def masked_convolve2d(in1, in2, correct_missing=True, norm=True, valid_ratio=1. / 3, *args, **kwargs):
    """A workaround for np.ma.MaskedArray in scipy.signal.convolve2d.
    It converts the masked values to complex values=1j. The complex space allows to set a limit
    for the imaginary convolution. The function use a ratio `valid_ratio` of np.sum(in2) to set a lower limit
    on the imaginary part to mask the values.
    I.e. in1=[[1.,1.,--,--]] in2=[[1.,1.]] -> imaginary_part/sum(in2): [[1., 1., .5, 0.]]
    -> valid_ratio=.5 -> out:[[1., 1., .5, --]].
    PARAMETERS
    ---------
    in1 : array_like
        First input.
    in2 : array_like
        Second input. Should have the same number of dimensions as `in1`.
    correct_missing : bool, optional
        correct the value of the convolution as a sum over valid data only,
        as masked values account 0 in the real space of the convolution.
    norm : bool, optional
        if the output should be normalized to np.sum(in2).
    valid_ratio: float, optional
        the upper limit of the imaginary convolution to mask values. Defined by the ratio of np.sum(in2).
    *args, **kwargs: optional
        parsed to scipy.signal.convolve(..., *args, **kwargs)
    """
    if not isinstance(in1, np.ma.MaskedArray):
        in1 = np.ma.array(in1)

    # np.complex128 -> stores real as np.float64
    con = scipy.signal.convolve2d(in1.astype(np.complex128).filled(fill_value=1j),
                                  in2.astype(np.complex128),
                                  *args, **kwargs
                                  )

    # split complex128 to two float64s
    con_imag = con.imag
    con = con.real
    mask = np.abs(con_imag / np.sum(in2)) > valid_ratio

    # con_east.real / (1. - con_east.imag): correction, to get the mean over all valid values
    # con_east.imag > percent: how many percent of the single convolution value have to be from valid values
    if correct_missing:
        correction = np.sum(in2) - con_imag
        con[correction != 0] *= np.sum(in2) / correction[correction != 0]

    if norm:
        con /= np.sum(in2)

    return np.ma.array(con, mask=mask)


def cal_middle(x):
    """Calculates: (x[1:]+x[:-1])*.5"""
    return (x[1:] + x[:-1]) * .5


def connect_polar(x):
    """Connect data for a polar plot, i.e. np.append(x, x[0])."""
    if isinstance(x, np.ma.MaskedArray):
        return np.ma.append(x, x[0])
    else:
        return np.append(x, x[0])


def pd_timestamp_mask_between(series_start, series_stop, time_from, time_to, tz="UTC"):
    """Mask time-extended entries which overlap with a time range: [time_from, time_to].
    time-extended entries are specified with series_start, series_stop.
    PARAMETER
    ---------
    series_start, series_stop: pandas.Series
        two series with the same length indicating the start and stop time of each entry
    time_from, time_to: datetime-like, str, int, float
        Value to be converted to Timestamp.
    tz : str, pytz.timezone, dateutil.tz.tzfile or None, optional
        Time zone for time_from, time_to. Default: "UTC"
    RETURNS
    -------
    mask: bool pandas.Series
        masked series of entries which overlap with the time range
    """
    time_from = pandas.Timestamp(time_from, tz=tz)
    time_to = pandas.Timestamp(time_to, tz=tz)

    # files which cover the start time
    mask = (series_start <= time_from) & (series_stop >= time_from)

    # files which cover the end time
    mask |= (series_start <= time_to) & (series_stop >= time_to)

    # files in-between start and end time
    mask |= (series_start >= time_from) & (series_stop <= time_to)

    return mask
