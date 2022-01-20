import numpy as np
from scipy.stats import binned_statistic
import strawb.sensors.lidar


class LaserAdjustmentScan:
    def __init__(self, file=None, lever_long=0.051, lever_short=0.038, rpm=31., delta_t_step=0.5,
                 thread_steepness=0.002, efficiency=0.5):
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
        # ---- Parameters from the hdf5 - file ----
        self.steps = None
        self.steps_length = None
        self._signal = None
        self._step_positions = None

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
        self._max_step_position = None
        self._theta = None
        self._phi = None

        self.phi_2d = None
        self.theta_2d = None
        self.pmt_counts_2d = None

        if isinstance(file, strawb.sensors.lidar.Lidar):  # if it is an instance of Lidar
            self.lidar = file  # use the provided Lidar instance
            self.extract_measurements()
        elif isinstance(file, (strawb.sensors.lidar.FileHandler, str)):  # if it is an instance of Lidar.FileHandler
            self.lidar = strawb.sensors.lidar.Lidar(file=file)  # creates a Lidar instance
            self.extract_measurements()
        else:
            self.lidar = None

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

    @property
    def phi(self):
        """
        The computed phi angle from the steps
        :return:
        self._phi: ndarray(dtype=float, ndim=1, len=variable)
        """
        if self._phi is None and self.step_positions is not None:
            self._phi, self._theta = self.convert_to_angles(step_positions_1=self.step_positions[:, 0],
                                                            step_positions_2=self.step_positions[:, 1])
        return self._phi

    @property
    def theta(self):
        """
        The computed theta angle from the steps
        :return:
        self._theta: ndarray(dtype=float, ndim=1, len=variable)
        """
        if self._theta is None and self.step_positions is not None:
            self._phi, self._theta = self.convert_to_angles(step_positions_1=self.step_positions[:, 0],
                                                            step_positions_2=self.step_positions[:, 1])
        return self._theta

    @property
    def step_positions(self):
        """
        The step positions of the hdf5-file
        :return:
        self._step_positions: ndarray(dtype=float, ndim=2, shape(steps_length,2))
        """
        if self._step_positions is None:
            self._step_positions = self.get_step_positions()
        return self._step_positions

    @step_positions.setter
    def step_positions(self, value):
        self._step_positions = value

    @property
    def signal(self):
        """
        The signal from the hdf5-file
        :return:
        self._signal: ndarray(dtype=float, ndim=2, shape(steps_length,2))
        """
        if self._signal is None:
            self._signal = self.get_signal()
        return self._signal

    @signal.setter
    def signal(self, value):
        self._signal = value

    @property
    def max_step_position(self):
        """
        Step positions corresponding to the measurement with the highest signal value
        :return:
        self._max_step_position: ndarray(dtype=float, ndim=1, shape=(2,))
        """
        if self._max_step_position is None:
            self._max_step_position = self.compute_maximum_position()
        return self._max_step_position

    def extract_measurements(self):
        """
        calls self.signal(), self.step_positions(), and self.max_step_position(), if they are None, their
        :return:
        self.positions: ndarray(dtype=float, ndim=2, shape(steps_length,2))
        self.signal: ndarray(dtype=float, ndim=1, shape(steps_length))
        """
        # self.signal  # = self.get_signal()
        # self.step_positions  # = self.get_step_positions()
        # self.max_step_position  # = self.compute_maximum_position()

        return self.step_positions, self.signal  # , self.max_step_position

    def get_signal(self):
        """
        Get middle of Timestamps of trb readout. Then sum the corresponding counts of PMT and laser in
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

        # laser_steps_x = np.array(self.lidar.file_handler.laser_set_adjust_x)
        # laser_steps_y = np.array(self.lidar.file_handler.laser_set_adjust_y)

        # change_x = np.where(np.diff(laser_steps_x))[0]
        # change_y = np.where(np.diff(laser_steps_y))[0]

        # step_positions = np.array([laser_steps_x[change_x], laser_steps_y[change_y]]).T

        # steps_x = laser_steps_x[change_x]
        # steps_y = laser_steps_y[change_y]
        # step_positions = np.array([laser_steps_x[change_x], laser_steps_y[change_y]]).T
        # step_positions = np.zeros((self.steps_length ** 2, 2))

        # # cut because laser moves back to (0,0) after last pos
        # step_positions[:, 0] = steps_x[:self.steps_length ** 2]
        # step_positions[:, 1] = steps_y[:self.steps_length ** 2]

        # take the middle of the measurement step-time and get the corresponding adjust_x/y values

        measurement_adjust_x = np.interp(self.lidar.file_handler.measurement_time,
                                         self.lidar.file_handler.laser_time,
                                         self.lidar.file_handler.laser_set_adjust_x)

        measurement_adjust_y = np.interp(self.lidar.file_handler.measurement_time,
                                         self.lidar.file_handler.laser_time,
                                         self.lidar.file_handler.laser_set_adjust_y)

        step_positions = np.array([measurement_adjust_x, measurement_adjust_y]).T

        return step_positions

    def compute_maximum_position(self):
        """
        finds the maximum of the self.signal array, assigns it to an offset variable and returns the corresponding steps
        :return:
        max_steps: ndarray(dtype=float, ndim=1, len=2)
        """
        index = np.argmax(self.signal)
        max_step_positions = self.step_positions[index]

        return max_step_positions

    def convert_to_angles(self, step_positions_1, step_positions_2):
        """
        gets a step and an offset as an input. Subtracts offset from steps and converts it to angles
        :param step_positions_1: First coordinate of steps ndarray(dtype=float, ndim=1, len=variable)
        :param step_positions_2: Second coordinate of steps ndarray(dtype=float, ndim=1, len=variable)
        :return:
        """

        n = np.cross(self.x_1 + self.v_motor * step_positions_1.reshape(-1, 1),
                     self.x_2 + self.v_motor * step_positions_2.reshape(-1, 1))

        theta = np.arccos(n[:, 2] / np.sqrt(np.sum(n ** 2, axis=-1)))
        phi = np.arctan2(n[:, 1], n[:, 0]) + np.pi

        return phi, theta
