import numpy as np
import pandas

from strawb.sensors.adcp import FileHandler


class Current:
    def __init__(self, file_handler: FileHandler):
        """A class to calculate basic current parameters from a ADCP (AcousticDopplerCurrentProfiler)"""
        if isinstance(file_handler, FileHandler):
            self.file_handler = file_handler
        else:
            raise TypeError(f"Expected `strawb.sensors.adcp.FileHandler` got: {type(file_handler)}")

        # properties store
        self._vel_abs = None
        self._theta = None
        self._phi = None

    @property
    def time(self):
        """The absolute timestamp as datetime."""
        if self.file_handler.time is None:
            return None
        return self.file_handler.time.asdatetime(scale2seconds=24. * 3600.)

    @property
    def velocity_abs(self, ):
        """Absolute velocity"""
        if self._vel_abs is None:
            self._vel_abs = np.sqrt(np.sum([self.file_handler.velocity_east[:] ** 2,
                                            self.file_handler.velocity_north[:] ** 2,
                                            self.file_handler.velocity_up[:] ** 2], axis=0))
        return self._vel_abs

    @property
    def theta(self, ):
        """Theta of velocity. Theta=0 -> upwards, Theta=np.pi=downwards."""
        if self._theta is None:
            self._theta = np.arccos(self.file_handler.velocity_up[:] / self.velocity_abs)
        return self._theta

    @property
    def phi(self, ):
        """Theta of velocity. Theta=0 -> upwards, Theta=np.pi=downwards."""
        if self._phi is None:
            self._phi = np.ma.arctan2(self.file_handler.velocity_east[:],
                                      self.file_handler.velocity_north[:])
            self._phi[self._phi < 0] += 2 * np.pi
        return self._phi

    def get_dataframe(self, ):
        # convert to pandas.DataFrame with MultiIndex (2D indexing)
        multi_index = pandas.MultiIndex.from_product([self.time, self.file_handler.depth[:]])

        return pandas.DataFrame({'vel_east': self.velocity_abs,
                                 'theta': self.theta,
                                 'phi': self.phi},
                                index=multi_index)
