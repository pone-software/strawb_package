# Author: Kilian Holzapfel <kilian.holzapfel@tum.de>
import pandas

from strawb.base_file_handler import BaseFileHandler


class FileHandler(BaseFileHandler):
    def __init__(self, *args, **kwargs):
        """The File Handler of the PMTSpectrometer hdf5 data."""
        # positions of deployments, shape: n_pos
        self.latitude = None  # [degrees_north]: latitude - shape:(n_pos,)
        self.longitude = None  # [degrees_east]: longitude - shape:(n_pos,)

        # Profiler depth: shape: n_depth
        # Water depth of measurement bins corrected for tilt, applies to meanBackscatter (beam-averaged backscatter)
        self.depth = None  # [meters]: - shape:(n_depth,)
        # Water depth for the u (east), v (north), w (up), velocityError seawater velocity bins,
        # accounting for bin-mapping
        self.binmap_depth = None  # [meters]: - shape:(n_depth,)
        # Range of measurement bins from the transducer, applies to all parameters except:
        # meanBackscatter and u, v, w, velocityError when bin-mapping is on - shape:(n_depth,)
        self.range = None  # [meters]

        # 1d arrays - shape: n_measurements = n_m
        self.time = None  # [days since 19700101T000000Z]: time - shape:(n_m,)
        self.pitch = None  # [degrees]: pitch - shape:(n_m,)
        self.roll = None  # [degrees]: roll - shape:(n_m,)
        self.temperature = None  # [K]: sea water temperature - shape:(n_m,)

        # 2d arrays - shape: (n_measurements= n_m, n_depth)
        # acoustic doppler current profiler = ADCP
        self.corr_beam1 = None  # [counts]: ADCP correlation magnitude beam 1 - shape:(n_m, n_depth)
        self.corr_beam2 = None  # [counts]: ADCP correlation magnitude beam 2 - shape:(n_m, n_depth)
        self.corr_beam3 = None  # [counts]: ADCP correlation magnitude beam 3 - shape:(n_m, n_depth)
        self.corr_beam4 = None  # [counts]: ADCP correlation magnitude beam 4 - shape:(n_m, n_depth)
        self.intens_beam1 = None  # [counts]: ADCP return signal strength intensity beam 1 - shape:(n_m, n_depth)
        self.intens_beam2 = None  # [counts]: ADCP return signal strength intensity beam 2 - shape:(n_m, n_depth)
        self.intens_beam3 = None  # [counts]: ADCP return signal strength intensity beam 3 - shape:(n_m, n_depth)
        self.intens_beam4 = None  # [counts]: ADCP return signal strength intensity beam 4 - shape:(n_m, n_depth)

        self.percentGood_beam1 = None  # [percent]: ADCP percent good beam 1 - shape:(n_m, n_depth)
        self.percentGood_beam2 = None  # [percent]: ADCP percent good beam 2 - shape:(n_m, n_depth)
        self.percentGood_beam3 = None  # [percent]: ADCP percent good beam 3 - shape:(n_m, n_depth)
        self.percentGood_beam4 = None  # [percent]: ADCP percent good beam 4 - shape:(n_m, n_depth)

        # velocity
        self.w = None  # [meters/second]: upward sea water velocity - shape:(n_m, n_depth)
        self.u = None  # [meters/second]: eastward sea water velocity - shape:(n_m, n_depth)
        self.v = None  # [meters/second]: northward sea water velocity - shape:(n_m, n_depth)

        self.velocityError = None  # [meters/second]: ADCP error velocity - shape:(n_m, n_depth)
        self.velocity_beam1 = None  # [meters/second]: radial velocity beam 1 - shape:(n_m, n_depth)
        self.velocity_beam2 = None  # [meters/second]: radial velocity beam 2 - shape:(n_m, n_depth)
        self.velocity_beam3 = None  # [meters/second]: radial velocity beam 3 - shape:(n_m, n_depth)
        self.velocity_beam4 = None  # [meters/second]: radial velocity beam 4 - shape:(n_m, n_depth)

        # beam averaged and corrected for two-way beam spreading and attenuation,
        # not bin-mapped, use with tilt-corrected water depth
        self.meanBackscatter = None  # [dB]: - shape:(n_m, n_depth)

        # holds the file version
        self.file_version = None

        # comes last to load the data in case file_name is set
        BaseFileHandler.__init__(self, *args, **kwargs)

    def __load_meta_data__(self, ):
        err_list = []
        for i in [self.__load_meta_data_v1__]:
            try:
                i()  # try file versions
                return
            # version is detected because datasets in the hdf5 aren't present -> i() fails with KeyError
            except (TypeError, KeyError) as a:
                err_list.append(a.args[0])

        raise KeyError('; '.join(err_list))

    def __load_meta_data_v1__(self, ):
        """Standard version."""
        self.latitude = self.file['latitude']  # [degrees_north]
        self.longitude = self.file['longitude']  # [degrees_east]

        self.binmap_depth = self.file['binmap_depth']  # [meters]
        self.depth = self.file['depth']  # [meters]
        self.range = self.file['range']  # [meters]

        self.time = self.file['time']  # [days since 19700101T000000Z]
        self.temperature = self.file['temperature']  # [K]
        self.roll = self.file['roll']  # [degrees]
        self.pitch = self.file['pitch']  # [degrees]

        self.velocity_beam3 = self.file['velocity_beam3']  # [meters/second]
        self.velocity_beam2 = self.file['velocity_beam2']  # [meters/second]
        self.velocity_beam1 = self.file['velocity_beam1']  # [meters/second]
        self.velocityError = self.file['velocityError']  # [meters/second]
        self.v = self.file['v']  # [meters/second]
        self.u = self.file['u']  # [meters/second]
        self.percentGood_beam4 = self.file['percentGood_beam4']  # [percent]
        self.percentGood_beam2 = self.file['percentGood_beam2']  # [percent]
        self.velocity_beam4 = self.file['velocity_beam4']  # [meters/second]
        self.percentGood_beam1 = self.file['percentGood_beam1']  # [percent]
        self.meanBackscatter = self.file['meanBackscatter']  # [dB]
        self.intens_beam4 = self.file['intens_beam4']  # [counts]
        self.intens_beam3 = self.file['intens_beam3']  # [counts]
        self.intens_beam2 = self.file['intens_beam2']  # [counts]
        self.intens_beam1 = self.file['intens_beam1']  # [counts]
        self.corr_beam4 = self.file['corr_beam4']  # [counts]
        self.corr_beam3 = self.file['corr_beam3']  # [counts]
        self.corr_beam2 = self.file['corr_beam2']  # [counts]
        self.corr_beam1 = self.file['corr_beam1']  # [counts]
        self.percentGood_beam3 = self.file['percentGood_beam3']  # [percent]
        self.w = self.file['w']  # [meters/second]

        self.file_version = 1

    @property
    def velocity_east(self, ):
        """Eastward sea water velocity [meters/second]. Alias for `self.u`"""
        return self.u

    @property
    def velocity_north(self, ):
        """Northward sea water velocity [meters/second]. Alias for `self.v`"""
        return self.v

    @property
    def velocity_up(self, ):
        """Upward sea water velocity [meters/second]. Alias for `self.w`"""
        return self.w

    # Define pandas DataFrame export helpers
    def get_pandas_velocity(self):
        """Return a multi-index DataFrame. Use `df.reset_index(inplace=True)` to move the index as columns.
        Returns None, if file isn't defined or open."""
        if self.file is None:
            return None
        multi_index = pandas.MultiIndex.from_product(
            [(self.time[:] * 24 * 3600 * 1e9).astype('datetime64[ns]'),  # convert to ms
             self.depth[:]], names=['time', 'depth'])

        return pandas.DataFrame({'vel_east': self.velocity_east[:].flatten(),
                                 'vel_north': self.velocity_north[:].flatten(),
                                 'vel_up': self.velocity_up.flatten(),
                                 'vel_err': self.velocityError[:].flatten()},
                                index=multi_index)
