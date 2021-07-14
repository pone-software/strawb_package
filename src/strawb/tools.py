import numpy as np
import scipy.stats
from matplotlib import pyplot as plt

import strawb


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

    lin, = ax.plot(strawb.AsDatetimeWrapper.asdatetime(bin_mid)[:],
                   bin_means, *args, **kwargs)
    ax.fill_between(strawb.AsDatetimeWrapper.asdatetime(bin_mid)[:],
                    y1=bin_means + bin_std, y2=bin_means - bin_std,
                    color=lin.get_color(), alpha=.2)
