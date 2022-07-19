import numpy as np
import scipy.ndimage
import cv2
import pandas as pd
import tqdm.notebook


class FindCluster:
    def __init__(self, camera, min_std=3, min_size_cluster=3, max_gaps=2,
                 pixel_mean=None, pixel_std=None, images=None):
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
        """

        self.camera = camera
        self._images_ = images

        self.min_std = min_std
        self.min_size_cluster = min_size_cluster
        self.max_gaps = max_gaps

        # mean brightness & standard deviation per pixel averaged over all available pictures
        self._pixel_mean_ = pixel_mean
        self._pixel_std_ = pixel_std

    def __del__(self):
        """Remove links to other classes to prevent deadlock."""
        del self._images_
        del self._pixel_mean_
        del self._pixel_std_
        del self.camera

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
            self._images_ = self.camera.images.cut2effective_pixel(self._images_)
        return self._images_

    @images.setter
    def images(self, value):
        self._images_ = value

    def get_cluster(self, pic_index, min_std=None, min_size_cluster=None, max_gaps=None):
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
        Returns
        -------
        numpy.ndarray
            Array in which all pixels of the same cluster are labeled with the same number.
        int
            Number of clusters found in the picture.
        """
        # in case its not specified, take the default from init
        if min_std is None:
            min_std = self.min_std
        if min_size_cluster is None:
            min_size_cluster = self.min_size_cluster
        if max_gaps is None:
            max_gaps = self.max_gaps

        # create 2darray with the deviation from mean in sigma for the selected picture
        dev = np.zeros_like(self.images[0], dtype=np.float64)
        mask = self.pixel_std != 0
        dev[mask] = (self.images[pic_index, mask] - self.pixel_mean[mask]) / self.pixel_std[mask]

        # create structure to fill gaps according to max_distance.
        # scipy.ndimage.measurements.label can only detect direct neighbours
        structure = np.ones((max_gaps * 2 - 1, max_gaps * 2 - 1), bool)
        structure[:max_gaps - 1] = 0
        structure[:, :max_gaps - 1] = 0

        z = dev >= min_std  # create a map with values True if the deviation is >= min_std, else False
        z_dil = scipy.ndimage.binary_dilation(z, structure=structure).astype(bool)

        # convert the pixel beneath and the pixel to the right of each pixel with 'True' to 'True' as well to also
        # include pixels in clusters who are separated from the cluster by one dark pixel
        # define the structure of the clusters so that diagonal pixels are considered neighbours
        s = scipy.ndimage.generate_binary_structure(2, 2)

        labeled_cluster, num_clusters = scipy.ndimage.measurements.label(z_dil, structure=s)
        # labeled_clusters_dil gives array with the number of the cluster the pixel is in
        # num_clusters is the number of clusters found in the picture
        labeled_cluster[z == 0] = 0

        counts = np.bincount(labeled_cluster.astype(np.int64).flatten())
        counts = counts[labeled_cluster.astype(np.int64)].reshape((labeled_cluster.shape[0],
                                                                   labeled_cluster.shape[1]))

        labeled_cluster[counts < min_size_cluster] = 0
        return labeled_cluster

    @staticmethod
    def get_box(mask_cluster):
        box = cv2.minAreaRect(np.argwhere(mask_cluster))

        # coordinates of the corners of the minimal bounding rectangle
        points = cv2.boxPoints(box).astype(np.float64)

        return {'angle': box[2],
                'box_center': box[0],
                'box_size': box[1],
                'box_corners': points}

    def get_sigma_deviation(self, pic_index, labels=None, index=None):
        """
        1. Compute absolute deviation from mean per pixel averaged over all pixels in the cluster.
        2. Compute deviation from mean in multiples of the standard deviation per pixel averaged
           over all pixels in the cluster.

        Parameters
        ----------
        pic_index : int
            Number of the picture of which the data frame is created.
        labels : array_like, optional
            Array of labels of same shape, or broadcastable to the same shape as
            `input`. All elements sharing the same label form one region over
            which the mean of the elements is computed.
        index : int or sequence of ints, optional
            Labels of the objects over which the mean is to be computed.
            Default is None, in which case the mean for all values where label is
            greater than 0 is calculated.

        Returns
        -------
        mean_abs_dev: array, float
            Mean absolute deviation from mean.
        sigma_dev: array, float
            Mean deviation from mean in times of the standard deviation.
        """
        # absolute deviation from mean for each pixel
        # abs_dev = np.abs(self.images[pic_index].astype(np.float64) - self.pixel_mean)
        abs_dev = self.images[pic_index].astype(np.float64) - self.pixel_mean

        # mean absolute deviation for the cluster
        mean_abs_dev = scipy.ndimage.measurements.mean(abs_dev, labels=labels, index=index)

        abs_dev = abs_dev / np.ma.masked_equal(self.pixel_std, 0)
        sigma_dev = scipy.ndimage.measurements.mean(abs_dev, labels=labels, index=index)

        return mean_abs_dev, sigma_dev

    def df_picture(self, pic_index, min_std=None, min_size_cluster=None, max_gaps=None):
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

        labeled_cluster = self.get_cluster(pic_index=pic_index,
                                           min_std=min_std,
                                           min_size_cluster=min_size_cluster,
                                           max_gaps=max_gaps)
        unique_labeled_cluster, n_pixel = np.unique(labeled_cluster, return_counts=True)

        mean_abs_dev, sigma_dev = self.get_sigma_deviation(pic_index=pic_index,
                                                           labels=labeled_cluster,
                                                           index=unique_labeled_cluster)

        df = pd.DataFrame(
            data={'time': self.camera.file_handler.time.asdatetime()[pic_index],
                  'label': unique_labeled_cluster,
                  'n_pixel': n_pixel,
                  'charge_with_noise': scipy.ndimage.measurements.sum(self.images[pic_index],
                                                                      labels=labeled_cluster,
                                                                      index=unique_labeled_cluster),
                  'noise': scipy.ndimage.measurements.sum(self.pixel_mean,
                                                          labels=labeled_cluster,
                                                          index=unique_labeled_cluster),
                  'mean_absolute_deviation_per_pixel': mean_abs_dev,
                  'mean_deviation_per_pixel_in_sigma': sigma_dev,
                  'center_of_mass': scipy.ndimage.measurements.center_of_mass(
                      self.images[pic_index] - self.pixel_mean,
                      labels=labeled_cluster,
                      index=unique_labeled_cluster),
                  'center_of_pix': scipy.ndimage.measurements.center_of_mass(
                      np.ones_like(labeled_cluster),
                      labels=labeled_cluster,
                      index=unique_labeled_cluster),
                  'angle': None,
                  'box_center': None,
                  'box_size': None,
                  'box_corners': None,
                  })

        df_box = pd.json_normalize([self.get_box(labeled_cluster == i) for i in unique_labeled_cluster])
        df.update(df_box)

        return df

    def df_all(self, pic_index=None, *args, **kwargs):
        """Detect Cluster in multiple pictures.
        PARAMETERS
        ----------
        pic_index: list, ndarray, optional
            the indexes of the pictures to detect teh cluster. If None, take all
        *args, **kwargs: list, dict, optional
            parsed to df_picture(...,*args, **kwargs)
        """
        df = pd.DataFrame()

        if pic_index is None:
            pic_index = np.arange(self.images.shape[0])

        # loop with progress bar
        for pic_i in tqdm.notebook.tqdm(pic_index):
            df = df.append(self.df_picture(pic_index=pic_i, *args, **kwargs), ignore_index=True)
        return df
