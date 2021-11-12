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

    def extract_measurements(self, file):
        lidar = strawb.sensors.lidar.Lidar(file=file)

        # ---- get data for signal ----
        abs_timestamp_middle = (lidar.file_handler.counts_time[:-1] + lidar.file_handler.counts_time[1:]) * 0.5

        bin_counts_pmt, bin_edges, binnumber = binned_statistic(
            abs_timestamp_middle,
            lidar.trb_rates.dcounts_pmt,
            statistic='sum',
            bins=lidar.file_handler.measurement_time)

        bin_counts_laser, bin_edges, binnumber = binned_statistic(
            abs_timestamp_middle,
            lidar.trb_rates.dcounts_laser,
            statistic='sum',
            bins=lidar.file_handler.measurement_time)

        bin_counts_pmt = bin_counts_pmt[::2]
        bin_counts_laser = bin_counts_laser[::2]

        self.signal = bin_counts_pmt / bin_counts_laser

        # ---- get data for steps ----

        try:
            self.steps = lidar.file_handler.file_attributes["mes_steps"]
        except KeyError:
            self.steps = lidar.file_handler.file_attributes["measurement_steps"]

        self.steps_length = int(2 * self.steps + 1)

        laser_steps_x = np.array(lidar.file_handler.laser_set_adjust_x)
        laser_steps_y = np.array(lidar.file_handler.laser_set_adjust_y)

        change_x = np.where(np.diff(laser_steps_x))[0]
        change_y = np.where(np.diff(laser_steps_y))[0]

        changes_all = np.array(np.sort(np.append(change_x, change_y)))

        steps_x = laser_steps_x[changes_all]
        steps_y = laser_steps_y[changes_all]

        step_positions = np.zeros((self.steps_length ** 2, 2))

        step_positions[:, 0] = steps_x[:self.steps_length ** 2]  # cut because laser moves back to (0,0) after last pos
        step_positions[:, 1] = steps_y[:self.steps_length ** 2]

        self.step_positions = step_positions

        return self.step_positions, self.signal

    def convert_to_angles(self):
        self.extract_measurements(self.file)
