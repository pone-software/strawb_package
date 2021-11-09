import numpy as np
import scipy
import strawb.sensors.lidar


class Analysis:
    def __init__(self, file, lever_long=0.051, lever_short=0.038, rpm=31, delta_t_step=0.5, thread_steepness=0.02,
                 efficiency=0.5):
        self.steps = None
        self.file = file

        self.lever_long = lever_long  # [m]; long distance between the fixed screw and the servo axis
        self.lever_short = lever_short  # [m]; short distance between the fixed screw and the servo axis
        self.rpm = rpm  # [1/min] rotations per minute
        self.rps = self.rpm / 60.  # [1/s] rotations per second
        self.delta_t_step = delta_t_step  # [s] seconds the motor moves per step
        self.thread_steepness = thread_steepness  # [m], thread steepness (distance per rotation)
        self.efficiency = efficiency  # the motor moves slow with friction, e.g. 50% slower -> .5
        self.dx = self.rps * self.delta_t_step * self.thread_steepness * self.efficiency  # [m] distance per rotation

        self.phi_2d = None
        self.theta_2d = None
        self.pmt_counts_2d = None

    def spiral(self):
        xx = self.steps * 2 + 1
        yy = self.steps * 2 + 1
        steps = np.zeros((xx * yy, 2))
        x = y = 0
        dx = 0
        dy = -1
        for i in range(max(xx, yy) ** 2):
            if (-xx / 2 < x <= xx / 2) and (-yy / 2 < y <= yy / 2):
                steps[i] = (x, y)
            if x == y or (x < 0 and x == -y) or (x > 0 and x == 1 - y):
                dx, dy = -dy, dx
            x, y = x + dx, y + dy
        return steps

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

        bin_counts_pmt, bin_edges, binnumber = scipy.stats.binned_statistic(
            abs_timestamp_middle,
            lidar.trb_rates.dcounts_pmt,
            statistic='sum',
            bins=lidar.file_handler.measurement_time)

        bin_counts_laser, bin_edges, binnumber = scipy.stats.binned_statistic(
            abs_timestamp_middle,
            lidar.trb_rates.dcounts_laser,
            statistic='sum',
            bins=lidar.file_handler.measurement_time)

        length = np.sqrt(len(bin_counts_pmt[:-1:2]))
        if not length % 1 == 0:
            raise TypeError(
                f'{length} is not an integer represented as float. Check manually if mask of changes in laser '
                f'adjustment was set correctly.')
        length = int(length)
        self.steps = int((length - 1) / 2)

        pmt_counts_2d = np.zeros((length, length))

        indices = self.spiral()
        indices_shifted = indices + self.steps

        bin_counts_pmt = bin_counts_pmt[::2]
        bin_counts_laser = bin_counts_laser[::2]

        for i in range(len(indices_shifted)):
            ii = int(indices_shifted[i, 0])
            jj = int(indices_shifted[i, 1])
            pmt_counts_2d[ii, jj] = bin_counts_pmt[i] / bin_counts_laser[i]

        self.pmt_counts_2d = pmt_counts_2d
        return pmt_counts_2d

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
        x_1 = np.array([[self.lever_short, 0, 0]])  # [m]; x Position stepper
        x_2 = np.array([[0, self.lever_long, 0]])  # [m]; y Position stepper
        v_motor = np.array([[0, 0, self.dx]])  # the vector per motor-step
        # print(f'Distance per Step: {dx * 1e3:.3f} mm')

        # ---- Steps ----
        # get the steps grid, e.g. steps in x and y from [-5,...,5]
        steps_all = int(2 * self.steps + 1)
        s_0, s_1 = np.meshgrid(np.arange(steps_all) - steps_all // 2, np.flip(np.arange(steps_all) - steps_all // 2))
        s_0 = s_0.flatten()
        s_1 = s_1.flatten()

        # ---- Angles ----
        # calculate the normal
        n = np.cross(x_1 + v_motor * s_0.reshape(-1, 1),
                     x_2 + v_motor * s_1.reshape(-1, 1))

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

        r = self.lever_long * self.lever_short / np.cos(max_theta)
        s1 = -r / (self.lever_long * self.dx) * np.cos(max_phi) * np.sin(max_theta)
        s2 = -r / (self.lever_short * self.dx) * np.sin(max_phi) * np.sin(max_theta)
        s1 = np.round(s1)
        s2 = np.round(s2)

        return s1, s2
