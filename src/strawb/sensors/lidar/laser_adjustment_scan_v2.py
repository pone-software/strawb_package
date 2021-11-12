import numpy as np
from scipy.stats import binned_statistic
import strawb.sensors.lidar


class LaserAdjustmentScan:
    def __init__(self, file, lever_long=0.051, lever_short=0.038, rpm=31., delta_t_step=0.5, thread_steepness=0.002,
                 efficiency=0.5):
        """
        TODO: add doc-string
        PARAMETER
        ---------
        file: string, absolut filepath to the hdf5-file
        lever_long: float, longer distance from fixed screw to connection point of one of the motors
        lever_short: float, shorter distance from fixed screw to connection point of one of the motors
        rpm: float, optional [1/min] rotations per minute
        delta_t_step: float, [s] seconds the motor moves per step
        thread_steepness: float, [m], thread steepness (distance per rotation)
        efficiency: float, the motor moves slow with friction, e.g. 50% slower -> .5

        phi_2d: ndarray(dtype=float, ndim=2, shape(steps_length,steps_length))
        theta_2d: ndarray(dtype=float, ndim=2, shape(steps_length,steps_length))
        pmt_counts_2d: ndarray(dtype=float, ndim=2, shape(steps_length,steps_length))

        """
        # TODO: add docs for parameters
        self.file = file
        #  Parameters from the hdf5 - file
        self.steps = None
        self.steps_length = None
        self.signal = 0
        self.step_positions = None

        self.rps = rpm / 60.  # [1/s] rotations per second
        self.delta_t_step = delta_t_step
        self.thread_steepness = thread_steepness
        self.efficiency = efficiency

        self.x_1 = np.array([[lever_short, 0, 0]])  # [m]; x Position stepper
        self.x_2 = np.array([[0, lever_long, 0]])  # [m]; y Position stepper
        self.v_motor = np.array([[0, 0, self.dx]])  # the vector per motor-step

        # TODO: add docs for parameters
        self.phi_2d = None
        self.theta_2d = None
        self.pmt_counts_2d = None

    @property
    def dx(self):
        """Distance in meter [m] per rotation."""
        return self.rps * self.delta_t_step * self.thread_steepness * self.efficiency  # [m] distance per rotation

    @property
    def rpm(self):
        """The rotations per minute of the motor."""
        return self.rps * 60.  # [1/min] rotations per min

    @rpm.setter
    def rpm(self, value):
        """Sets the rotations per minute of the motor.
        PARAMETER
        ---------
        value: float
            rotations per minute in unit [1/m]
        """
        self.rps = value / 60.  # [1/m] -> [1/s] rotations per second

    def extract_measurments(self):
        lidar = strawb.sensors.lidar.Lidar(file=self.file)

        #

