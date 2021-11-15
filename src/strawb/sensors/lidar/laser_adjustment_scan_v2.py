import numpy as np
from scipy.stats import binned_statistic
import strawb.sensors.lidar


class LaserAdjustmentScan:
    def __init__(self, file=None, lever_long=0.051, lever_short=0.038, rpm=31., delta_t_step=0.5, thread_steepness=0.002,
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

        phi_2d: ndarray(dtype=float, 11ndim=2, shape(steps_length,steps_length))
        theta_2d: ndarray(dtype=float, ndim=2, shape(steps_length,steps_length))
        pmt_counts_2d: ndarray(dtype=float, ndim=2, shape(steps_length,steps_length))

        """
        # TODO: add docs for parameters

        self.lidar = strawb.sensors.lidar.Lidar(file=file)
        # ---- Parameters from the hdf5 - file ----
        self.steps = None
        self.steps_length = None
        self.signal = None
        self.step_positions = None

        # ---- Parameters for the Geometry ----
        self.rps = rpm / 60.  # [1/s] rotations per second
        self.delta_t_step = delta_t_step
        self.thread_steepness = thread_steepness
        self.efficiency = efficiency
        self.x_1 = np.array([[lever_short, 0, 0]])  # [m]; x Position stepper
        self.x_2 = np.array([[0, lever_long, 0]])  # [m]; y Position stepper
        self.v_motor = np.array([[0, 0, self.dx]])  # the vector per motor-step

        # TODO: add docs for parameters
        # ---- Computed variables ----
        self.offset = None
        self._theta = None
        self._phi = None

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

    def extract_measurements(self):
        """
        calls self.get_signal(), self.get_step_positions(), and assigns it to class variables, also returns the result
        :return:
        self.positions: ndarray(dtype=float, ndim=2, shape(steps_length,2))
        self.signal: ndarray(dtype=float, ndim=1, shape(steps_length))
        """
        self.signal = self.get_signal()
        self.step_positions = self.get_step_positions()

        return self.step_positions, self.signal

    def get_signal(self):
        """
        Get middle of Timestamps of trb readout. than sum the corresponding counts of PMT and laser in
        binned_statistics, only take every second element, due to bins from measurement_time. assign self.signal
        counts_pmt/counts_laser.
        :return:
        self.signal: ndarray(dtype=float, ndim=1, shape(steps_length))
        """
        # ---- get data for signal ----
        abs_timestamp_middle = (self.lidar.file_handler.counts_time[:-1]
                                + self.lidar.file_handler.counts_time[1:]) * 0.5

        bin_counts_pmt, bin_edges, binnumber = binned_statistic(
            abs_timestamp_middle,
            self.lidar.trb_rates.dcounts_pmt,
            statistic='sum',
            bins=self.lidar.file_handler.measurement_time)

        bin_counts_laser, bin_edges, binnumber = binned_statistic(
            abs_timestamp_middle,
            self.lidar.trb_rates.dcounts_laser,
            statistic='sum',
            bins=self.lidar.file_handler.measurement_time)

        bin_counts_pmt = bin_counts_pmt[::2]  # every second to not count data from between steps
        bin_counts_laser = bin_counts_laser[::2]

        signal = bin_counts_pmt / bin_counts_laser

        return signal

    def get_step_positions(self):
        """
        Gets the steps from the hdf5-file, remove "duplicate" values in the array and returns it as 2d array
        eg. for 1d array: [0,0,0,1,1,0,0,0,0,-1,-1,-1] => [0,1,0,-1]
        Is done for both direction separately and combined in the end

        IMPORTANT: Only works for spirals!

        :return:
        self.positions: ndarray(dtype=float, ndim=2, shape(steps_length,2))
        """
        try:
            self.steps = self.lidar.file_handler.file_attributes["mes_steps"]
        except KeyError:
            self.steps = self.lidar.file_handler.file_attributes["measurement_steps"]

        self.steps_length = int(2 * self.steps + 1)

        laser_steps_x = np.array(self.lidar.file_handler.laser_set_adjust_x)
        laser_steps_y = np.array(self.lidar.file_handler.laser_set_adjust_y)

        change_x = np.where(np.diff(laser_steps_x))[0]
        change_y = np.where(np.diff(laser_steps_y))[0]

        steps_x = laser_steps_x[change_x]
        steps_y = laser_steps_y[change_y]

        step_positions = np.zeros((self.steps_length ** 2, 2))

        step_positions[:, 0] = steps_x[:self.steps_length ** 2]  # cut because laser moves back to (0,0) after last pos
        step_positions[:, 1] = steps_y[:self.steps_length ** 2]

        return step_positions

    def compute_maximum_position(self):
        """
        finds the maximum of the self.signal array, assigns it to an offset variable and returns the corresponding steps
        :return:
        max_steps: ndarray(dtype=float, ndim=1, len=2)
        """
        index = np.max(self.signal)
        max_step_positions = self.step_positions[index]
        self.offset = max_step_positions

        return max_step_positions

    def convert_to_angles(self, step_position, offset=None):
        """
        gets a step and an offset as an input. Subtracts offset from steps and converts it to angles
        :param step_position:
        :param offset:
        :return:
        """
        # step_position -= offset

        n = np.cross(self.x_1 + self.v_motor * step_position[:, 0].reshape(-1, 1),
                     self.x_2 + self.v_motor * step_position[:, 1].reshape(-1, 1))

        theta = np.arccos(n[:, 2] / np.sqrt(np.sum(n ** 2, axis=-1)))
        phi = np.arctan2(n[:, 1], n[:, 0]) + np.pi

        return phi, theta

    @property
    def phi(self):
        if self._phi is None and self.step_positions is not None:
            self._phi, self._theta = self.convert_to_angles(step_position=self.step_positions)
        return self._phi

    @property
    def theta(self):
        if self._theta is None and self.step_positions is not None:
            self._phi, self._theta = self.convert_to_angles(step_position=self.step_positions)
        return self._theta
