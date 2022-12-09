import numpy as np
import pandas

import strawb
from strawb import Config
from strawb.sync_db_handler.base_db_handler import BaseDBHandler


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
            if f'charge{i}' not in self.dataframe:
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

        # only do the calculation for labels > 0; label=0 is not the cluster, its the rest of the image without clusters
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

        # only do the calculation for labels > 0; label=0 is not the cluster, its the rest of the image without clusters
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

        # only do the calculation for labels > 0; label=0 is not the cluster, its the rest of the image without clusters
        mask_label = self.dataframe.label > 0

        # the coordinates in x and y are flipped, see doc at `contours` calculation above
        pos_y[mask_label], pos_x[mask_label] = strawb.camera.get_nearest_points_line(
            self.dataframe.loc[mask_label, f'{coordinates}_y'],  # the coordinates in x and y are flipped, see above
            self.dataframe.loc[mask_label, f'{coordinates}_x'],  # the coordinates in x and y are flipped, see above
            line,  # point of the steel cable at the mounting
        ).T
        return pos_x, pos_y
