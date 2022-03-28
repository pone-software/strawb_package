# Author: Kilian Holzapfel <kilian.holzapfel@tum.de>
import matplotlib.cm
import numpy as np


class PMTMetaData:
    """ Holds the MetaData for the PMTSpectrometer001 (the one which is working in the Pacific)"""

    def __init__(self):
        # The entries are:        [index, channel_name, wavelength, label]
        dtype = [('index', int), ('trb', int), ('dac', int), ('padiwa', int), ('wavelength', int),
                 ('label', object), ('color', object)]
        channel_meta_array = np.array([(0, 1, 4, 8, 492, '', None),   # or (0, 1, 3, 4, 450, '', None) ?
                                       (1, 3, 1, 7, 480, '', None),
                                       (2, 5, 3, 6, 470, '', None),
                                       (3, 6, 7, 14, 0, '', None),
                                       (4, 7, 4, 5, 460, '', None),
                                       (5, 8, 5, 13, 550, '', None),
                                       (6, 9, 3, 4, 450, '', None),  # or (6, 9, 4, 8, 492, '', None) ?
                                       (7, 10, 6, 12, 525, '', None),
                                       (8, 11, 2, 3, 425, '', None),
                                       (9, 12, 5, 11, 510, '', None),
                                       (10, 13, 1, 2, 400, '', None),
                                       (11, 15, 0, 1, 350, '', None)],
                                      dtype=dtype)

        # sort in place
        channel_meta_array.sort(order='wavelength')

        # create labels
        channel_meta_array['label'] = [f'{i:.0f} nm' for i in channel_meta_array['wavelength']]
        channel_meta_array['label'][channel_meta_array['wavelength'] == 0] = 'No Filter'

        # store in place
        self.channel_meta_array = channel_meta_array

        self.add_colors()  # color with default settings

    def add_colors(self, color_map=None, no_filter_color='gray', invisible_cmap=None):
        """ Create colors.
        PARAMETERS
        ----------
        color_map: matplotlib.cm or str, optional
            a matplotlib colormap, default (None) is `color_map = matplotlib.cm.get_cmap('viridis')`
            If a string is provided its: color_map = matplotlib.cm.get_cmap(color_map)
        no_filter_color: matplotlib color or RGB(A)-Tuple, optional
            defines the color of the channel without filter.
        invisible_cmap: matplotlib.cm, optional
            the colors for invisible
        """
        if color_map is None:
            color_map = matplotlib.cm.get_cmap('viridis')
        elif isinstance(color_map, str):
            color_map = matplotlib.cm.get_cmap(color_map)

        self.channel_meta_array['color'] = None  # reset all colors to None

        # not-visible wavelengths
        if invisible_cmap is not None:
            m = self.channel_meta_array['wavelength'] < 380
            n_inv = np.count_nonzero(m)
            for i in np.argwhere(m).flatten():
                self.channel_meta_array['color'][i] = invisible_cmap(i / n_inv)

        if no_filter_color is not None:
            self.channel_meta_array['color'][self.channel_meta_array['wavelength'] == 0] = no_filter_color

        # set missing (None) colors
        # noinspection PyComparisonWithNone
        m = self.channel_meta_array['color'] == None
        n_inv = np.count_nonzero(m)
        for i in np.argwhere(m).flatten():
            self.channel_meta_array['color'][i] = color_map(i / n_inv)
