# Author: Kilian Holzapfel <kilian.holzapfel@tum.de>

import numpy as np


class PMTMetaData:
    """ Holds the MetaData for the PMTSpectrometer001 (the one which is working in the Pacific)"""
    def __init__(self):
        # The entries are:        [index, channel_name, wavelength, label]
        dtype = [('index', int), ('channel', int), ('wavelength', int), ('label', object), ('color', object)]
        channel_meta_array = np.array([(0, 1, 450, '', None),
                                       (1, 3, 480, '', None),
                                       (2, 5, 470, '', None),
                                       (3, 6, 0, '', None),
                                       (4, 7, 460, '', None),
                                       (5, 8, 550, '', None),
                                       (6, 9, 492, '', None),
                                       (7, 10, 525, '', None),
                                       (8, 11, 425, '', None),
                                       (9, 12, 510, '', None),
                                       (10, 13, 400, '', None),
                                       (11, 15, 350, '', None)],
                                      dtype=dtype)

        # sort in place
        channel_meta_array.sort(order='wavelength')

        # create labels
        channel_meta_array['label'] = [f'{i:.0f} nm' for i in channel_meta_array['wavelength']]
        channel_meta_array['label'][channel_meta_array['wavelength'] == 0] = 'No Filter'

        # store in place
        self.channel_meta_array = channel_meta_array

    def add_colors(self, color_map, no_filter_color='gray'):
        """ Create colors.
        PARAMETERS
        ----------
        color_map: matplotlib.cm
            a matplotlib colormap, i.e. `color_map = matplotlib.cm.get_cmap('viridis')`
        no_filter_color: matplotlib color or RGB(A)-Tuple, optional
            defines the color of the channel without filter.
        """
        entries = self.channel_meta_array.shape[0]
        self.channel_meta_array['color'] = [color_map(i / entries) for i in range(entries)]
        if no_filter_color is not None:
            self.channel_meta_array['color'][self.channel_meta_array['wavelength'] == 0] = no_filter_color
