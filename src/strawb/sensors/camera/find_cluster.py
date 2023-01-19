import numpy as np
import scipy.ndimage
import cv2
import pandas as pd
import tqdm.notebook

from strawb.tools import asdatetime


class FindCluster:
    def __init__(self, camera, min_std=3, min_size_cluster=3, max_gaps=2,
                 pixel_mean=None, pixel_std=None, images=None, eff_margin=True):
        """
        Parameters
        ----------
        images : numpy.ndarray
            Array of all available images.
        min_std : int, optional
            Minimum multiple of the standard deviation for a pixel to be considered as bright.
        min_size_cluster : int, optional
            Minimum number of adjoining pixels to be considered a cluster.
        max_gaps: int, optional
            the maximum gap size within one cluster
        images : numpy.ndarray, optional
            Array of all available images. If None, create arrays at initialisation.
            Or provide the data, can speed things up.
        pixel_mean, pixel_std: numpy.ndarray, optional
            If None, create arrays at initialisation. Or provide the data, can speed things up.
        eff_margin: bool, optional
            if pixel should be cut by the effective margin. Default, True.
        """

        self.camera = camera
        self._images_ = images
        self.eff_margin = eff_margin

        self.min_std = min_std
        self.min_size_cluster = min_size_cluster
        self.max_gaps = max_gaps

        # mean brightness & standard deviation per pixel averaged over all available pictures
        self._pixel_mean_ = pixel_mean
        self._pixel_std_ = pixel_std

        self._pixel_rgb_mask_ = None

    def __del__(self):
        """Remove links to other classes to prevent deadlock."""
        self.camera = None  # unlink
        del self._images_
        del self._pixel_mean_
        del self._pixel_std_

    @property
    def pixel_rgb_mask(self):
        if self._pixel_rgb_mask_ is None:
            self._pixel_rgb_mask_ = [self.camera.images.get_raw_rgb_mask(self.images.shape[1:], 'red',
                                                                         eff_margin=self.eff_margin),
                                     self.camera.images.get_raw_rgb_mask(self.images.shape[1:], 'green',
                                                                         eff_margin=self.eff_margin),
                                     self.camera.images.get_raw_rgb_mask(self.images.shape[1:], 'blue',
                                                                         eff_margin=self.eff_margin)
                                     ]
        return self._pixel_rgb_mask_

    @property
    def pixel_red_mask(self):
        return self.pixel_rgb_mask[0]

    @property
    def pixel_green_mask(self):
        return self.pixel_rgb_mask[1]

    @property
    def pixel_blue_mask(self):
        return self.pixel_rgb_mask[2]

    @property
    def pixel_mean(self):
        """Mean brightness per pixel averaged over all available pictures"""
        if self._pixel_mean_ is None:
            self._pixel_mean_ = np.mean(self.images, axis=0)
        return self._pixel_mean_

    @pixel_mean.setter
    def pixel_mean(self, value):
        """Setter for mean brightness per pixel averaged over all available pictures"""
        self._pixel_mean_ = value

    @property
    def pixel_std(self):
        """Standard deviation per pixel averaged over all available pictures"""
        if self._pixel_std_ is None:
            self._pixel_std_ = np.std(self.images, axis=0)
        return self._pixel_std_

    @pixel_std.setter
    def pixel_std(self, value):
        """Setter for standard deviation per pixel averaged over all available pictures"""
        self._pixel_std_ = value

    @property
    def images(self):
        if self._images_ is None:
            self._images_ = self.camera.file_handler.raw[:]
            if self.eff_margin:
                self._images_ = self.camera.images.cut2effective_pixel(self._images_)
        return self._images_

    @images.setter
    def images(self, value):
        self._images_ = value

    def get_cluster(self, pic_index, min_std=None, min_size_cluster=None, max_gaps=None, mask_mounting=False):
        """
        Find clusters of bright pixels.

        Parameters
        ----------
        pic_index : int
            Index of the picture (in self.images) to get the labels of.
        min_std : int, optional
            Minimum multiple of the standard deviation for a pixel to be considered as bright. If None, take from init.
        min_size_cluster : int, optional
            Minimum number of adjoining pixels to be considered a cluster. If None, take from init.
        max_gaps: int, optional
            the maximum gap size within one cluster. If None, take from init.
        mask_mounting: bool or ndarray, optional
            True if the mounting, if known, should be excluded from the cluster search (mounting will be all label=0).
            A ndarray defines the mask which pixels should be excluded from the cluster search. Must match the pixel
            shape. `mask_mounting[i] = True` means include and `mask_mounting[i] = False` exclude the pixel i.
        Returns
        -------
        numpy.ndarray
            Array in which all pixels of the same cluster are labeled with the same number.
        int
            Number of clusters found in the picture.
        """
        # in case it's not specified, take the default from init
        if min_std is None:
            min_std = self.min_std
        if min_size_cluster is None:
            min_size_cluster = self.min_size_cluster
        if max_gaps is None:
            max_gaps = self.max_gaps
        if isinstance(mask_mounting, bool):
            if mask_mounting:
                if len(self.camera.config.mask_mounting.shape) == len(self.images[0].shape) and \
                        np.all(np.array(self.camera.config.mask_mounting.shape) == np.array(self.images[0].shape)):
                    mask_mounting = self.camera.config.mask_mounting
                else:
                    print(f'Provided mask_mounting (shape: {self.camera.config.mask_mounting.shape}) has incompatible ',
                          f'shape to image (shape: {self.images[0].shape})')
                    mask_mounting = None
            else:
                mask_mounting = None
        elif isinstance(mask_mounting, np.ndarray):
            pass

        # create 2d-array with the deviation from mean in sigma for the selected picture
        dev = np.zeros_like(self.images[0], dtype=np.float64)
        mask = self.pixel_std != 0
        dev[mask] = (self.images[pic_index, mask] - self.pixel_mean[mask]) / self.pixel_std[mask]

        # create a map with values True if the deviation is >= min_std, else False
        z = dev >= min_std
        del dev

        if mask_mounting is not None:
            # all mask_mounting==False should be set to False in dev
            z[~mask_mounting] = 0

        # create structure to fill gaps according to max_distance.
        # scipy.ndimage.measurements.label can only detect direct neighbours
        # if max_gaps == 0:
        #     max_gaps = 1
        structure = np.ones((max_gaps * 2 + 1, max_gaps * 2 + 1), bool)
        structure[:max_gaps] = 0
        structure[:, :max_gaps] = 0
        z_dil = scipy.ndimage.binary_dilation(z, structure=structure).astype(bool)

        # convert the pixel beneath and the pixel to the right of each pixel with 'True' to 'True' as well to also
        # include pixels in clusters who are separated from the cluster by one dark pixel
        # define the structure of the clusters so that diagonal pixels are considered neighbours
        s = scipy.ndimage.generate_binary_structure(2, 2)

        # labeled_clusters_dil gives array with the number of the cluster the pixel is in
        # num_clusters is the number of clusters found in the picture
        # label 0 in labeled_cluster is where z_dil==False, in other words, label=0 is background
        labeled_cluster, num_clusters = scipy.ndimage.label(z_dil, structure=s)
        labeled_cluster[z == 0] = 0  # add all False in z to background (label 0)

        counts = np.bincount(labeled_cluster.astype(np.int64).flatten())
        counts = counts[labeled_cluster.astype(np.int64)].reshape((labeled_cluster.shape[0],
                                                                   labeled_cluster.shape[1]))

        # add too small cluster to label 0, in other words, remove the cluster and set is as background
        labeled_cluster[counts < min_size_cluster] = 0
        return labeled_cluster

    @staticmethod
    def get_box(mask_cluster):
        """Calculates the minimum box features of a 2D bool array covering all True values.
        The parameters returned are: box_center, box_size_x, box_size_y, and angle.

        PARAMETER
        ---------
        mask_cluster: ndarray
            2d bool array. The box represents the minimum box around all True values.

        EXAMPLE
        -------
        The corners of the bax can be calculated with openCV, i.e.:
        >>> box_dict = FindCluster.get_box(mask_cluster)
        >>> points = cv2.boxPoints(((box_dict['box_center_x'], box_dict['box_center_y']),
        >>>                         (box_dict['box_size_x'], box_dict['box_size_y']),
        >>>                         box_dict['angle']))
        """
        box = cv2.minAreaRect(np.argwhere(mask_cluster))
        return {'angle': float(box[2]),
                **{f'box_center_{l}': box[0][i] for i, l in enumerate(['x', 'y'])},
                **{f'box_size_{l}': box[1][i] for i, l in enumerate(['x', 'y'])},
                # 'box_corners': points
                }

    def get_sigma_deviation(self, pic_index, labels=None, index=None, color=None):
        """
        1. Compute absolute deviation from mean per pixel averaged over all pixels in the cluster.
        2. Compute deviation from mean in multiples of the standard deviation per pixel averaged
           over all pixels in the cluster.

        Parameters
        ----------
        pic_index : ndarray
            Index of the image in images.
        labels : array_like, optional
            Array of labels of same shape, or broadcastable to the same shape as
            `image`. All elements sharing the same label form one region over
            which the mean of the elements is computed.
        index : int or sequence of ints, optional
            Labels of the objects over which the mean is to be computed.
            Default is None, in which case the mean for all values where label is
            greater than 0 is calculated.
        color: None or str, optional
            allowed inputs are None or one strings of ['red', 'green', 'blue']. If a color is specified the statistic is
             computed for the pixel with the color, only.

        Returns
        -------
        mean_abs_dev: array, float
            Mean absolute deviation from mean.
        sigma_dev: array, float
            Mean deviation from mean in times of the standard deviation.
        """
        color_mask = None
        if color == 'red':
            color_mask = self.pixel_red_mask
        elif color == 'green':
            color_mask = self.pixel_green_mask
        elif color == 'blue':
            color_mask = self.pixel_blue_mask

        labels = labels[color_mask]
        index_present = np.unique(labels)  # unique labels which are present in labels (because of masking)
        _, ind, _ = np.intersect1d(index,  # all unique labels
                                   index_present,  # unique labels which are present in labels (because of masking)
                                   return_indices=True,  # returns the indexes of input arrays (here: ind, _)
                                   assume_unique=True)

        print(self.images[pic_index][color_mask], labels)

        # absolute deviation from mean for each pixel
        # abs_dev = np.abs(self.images[pic_index].astype(np.float64) - self.pixel_mean)
        abs_dev = self.images[pic_index][color_mask].astype(np.float64) - self.pixel_mean[color_mask]

        # mean absolute deviation for the cluster
        # np.nan if the label isn't in labels (because of masking)
        mean_abs_dev = np.zeros_like(index, dtype=float) + np.nan
        mean_abs_dev[ind] = scipy.ndimage.mean(abs_dev, labels=labels, index=index_present)

        abs_dev = abs_dev / np.ma.masked_equal(self.pixel_std[color_mask], 0)
        sigma_dev = np.zeros_like(index, dtype=float) + np.nan
        sigma_dev[ind] = scipy.ndimage.mean(abs_dev, labels=labels, index=index_present)

        return mean_abs_dev, sigma_dev

    def get_cluster_specs(self, pic_index, labels, index, color=None):
        """
        Parameters
        ----------
        pic_index : ndarray
            Index of the image in images.
        labels : array_like, optional
            Array of labels of same shape, or broadcastable to the same shape as
            `image`. All elements sharing the same label form one region over
            which the mean of the elements is computed.
        index : int or sequence of ints, optional
            Labels of the objects over which the mean is to be computed.
            Default is None, in which case the mean for all values where label is
            greater than 0 is calculated.
        color: None or str, optional
            allowed inputs are None or one strings of ['red', 'green', 'blue']. If a color is specified the statistic is
             computed for the pixel with the color, only.
        """
        color_mask = None
        if color == 'red':
            color_mask = self.pixel_red_mask
        elif color == 'green':
            color_mask = self.pixel_green_mask
        elif color == 'blue':
            color_mask = self.pixel_blue_mask

        labels_c = labels[color_mask]
        index_present = np.unique(labels_c)  # unique labels which are present in labels (because of masking)
        _, ind, _ = np.intersect1d(index,  # all unique labels
                                   index_present,  # unique labels which are present in labels (because of masking)
                                   return_indices=True,  # returns the indexes of input arrays (here: ind, _)
                                   assume_unique=True)
        image = self.images[pic_index][color_mask]

        # absolute deviation from mean for each pixel
        # abs_dev = np.abs(self.images[pic_index].astype(np.float64) - self.pixel_mean)
        abs_dev = image.astype(np.float64) - self.pixel_mean[color_mask]

        # mean absolute deviation for the cluster
        # np.nan if the label isn't in labels (because of masking)
        mean_abs_dev = np.zeros_like(index, dtype=float) + np.nan
        mean_abs_dev[ind] = scipy.ndimage.mean(abs_dev, labels=labels_c, index=index_present)

        abs_dev = abs_dev / np.ma.masked_equal(self.pixel_std[color_mask], 0)
        sigma_dev = np.zeros_like(index, dtype=float) + np.nan
        sigma_dev[ind] = scipy.ndimage.mean(abs_dev, labels=labels_c, index=index_present)

        # mean_abs_dev, sigma_dev = self.get_sigma_deviation(pic_index=pic_index,
        #                                                    labels=labels,
        #                                                    index=index,
        #                                                    color=color)

        n_pixel = np.zeros_like(index, dtype=int)
        n_pixel[ind] = scipy.ndimage.sum(np.ones_like(image, dtype=np.uint32),
                                         labels=labels_c,
                                         index=index_present)

        noise = np.zeros_like(index, dtype=float)
        noise[ind] = scipy.ndimage.sum(self.pixel_mean[color_mask],
                                       labels=labels_c,
                                       index=index_present)

        charge_with_noise = np.zeros_like(index, dtype=float) + np.nan
        charge_with_noise[ind] = scipy.ndimage.sum(image,
                                                   labels=labels_c,
                                                   index=index_present)

        color_str = ""
        if color is not None:
            color_str = f"_{color}"

        # sn: signal to noise
        specs_dict = {
            f'n_pixel{color_str}': n_pixel.astype(np.int32),
            f'noise{color_str}': noise,
            f'charge_with_noise{color_str}': charge_with_noise,
            f'sn_mean_deviation{color_str}': mean_abs_dev,
            f'sn_mean_deviation_sigma{color_str}': sigma_dev,
        }

        return specs_dict

    def df_picture(self, pic_index, min_std=None, min_size_cluster=None, max_gaps=None, mask_mounting=False):
        """
        Get DataFrame with properties of all clusters in a picture.

        Parameters
        ----------
        pic_index : int
            Number of the picture of which the data frame is created.
        min_std : int, optional
            Minimum multiple of the standard deviation for a pixel to be considered as bright. If None, take from init.
        min_size_cluster : int, optional
            Minimum number of adjoining pixels to be considered a cluster. If None, take from init.
        max_gaps: int, optional
            the maximum gap size within one cluster. If None, take from init.
        mask_mounting: bool or ndarray, optional
            True if the mounting, if known, should be excluded from the cluster search (mounting will be all label=0).
            An ndarray defines the mask which pixels should be excluded from the cluster search. Must match the pixel
            shape. `mask_mounting[i] = True` means include and `mask_mounting[i] = False` exclude the pixel i.

        Returns
        -------
        data frame
            Table with all clusters in the picture and their properties.
        """
        # in case its not specified, take the default from init
        if min_std is None:
            min_std = self.min_std
        if min_size_cluster is None:
            min_size_cluster = self.min_size_cluster

        labels = self.get_cluster(pic_index=pic_index,
                                  min_std=min_std,
                                  min_size_cluster=min_size_cluster,
                                  max_gaps=max_gaps,
                                  mask_mounting=mask_mounting)
        index = np.unique(labels)

        data_dict = self.get_cluster_specs(pic_index, labels, index, color=None)
        data_dict.update(self.get_cluster_specs(pic_index, labels, index, color='red'))
        data_dict.update(self.get_cluster_specs(pic_index, labels, index, color='green'))
        data_dict.update(self.get_cluster_specs(pic_index, labels, index, color='blue'))

        # center_of_mass = np.array(scipy.ndimage.measurements.center_of_mass(
        center_of_mass = np.array(scipy.ndimage.center_of_mass(
            self.images[pic_index] - self.pixel_mean,
            labels=labels,
            index=index))
        # center_of_pix = np.array(scipy.ndimage.measurements.center_of_mass(
        center_of_pix = np.array(scipy.ndimage.center_of_mass(
            np.ones_like(labels),
            labels=labels,
            index=index))

        df = pd.DataFrame(
            data={'time': asdatetime(self.camera.file_handler.time[pic_index]),
                  'label': index,
                  **{f'center_of_mass_{l}': center_of_mass[:, i] for i, l in enumerate(['x', 'y'])},
                  **{f'center_of_pix_{l}': center_of_pix[:, i] for i, l in enumerate(['x', 'y'])},
                  **data_dict,
                  })

        df_box = pd.json_normalize([self.get_box(labels == i) for i in index])
        df = df.merge(df_box, left_index=True, right_index=True)
        return df

    def df_all(self, pic_index=None, progressbar=None, tqdm_kwargs=None, *args, **kwargs):
        """Detect Cluster in multiple pictures.
        PARAMETERS
        ----------
        pic_index: list, ndarray, optional
            the indexes of the pictures to detect teh cluster. If None, take all
        progressbar: bool, optional
            if the loop should print a progressbae.
            It supports module tqdm: i.e. progressbar=tqdm.notebook.tqdm, or progressbar=tqdm.tqdm
        tqdm_kwargs: dict, optional
            kwargs for tqdm.notebook
        *args, **kwargs: list, dict, optional
            parsed to df_picture(...,*args, **kwargs)
        """
        if tqdm_kwargs is None:
            tqdm_kwargs = {}

        df = pd.DataFrame()

        if pic_index is None:
            pic_index = np.arange(self.images.shape[0])

        iterator = pic_index
        if progressbar is None:
            iterator = tqdm.tqdm(iterator, **tqdm_kwargs)
        elif not progressbar:
            iterator = progressbar(iterator, **tqdm_kwargs)

        # loop with or without progress bar
        for pic_i in iterator:
            df = df.append(self.df_picture(pic_index=pic_i, *args, **kwargs), ignore_index=True)
        return df
