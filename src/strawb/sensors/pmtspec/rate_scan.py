import numpy as np
import scipy.stats
from matplotlib import pyplot as plt
import strawb


class Scan:
    def __init__(self, time_padiwa, steps_padiwa,
                 time_interpolated, rate_interpolated, active_ratio,
                 scan_threshold_dict, name=''):
        """ Stores the parameter of one scan."""
        self.name = name

        self.time_padiwa = strawb.tools.asdatetime(time_padiwa)
        self.steps_padiwa = steps_padiwa

        self.time_interpolated = time_interpolated
        self.rate_interpolated = rate_interpolated

        # the ratio how often the counts reading happened at active TRB state
        self.active_ratio = active_ratio

        # the starting threshold in the form:
        # {<padiwa channel>: value}, <padiwa channel> <-> pmt_meta_data.channel_meta_array['padiwa']
        self.scan_threshold_dict = scan_threshold_dict


class RateScan:
    def __init__(self, pmt_spec):
        """Class which takes separates the steps of a rate scan and calculate the average rates per threshold.

        PARAMETER
        ---------
        pmt_spec: strawb.sensors.PMTSpec
            link to the strawb.sensors.PMTSpec instance (parent of the class)
        """
        self.pmt_spec = pmt_spec

        # store the instances of `Scan` for both scans and the properties
        self._scan_on_ = None
        self._scan_off_ = None

    @property
    def scan_on(self):
        """Returns the instance `strawb.sensors.pmtspec.rate_scan.Scan` which hold parameters of the rate scan with
        HV enabled."""
        if self._scan_on_ is None:
            self._scan_off_, self._scan_on_ = self.generate_scans()
        return self._scan_on_

    @property
    def scan_off(self):
        """Returns the instance strawb.sensors.pmtspec.rate_scan.Scan which hold parameters of the rate scan with
        HV disabled."""
        if self._scan_off_ is None:
            self._scan_off_, self._scan_on_ = self.generate_scans()
        return self._scan_off_

    def generate_scans(self, *args, **kwargs):
        """Generates the two instances of Scan, i.e. scan_on and scan_off.
        PARAMETER
        ---------
        *args, **kwargs: optional
            get parsed to self.extract_scans(*args, **kwargs)
        """
        [t_off, padiwa_steps_off], [t_on, padiwa_steps_on] = self.extract_scans(*args, **kwargs)
        scan_off = self.generate_one_scan(name='HV OFF',
                                          time_padiwa=t_off,
                                          steps_padiwa=padiwa_steps_off,
                                          )

        scan_on = self.generate_one_scan(name='HV ON',
                                         time_padiwa=t_on,
                                         steps_padiwa=padiwa_steps_on,
                                         )
        return scan_off, scan_on

    def generate_one_scan(self, time_padiwa, steps_padiwa, name=''):
        """

        time_padiwa: ndarray
        steps_padiwa: ndarray

        name: str, optional
            to define a name
        """
        # if the last step takes 0 seconds
        if time_padiwa[-2] == time_padiwa[-1]:
            time_padiwa[-1] += time_padiwa[-3] - time_padiwa[-4]

        t_0 = strawb.tools.datetime2float(self.pmt_spec.trb_rates.time)[0]
        t, r, a = self.pmt_spec.trb_rates.interpolate_rate(time_probe=time_padiwa - t_0)

        # count how often the channel is active
        active, b, n = scipy.stats.binned_statistic(self.pmt_spec.file_handler.counts_time,
                                                    self.pmt_spec.trb_rates.active_read,
                                                    statistic='sum',
                                                    bins=time_padiwa)
        reads, b, n = scipy.stats.binned_statistic(self.pmt_spec.file_handler.counts_time,
                                                   None,
                                                   statistic='count',
                                                   bins=time_padiwa)
        active_ratio = active / reads

        # Starting Threshold
        # get the starting threshold of the scan to which the offset applies.
        # Some older files had problems, correct them here.

        # {<padiwa channel>: value}, <padiwa channel> <-> pmt_meta_data.channel_meta_array['padiwa']
        scan_threshold_dict = {}

        # mask the time of the scan
        mask_th = (self.pmt_spec.file_handler.padiwa_time[:] >= time_padiwa[0])
        mask_th &= (self.pmt_spec.file_handler.padiwa_time[:] <= time_padiwa[-1])

        for ch in self.pmt_spec.pmt_meta_data.channel_meta_array:
            # get the parameters from the file
            scan_threshold = self.pmt_spec.file_handler.__getattribute__(f"padiwa_th{ch['padiwa']}")
            # older version haven't logged the scan_threshold, and 'file_id' == 17343680081235907706 is special
            if self.pmt_spec.file_handler.file_attributes['file_id'] == 17343680081235907706:
                scan_threshold_dict[ch['padiwa']] = 65000

            # older version haven't logged the scan_threshold but they all used 34000 with one exception (s. above)
            elif len(np.unique(scan_threshold)) == 1:
                scan_threshold_dict[ch['padiwa']] = 34000

            # take the any value, they should be all the same, here the last
            else:
                scan_threshold_dict[ch['padiwa']] = scan_threshold[mask_th][-1]

        return Scan(time_padiwa=time_padiwa,
                    steps_padiwa=steps_padiwa,
                    time_interpolated=t,
                    rate_interpolated=r,
                    active_ratio=active_ratio,
                    scan_threshold_dict=scan_threshold_dict,
                    name=name)

    def extract_scans(self, plot=False, output=False):
        """ Extract the scans of the files. The scan measures the rate for different threshold offsets.
        PARAMETER
        ---------
        plot: bool, optional
            generate a plot for more insight, default False
        output: bool, optional
            print some output, default False

        RETURNS
        -------
        [[t_off, s_off], [t_on, s_on]]
            t_off and s_off are the parameters for the scan with HV OFF and t_on, s_on are with HV ON.
            Both are np.ndarray in the style of strawb.tools.unique_steps(...).
            Therefore, t_xxx and s_xxx has the shape of: [step_i, 2] with
            t_xxx: [[start time, end time],... of the steps and,
            s_xxx: [[value step_i, value step_i], ...]
        """
        # get unique_steps: each step (same values in a row) get a start and end time
        # if there is only one time for one step, the end is calculated as a ratio (ratio_steps_len_1)
        # to the next step, for more information see above
        t_steps_padiwa, state_steps_padiwa = strawb.tools.unique_steps(self.pmt_spec.file_handler.padiwa_time[:],
                                                                       self.pmt_spec.file_handler.padiwa_offset[:])
        t_steps_hv, state_steps_hv = strawb.tools.unique_steps(self.pmt_spec.file_handler.hv_time[:],
                                                               self.pmt_spec.file_handler.hv_power[:])

        # t_steps_padiwa     = [[t_0, t_1], [t_2, t_3],...,[t_(2*i),t_(2*i+1)]]
        # state_steps_padiwa = [[s_0, s_0], [s_1, s_1],...,[s_i,s_i]]

        #     # convert to datetime64
        #     t_steps_padiwa = strawb.tools.asdatetime(t_steps_padiwa)
        #     t_steps_hv = strawb.tools.asdatetime(t_steps_hv)

        # get OFF scan
        t_hv_off = t_steps_hv[state_steps_hv[:, 0] == 0][0]
        m_padiwa_hv_off = (t_steps_padiwa >= t_hv_off[0]) & (t_steps_padiwa < t_hv_off[1])

        t_start_off = np.max([t_hv_off[0],
                              t_steps_padiwa[(state_steps_padiwa == 0) & m_padiwa_hv_off][0],
                              ])
        # old sdaq versions don't log the right before the switch
        # -> take the time when hv is switched on - 1 second
        # -> t_steps_hv[state_steps_hv[:,0] == 1][-1,0] - 1.
        t_end_off = t_steps_hv[state_steps_hv[:, 0] == 1][-1, 0] - 2  # -2 seconds
        if output:
            print('scan hv OFF: ', t_start_off, t_end_off)

        # get ON scan
        # get the time, when hv switched to active (...[:,0] == 1) the last time (...[-1])
        # t_hv_on = [time start ON, time end ON]
        t_hv_on = t_steps_hv[state_steps_hv[:, 0] == 1][-1]
        # the time end ON isn't record properly -> NO: & (t_steps_padiwa < t_hv_on[1])
        m_padiwa_hv_on = t_steps_padiwa >= t_hv_on[0]

        t_start_on = np.max([t_hv_on[0],
                             t_steps_padiwa[(state_steps_padiwa == 0) & m_padiwa_hv_on][0],
                             ])

        # old sdaq versions don't log the right before the switch
        # -> take the time when hv is switched on - 1 second
        # -> t_steps_hv[state_steps_hv[:,0] == 1][-1,0] - 1.
        t_end_on = t_steps_padiwa[(state_steps_padiwa != 0) & m_padiwa_hv_on][-1] + 2  # +2 seconds

        if output:
            print('scan hv ON : ', t_start_on, t_end_on)

        mask_on = (t_steps_padiwa >= t_start_on) & (t_steps_padiwa <= t_end_on)
        mask_off = (t_steps_padiwa >= t_start_off) & (t_steps_padiwa <= t_end_off)

        # plot for more insight
        if plot:
            plt.figure()
            # plt.plot(pmt.file_handler.padiwa_time.asdatetime()[:],
            #          pmt.file_handler.padiwa_offset[:].astype(bool), '-')
            plt.plot(t_steps_padiwa.flatten(), state_steps_padiwa.flatten() / state_steps_padiwa.max(), 'o-',
                     label='padiwa steps')
            plt.plot(t_steps_hv.flatten(), state_steps_hv.flatten(), 'o-', label='HV steps')

            plt.fill_between([t_start_off, t_end_off], [0, 0], [1, 1], alpha=.2, color='gray', label='scan HV OFF')
            plt.fill_between([t_start_on, t_end_on], [0, 0], [1, 1], alpha=.4, color='gray', label='scan HV ON')
            plt.grid()
            plt.legend(loc=4)

        t_off = t_steps_padiwa[mask_off]
        s_off = state_steps_padiwa[mask_off]

        # each step should have a start and end, sometimes the end is dropped.
        # add it here
        if s_off[-2] != s_off[-1]:
            s_off = np.array([*s_off, s_off[-1]])
            #
            t_off = np.array([*t_off, t_off[-1] + t_off[-3] - t_off[-4]])

        t_on = t_steps_padiwa[mask_on]
        s_on = state_steps_padiwa[mask_on]

        # each step should have a start and end, sometimes the end is dropped.
        # add it here
        if s_on[-2] != s_on[-1]:
            s_on = np.array([*s_on, s_on[-1]])
            #
            t_on = np.array([*t_on, t_on[-1] + t_on[-3] - t_on[-4]])

        return [[t_off, s_off], [t_on, s_on]]
