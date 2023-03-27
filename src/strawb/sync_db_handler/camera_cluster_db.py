import cv2
import numpy as np
import pandas

import strawb
from strawb import Config
from strawb.sync_db_handler.base_db_handler import BaseDBHandler
import strawb.sensors.camera.config


class ImageClusterDB(BaseDBHandler):
    # set defaults
    _default_raw_data_dir_ = Config.raw_data_dir
    _default_file_name_ = None  # there is no default

    def __init__(self, file_name, device_code, update=False, load_db=True):
        """Handle a cluster DB stored as a `pandas.DataFrame` in `self.dataframe`.
        PARAMETER
        ---------
        file_name: Union[str, None], optional
            If None, it doesn't load the DB. If it is a string, it can be:
            - the full path to the DB
            - a relative path to the DB
        device_code: str
            the device_code of the module where the camera is located, i.e.
            'TUMPMTSPECTROMETER001', 'TUMPMTSPECTROMETER002', or 'TUMMINISPECTROMETER001'
        update: bool, optional
            defines if the entries should be checked against existing files
        load_db: bool, update
            True (default) loads the DB if it exists and if `file_name` is not None. False doesn't load it.
        """
        BaseDBHandler.__init__(self, file_name=file_name, update=update, load_db=load_db, search_file=False)

        # check if valid device_code
        assert device_code in ['TUMPMTSPECTROMETER001', 'TUMPMTSPECTROMETER002', 'TUMMINISPECTROMETER001']
        self.device_code = device_code

        # directly add the charge, doesn't need long
        if self.dataframe is not None:
            self.add_charge()

        self.cam_config = strawb.sensors.camera.config.Config(device_code=device_code)

    def save_db(self):
        # remove the extra columns again to save space
        for i in ['charge', 'charge_red', 'charge_blue', 'charge_green']:
            if i in self.dataframe:
                self.dataframe.pop(i)
        BaseDBHandler.save_db(self)
        self.add_charge()  # and add it back

    def update(self, force=False, coordinates='center_of_pix', verbose=1):
        """
        PARAMETER
        ---------
        force: bool
            if existing columns should be calculated new, default False
        coordinates
            define which coordinates to use for the distance calculations, must be one of:
             ['center_of_mass', 'box_center', 'center_of_pix']
        verbose: int
            values >0 print process information
        """
        assert coordinates in ['center_of_mass', 'box_center', 'center_of_pix']
        self.add_charge()
        if 'distance_fov' not in self.dataframe or force:
            if verbose > 0:
                print('calculate distance_fov')
            self.dataframe['distance_fov'] = self.get_distance_fov(coordinates=coordinates)

        if 'distance_cable' not in self.dataframe or force:
            if verbose > 0:
                print('calculate distance_cable')
            self.dataframe['distance_cable'] = self.get_distance_cable(coordinates=coordinates)

        if ('nearest_point_cable_x' not in self.dataframe) or ('nearest_point_cable_y' not in self.dataframe) or force:
            if verbose > 0:
                print('calculate nearest_point_cable (_x, _y)')
            x, y = self.get_nearest_point_cable(coordinates=coordinates)
            self.dataframe['nearest_point_cable_x'] = x
            self.dataframe['nearest_point_cable_y'] = y

    def add_charge(self):
        """Adds new columns for charge based on charge_with_noise-noise also for the colors"""
        for i in ['', '_red', '_blue', '_green']:
            if f'charge{i}' not in self.dataframe and \
                    f'charge_with_noise{i}' in self.dataframe and \
                    f'noise{i}' in self.dataframe:
                self.dataframe[f'charge{i}'] = self.dataframe[f'charge_with_noise{i}'] - self.dataframe[f'noise{i}']

    def get_distance_fov(self, coordinates='center_of_pix'):
        """ Get the distance to the fov for the given coordinate system. Negative means inside the fov, positive
        outside.
        PARAMETER
        ---------
        coordinates
            define which coordinates to use for the calculation, must be one of:
             ['center_of_mass', 'box_center', 'center_of_pix']
        """
        assert coordinates in ['center_of_mass', 'box_center', 'center_of_pix']

        # camera config class
        cam_conf = strawb.camera.Config(self.device_code)
        # mounting contour, in contours it is contours[0]=[[y, x],...] as the first dimension of the mask represents y
        # and not x
        contours, hierarchy = strawb.camera.get_contours_simplify(cam_conf.mask_mounting)

        # create pandas.Series filled with nans
        distance = pandas.Series(data=np.nan, index=self.dataframe.index)

        # only do the calculation for labels > 0; label=0 is not the cluster, it's the image's rest without clusters
        mask_label = self.dataframe.label > 0

        # the coordinates in x and y are flipped, see doc at `contours` calculation above
        distance[mask_label] = strawb.camera.get_distances_poly(
            self.dataframe.loc[mask_label, f'{coordinates}_y'],  # the coordinates in x and y are flipped, see above
            self.dataframe.loc[mask_label, f'{coordinates}_x'],  # the coordinates in x and y are flipped, see above
            contours[0]  # the polygon
        )
        return distance

    def get_distance_cable(self, coordinates='center_of_pix'):
        """ Get the distance to the cable for the given coordinate system. The distance is >=0
        PARAMETER
        ---------
        coordinates
            define which coordinates to use for the calculation, must be one of:
             ['center_of_mass', 'box_center', 'center_of_pix']
        """
        assert coordinates in ['center_of_mass', 'box_center', 'center_of_pix']

        # camera config class
        cam_conf = strawb.camera.Config(self.device_code)
        # the line
        line = np.array([cam_conf.position_data_cable,  # point of the data cable at the mounting
                         cam_conf.position_module,  # point of the module above
                         cam_conf.position_steel_cable])  # point of the steel cable at the mounting

        # create pandas.Series filled with nans
        distance = pandas.Series(data=np.nan, index=self.dataframe.index)

        # only do the calculation for labels > 0; label=0 is not the cluster, it's the image's rest without clusters
        mask_label = self.dataframe.label > 0

        # the coordinates in x and y are flipped, see doc at `contours` calculation above
        distance[mask_label] = strawb.camera.get_distances_line(
            self.dataframe.loc[mask_label, f'{coordinates}_y'],  # the coordinates in x and y are flipped, see above
            self.dataframe.loc[mask_label, f'{coordinates}_x'],  # the coordinates in x and y are flipped, see above
            line  # the line
        )
        return distance

    def get_nearest_point_cable(self, coordinates='center_of_pix'):
        """ Get the distance to the cable for the given coordinate system. The distance is >=0
        PARAMETER
        ---------
        coordinates
            define which coordinates to use for the calculation, must be one of:
             ['center_of_mass', 'box_center', 'center_of_pix']
        """
        assert coordinates in ['center_of_mass', 'box_center', 'center_of_pix']

        # camera config class
        cam_conf = strawb.camera.Config(self.device_code)
        # the line
        line = np.array([cam_conf.position_data_cable,  # point of the data cable at the mounting
                         cam_conf.position_module,  # point of the module above
                         cam_conf.position_steel_cable])  # point of the steel cable at the mounting

        # create pandas.Series filled with nans
        pos_x = pandas.Series(data=np.nan, index=self.dataframe.index)
        pos_y = pandas.Series(data=np.nan, index=self.dataframe.index)

        # only do the calculation for labels > 0; label=0 is not the cluster, it's the image's rest without clusters
        mask_label = self.dataframe.label > 0

        # the coordinates in x and y are flipped, see doc at `contours` calculation above
        pos_y[mask_label], pos_x[mask_label] = strawb.camera.get_nearest_points_line(
            self.dataframe.loc[mask_label, f'{coordinates}_y'],  # the coordinates in x and y are flipped, see above
            self.dataframe.loc[mask_label, f'{coordinates}_x'],  # the coordinates in x and y are flipped, see above
            line,  # point of the steel cable at the mounting
        ).T
        return pos_x, pos_y

    def add_classes(self, distance_cable=100, distance_fov=10):
        """Split cluster into some basic classes. There are two types of classes,
        where each cluster is individually labeled:
        - 'cable': clusters within the maximum distance from the cables ('distance_cable')
                   and in the module's FoV
        - 'fov'  : clusters which are inside the module's FoV and are not in the class 'cable'
        - 'noise': clusters which are outside the module's FoV
        and where all clusters of one picture are labeled if it matches the condition
        - 'invalid': if at least one cluster has greater dimensions as the module's FoV
        - 'flash'  : if the flasher LEDs have been enabled for that picture.
                     Flasher LEDs are located in the same modules as the camera and work like a normal flash
        - 'led'    : if the LEDs in the neighboring module are enabled
        """
        # label cluster classes: 'cable', 'fov', 'noise'
        mask_label = (self.dataframe.label > 0)  # don't label the label 0

        self.dataframe['class'] = ''
        # the label order is important: 'fov', 'cable', 'noise'!
        # distance_fov is negative if it is inside
        self.dataframe.loc[mask_label & (self.dataframe.distance_fov < distance_fov), 'class'] = 'fov'
        # distance_cable is not negative as there can't be a cluster inside
        self.dataframe.loc[mask_label &
                           (self.dataframe.distance_cable < distance_cable) &
                           (self.dataframe.distance_fov < 0), 'class'] = 'cable'
        # all clusters outside the module's fov
        self.dataframe.loc[mask_label & (self.dataframe.distance_fov >= distance_fov), 'class'] = 'noise'

        # label image classes: 'invalid', 'flash', 'led'
        # 'invalid': mask too big cluster that have greater dimensions as the fov and
        rect = cv2.minAreaRect(np.argwhere(self.cam_config.mask_mounting))  # get dimensions
        mask_box = self.dataframe.box_size_x > rect[1][0]
        mask_box |= self.dataframe.box_size_y > rect[1][1]
        # when one cluster is too big, mask also all cluster in the same picture
        mask_box = self.dataframe.time.isin(self.dataframe[mask_box & mask_label].time)
        self.dataframe.loc[mask_box, 'class'] = 'invalid'

        # 'flash', 'led': mask cluster with enabled LED and label them as valid
        mask_led_module = self.dataframe.luciver_deviceCode == self.device_code
        self.dataframe.loc[~self.dataframe.option_tag.isna() & mask_led_module, 'class'] = 'flash'
        self.dataframe.loc[~self.dataframe.option_tag.isna() & ~mask_led_module, 'class'] = 'led'
