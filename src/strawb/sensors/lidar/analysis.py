import numpy as np
from scipy.stats import binned_statistic
import strawb.sensors.lidar


class Analysis:
    def __init__(self, file, lever_long=0.051, lever_short=0.038, rpm=31, delta_t_step=0.5, thread_steepness=0.002,
                 efficiency=0.5):
        self.steps = None
        self.steps_length = None
        self.file = file
        self.step_positions = None

        self.rpm = rpm  # [1/min] rotations per minute
        self.rps = self.rpm / 60.  # [1/s] rotations per second
        self.delta_t_step = delta_t_step  # [s] seconds the motor moves per step
        self.thread_steepness = thread_steepness  # [m], thread steepness (distance per rotation)
        self.efficiency = efficiency  # the motor moves slow with friction, e.g. 50% slower -> .5
        self.dx = self.rps * self.delta_t_step * self.thread_steepness * self.efficiency  # [m] distance per rotation
        self.x_1 = np.array([[lever_short, 0, 0]])  # [m]; x Position stepper
        self.x_2 = np.array([[0, lever_long, 0]])  # [m]; y Position stepper
        self.v_motor = np.array([[0, 0, self.dx]])  # the vector per motor-step
        self.phi_2d = None
        self.theta_2d = None
        self.pmt_counts_2d = None

    def get_steps(self):
        """
        Gets the individual steps from the hdf5-file, also sets the maximum steps for one direction, and the length for
        one direction (so 2*steps+1). Sets the steps that the laser moved steps: it is a 2D array with the absolut
        steps for the spiral shape=((2*steps+1)**2,2)
        :return:
        None
        """
        lidar = strawb.sensors.lidar.Lidar(file=self.file)
        self.steps = lidar.file_handler.file_attributes["mes_steps"]
        self.steps_length = int(2 * self.steps + 1)

        laser_steps_x = np.array(lidar.file_handler.laser_set_adjust_x)
        laser_steps_y = np.array(lidar.file_handler.laser_set_adjust_y)

        change_x = np.where(np.diff(laser_steps_x))[0]
        change_y = np.where(np.diff(laser_steps_y))[0]

        changes_all = np.array(np.sort(np.append(change_x, change_y)))

        steps_x = laser_steps_x[changes_all]
        steps_y = laser_steps_y[changes_all]

        step_positions = np.zeros((self.steps_length ** 2, 2))

        step_positions[:, 0] = steps_x[:self.steps_length**2]  # cut because laser moves back to (0,0) after last pos
        step_positions[:, 1] = steps_y[:self.steps_length**2]

        self.step_positions = step_positions

    def laser_adjustment_return(self):
        """
        Use direct trb readout. TRB is read out with constant frequency. Both the PMT and the Laser Channel. Use middle
        of these absolute timestamps as integration points in binned_statistics. "lidar.file_handler.measurement_time"
        gives the bins. Larger when hld-files are produced. Therefore use recorded photons/emitted pulses as value to
        counteract this effect.
        RETURN
        ------
        Returns the correct mapping of the calculated values to the spiral and reshapes it into 2d array

        """
        lidar = strawb.sensors.lidar.Lidar(file=self.file)

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

        self.get_steps()

        if not self.steps_length % 1 == 0:
            raise TypeError(
                f'{self.steps_length} is not an integer represented as float. Check manually if mask of changes in '
                f'laser adjustment was set correctly.')

        pmt_counts_2d = np.zeros((self.steps_length, self.steps_length))

        indices_shifted = self.step_positions + self.steps

        bin_counts_pmt = bin_counts_pmt[::2]
        bin_counts_laser = bin_counts_laser[::2]

        for i in range(len(indices_shifted)):
            ii = int(indices_shifted[i, 0])
            jj = int(indices_shifted[i, 1])
            pmt_counts_2d[ii, jj] = bin_counts_pmt[i] / bin_counts_laser[i]

        self.pmt_counts_2d = pmt_counts_2d

        return self.pmt_counts_2d

    def get_angles(self):
        """
        Calculates the steps that are taken in the directions s_0,s_1 via meshgrid. Identical to spiral but as the
        values for a 2D grid. the angle of rotations are
        n1 = [X_1, 0, V_motor * s_1]
        n2 = [0, X_2, V_motor * s_1]
        and the laser direction is the crossproduct of which theta and phi is calculated
        PARAMETER
        ---------
        steps: int
            the amount of steps that where went into one direction, default=10

        RETURN
        ------
        phi: array,float, len= (2*steps+1)**2
        theta: array,float, len= (2*steps+1)**2
        """
        # ---- Steps ----
        # get the steps grid, e.g. steps in x and y from [-5,...,5]
        s_0, s_1 = np.meshgrid(np.arange(self.steps_length) - self.steps_length // 2,
                               np.flip(np.arange(self.steps_length) - self.steps_length // 2))
        s_0 = s_0.flatten()
        s_1 = s_1.flatten()

        # ---- Angles ----
        # calculate the normal
        n = np.cross(self.x_1 + self.v_motor * s_0.reshape(-1, 1),
                     self.x_2 + self.v_motor * s_1.reshape(-1, 1))

        theta = np.arccos(n[:, 2] / np.sqrt(np.sum(n ** 2, axis=-1)))
        phi = np.arctan2(n[:, 1], n[:, 0]) + np.pi

        self.phi_2d = phi.reshape(2 * self.steps + 1, 2 * self.steps + 1)
        self.theta_2d = theta.reshape(2 * self.steps + 1, 2 * self.steps + 1)

        return self.phi_2d, self.theta_2d

    def get_steps_from_max_value(self):
        """
        np.max() returns index of max value which corresponds to a direction. Can be translated to steps and than
        returned. s1 = steps in x-direction s2 = steps in y-direction
        PARAMETER
        ---------
        phi_2d: array, float, dim= (2*steps+1,2*steps+1). For 10 steps it has size (21,21)
        theta2d: array, float, dim= (2*steps+1,2*steps+1). For 10 steps it has size (21,21)

        RETURN
        ------
        s1: float, 1. coordinate for steps to the max value
        s2: float, 2. coordinate for steps to the max value
        """
        self.laser_adjustment_return()
        self.get_angles()

        max_ind = np.unravel_index(self.pmt_counts_2d.argmax(), self.pmt_counts_2d.shape)

        max_phi = self.phi_2d[max_ind]
        max_theta = self.theta_2d[max_ind]

        r = self.x_2[0, 1] * self.x_1[0, 0] / np.cos(max_theta)
        s1 = -r / (self.x_2[0, 1] * self.dx) * np.cos(max_phi) * np.sin(max_theta)
        s2 = -r / (self.x_1[0, 0] * self.dx) * np.sin(max_phi) * np.sin(max_theta)
        s1 = np.round(s1)
        s2 = np.round(s2)

        return s1, s2
