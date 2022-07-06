import numpy as np
import pandas

from strawb.sensors.adcp.file_handler import FileHandler
import strawb.tools


class BaseCurrent:
    def __init__(self,):
        """Class to calculate and store current data, e.g. from an ADCP.
         The data are stored in 2d arrays, where the first axis is the time and the second the depth."""
        self._phi = None
        self._theta = None
        self._velocity_abs = None
        self._timestamp_ = None
        self._depth_ = None

    def set_velocities(self, velocity_east, velocity_north, velocity_up):
        """Set the currents with cartesian data: velocity_east, velocity_north, velocity_up."""
        self._phi = np.ma.arctan2(velocity_east, velocity_north)
        self._phi[self._phi < 0] += 2 * np.pi

        self._velocity_abs = np.ma.sqrt(np.ma.sum([velocity_east[:] ** 2,
                                                   velocity_north[:] ** 2,
                                                   velocity_up[:] ** 2], axis=0))

        self._theta = np.zeros_like(velocity_up)
        mask = self._velocity_abs != 0
        self._theta[mask] = np.ma.arccos(velocity_up[mask] / self._velocity_abs[mask])
        self._theta[~mask] = 0

    def set_polar(self, velocity_abs, theta, phi):
        """Set the currents with polar data: velocity_abs, theta, phi."""
        self._phi = phi
        self._theta = theta
        self._velocity_abs = velocity_abs

    @property
    def time(self):
        """The absolute timestamp as datetime."""
        return strawb.tools.asdatetime(self.timestamp)

    @property
    def timestamp(self):
        """The absolute timestamp as seconds since epoch."""
        return self._timestamp_

    @property
    def depth(self):
        """The absolute timestamp as seconds since epoch."""
        return self._depth_

    @property
    def phi(self):
        """Theta of velocity. Phi=0 -> north, Phi=np.pi/2.=east, Phi=np.pi=south,"""
        return self._phi

    @property
    def theta(self, ):
        """Theta of velocity. Theta=0 -> upwards, Theta=np.pi=downwards."""
        return self._theta

    @property
    def velocity_abs(self, ):
        """Absolute velocity in m/s"""
        return self._velocity_abs

    @property
    def velocity_east(self):
        """Velocity in eastern direction. m/s"""
        return np.ma.sin(self.phi) * np.ma.sin(self.theta) * self.velocity_abs

    @property
    def velocity_north(self):
        """Velocity in northern direction. m/s"""
        return np.ma.cos(self.phi) * np.ma.sin(self.theta) * self.velocity_abs

    @property
    def velocity_up(self):
        """Velocity in upwards direction. m/s"""
        return np.ma.cos(self.theta) * self.velocity_abs


class CurrentData(BaseCurrent):
    def __init__(self, timestamp, depth=None,
                 velocity_east=None, velocity_north=None, velocity_up=None,
                 velocity_abs=None, theta=None, phi=None):
        """Class to calculate and store current data, e.g. from an ADCP. The data are stored in 2d arrays, where the
        first axis is the time and the second the depth. The values itself can be set either by
        velocity_east, velocity_north, velocity_up or velocity_abs, theta, phi
        (all are 2d arrays with the described axis)"""
        BaseCurrent.__init__(self,)

        self._timestamp_ = timestamp
        self._depth_ = depth

        if all([velocity_east is not None, velocity_north is not None, velocity_up is not None]):
            self.set_velocities(velocity_east=velocity_east, velocity_north=velocity_north, velocity_up=velocity_up)
        elif any([velocity_abs is None, theta is None, phi is None]):
            raise KeyError(f'Either all of [velocity_east, velocity_north, velocity_up] or \
                             all of [velocity_abs, theta, phi] must be set.')
        else:
            self.set_polar(velocity_abs=velocity_abs, theta=theta, phi=phi)


class CurrentFile(BaseCurrent):
    def __init__(self, file_handler: FileHandler):
        """Class to calculate and store current data, e.g. from an ADCP. The data are stored in 2d arrays, where the
        first axis is the time and the second the depth. The values are read from the file directly.
        """
        BaseCurrent.__init__(self,)

        if isinstance(file_handler, FileHandler):
            self.file_handler = file_handler
        else:
            raise TypeError(f"Expected `strawb.sensors.adcp.FileHandler` got: {type(file_handler)}")

    @property
    def timestamp(self):
        """The absolute timestamp as seconds since epoch."""
        if self.file_handler.time is None:
            return None
        if self._timestamp_ is None:
            self._timestamp_ = self.file_handler.time[:] * 24. * 3600.
        return self._timestamp_

    @property
    def depth(self):
        """The absolute timestamp as seconds since epoch."""
        if self.file_handler.depth is None:
            return None
        if self._depth_ is None:
            # max_shape because virtual hdf5 adds extends the depth. Take only the first entries.
            max_shape = self.file_handler.velocity_east.shape[-1]
            self._depth_ = self.file_handler.depth[:max_shape] * 24. * 3600.
        return self._depth_

    @property
    def time(self):
        """The absolute timestamp as datetime."""
        if self.file_handler.time is None:
            return None
        return strawb.tools.asdatetime(self.timestamp)

    @property
    def velocity_abs(self, ):
        """Absolute velocity"""
        if self._velocity_abs is None:
            self.set_velocities(velocity_east=self.file_handler.velocity_east[:],
                                velocity_north=self.file_handler.velocity_north[:],
                                velocity_up=self.file_handler.velocity_up[:])
        return self._velocity_abs

    @property
    def theta(self, ):
        """Theta of velocity. Theta=0 -> upwards, Theta=np.pi=downwards."""
        if self._theta is None:
            self.set_velocities(velocity_east=self.file_handler.velocity_east[:],
                                velocity_north=self.file_handler.velocity_north[:],
                                velocity_up=self.file_handler.velocity_up[:])
        return self._theta

    @property
    def phi(self, ):
        """Phi of velocity. phi=0 -> north, phi=np.pi -> south"""
        if self._phi is None:
            self.set_velocities(velocity_east=self.file_handler.velocity_east[:],
                                velocity_north=self.file_handler.velocity_north[:],
                                velocity_up=self.file_handler.velocity_up[:])
        return self._phi

    def get_dataframe(self, ):
        # convert to pandas.DataFrame with MultiIndex (2D indexing)
        multi_index = pandas.MultiIndex.from_product([self.time, self.file_handler.depth[:]])

        return pandas.DataFrame({'vel_east': self.velocity_abs,
                                 'theta': self.theta,
                                 'phi': self.phi},
                                index=multi_index)
