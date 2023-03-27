from strawb.base_file_handler import BaseFileHandler


class FileHandler(BaseFileHandler):
    def __init__(self, *args, **kwargs):
        """MuonTracker File Handler it holds links to the data available in the hdf5 file from the MuonTracker.
        PARAMETERS
        ----------
        *args, **kwargs: optional
            parsed to BaseFileHandler
        """
        # Counter, similar to PMTSpectrometer. Added to hdf5 ???.
        # -> File version ???
        self.counts_time = None  # absolute timestamps in seconds for each counts reading
        self.counts_ch0 = None  # channel which counts up at a constant frequency
        self.counts_ch1 = None
        self.counts_ch10 = None
        self.counts_ch11 = None
        self.counts_ch12 = None
        self.counts_ch13 = None
        self.counts_ch14 = None
        self.counts_ch15 = None
        self.counts_ch16 = None
        self.counts_ch2 = None
        self.counts_ch3 = None
        self.counts_ch4 = None
        self.counts_ch5 = None
        self.counts_ch6 = None
        self.counts_ch7 = None
        self.counts_ch8 = None
        self.counts_ch9 = None

        # TRB_DAQ
        self.daq_time = None
        self.daq_frequency_readout = None  # the frequency when the TRB counts up counts channel 0
        self.daq_state = None  # 0: TRB not ready; 1: TRB ready; 2: TRB takes hld
        self.daq_trb = None  # TRB power; 0: OFF; 1: ON

        # hv
        self.hv_hv_value = None
        self.hv_time = None

        # Padiwa Settings thresholds
        self.padiwa_offset = None
        self.padiwa_power = None
        self.padiwa_th1 = None
        self.padiwa_th10 = None
        self.padiwa_th11 = None
        self.padiwa_th12 = None
        self.padiwa_th13 = None
        self.padiwa_th14 = None
        self.padiwa_th15 = None
        self.padiwa_th16 = None
        self.padiwa_th2 = None
        self.padiwa_th3 = None
        self.padiwa_th4 = None
        self.padiwa_th5 = None
        self.padiwa_th6 = None
        self.padiwa_th7 = None
        self.padiwa_th8 = None
        self.padiwa_th9 = None
        self.padiwa_time = None

        # PMT TOT (time over threshold), each entry is a separated event. Added to hdf5 ???>.
        # -> File version ???
        self.tot_channel = None
        self.tot_time = None
        self.tot_time_ns = None
        self.tot_tot = None

        # holds the file version
        self.file_version = None

        # comes last to load the data in case file_name is set
        BaseFileHandler.__init__(self, *args, **kwargs)

    @staticmethod
    def __load_functions__(f_list):
        # order is important, tries to load newest first and oldest latest.
        err_list = []
        for i in f_list:
            try:
                i()  # try file versions
                return
            # version is detected because datasets in the hdf5 aren't present -> i() fails with KeyError
            except KeyError as a:
                err_list.append(a.args[0])
            except OSError as a:
                err_list.append(a.args[0])

        raise KeyError('; '.join(err_list))

    def _test_functions_(self, f_list):
        result_dict = {}
        for i, f_i in enumerate(f_list):
            try:
                self.__load_functions__([f_i])
                result_dict.update({i: True})
            except Exception as a:
                result_dict.update({i: a})
        return result_dict

    def __load_meta_data__(self, ):
        try:
            self.__load_counts_v0__()
        except KeyError:
            pass

        try:
            self.__load_hv__()
        except KeyError:
            pass

        self.__load_functions__([self.__load_meta_data_v4__, self.__load_meta_data_v3__,
                                 self.__load_meta_data_v2__, self.__load_meta_data_v1__])

    # ---- The functions for different versions ----
    def __load_meta_data_v1__(self, ):
        """Loads the initial SDAQ-hdf5 File Version"""
        # load the single hdf5 groups
        self.__load_daq_v1__()  # TRB_DAQ
        try:
            self.__load_padiwa_v1__()
        except KeyError:
            pass

        self.file_version = 1

    def __load_meta_data_v2__(self, ):
        """Loads the initial SDAQ-hdf5 File Version"""
        self.__load_daq_v2__()  # TRB_DAQ
        try:
            self.__load_padiwa_v2__()
        except KeyError:
            pass

        self.file_version = 2

    def __load_meta_data_v3__(self, ):
        """Loads the initial SDAQ-hdf5 File Version"""
        self.__load_daq_v3__()  # TRB_DAQ
        try:
            self.__load_padiwa_v2__()
        except KeyError:
            pass

        self.file_version = 3

    def __load_meta_data_v4__(self, ):
        """Loads the initial SDAQ-hdf5 File Version"""
        self.__load_padiwa_v2__()
        self.__load_daq_v3__()
        self.__load_tot__()

        self.file_version = 4

    # Tester
    def test_all(self, ):
        results = {
            'hv': self._test_hv_(),
            'tot': self._test_tot_(),
            'counts': self._test_counts__(),
            'daq': self._test_daq_(),
            'padiwa': self._test_padiwa_(),
        }
        return results

    def test_all_list(self, ):
        results = self.test_all()
        results_2 = {}
        for j in results:
            results_2.update({f'{j}_{i}': results[j][i] is True for i in results[j]})

        return results_2

    def _test_hv_(self, ):
        return self._test_functions_([self.__load_hv__])

    def _test_tot_(self, ):
        return self._test_functions_([self.__load_tot__])

    def _test_counts__(self, ):
        return self._test_functions_([self.__load_counts_v1__, self.__load_counts_v2__])

    def _test_daq_(self, ):
        return self._test_functions_([self.__load_daq_v1__, self.__load_daq_v2__, self.__load_daq_v3__])

    def _test_padiwa_(self, ):
        return self._test_functions_([self.__load_padiwa_v1__,
                                      self.__load_padiwa_v2__])

    # ---- Helper functions for load ----
    def __load_hv__(self):
        # TOT - sometime there are is no TOT available
        self.hv_hv_value = self.file['hv/hv_value']
        self.hv_time = self.file['hv/time']

    def __load_tot__(self):
        # TOT - sometime there are is no TOT available
        self.tot_time = self.file['tot/time']
        # fix bug, that swapped `tot_time` and  `tot_time_ns`
        if self.tot_time[0].max() < 1e8:
            self.tot_time = self.file['tot/time_ns']
            self.tot_time_ns = self.file['tot/time']
        else:
            self.tot_time = self.file['tot/time']
            self.tot_time_ns = self.file['tot/time_ns']

        self.tot_tot = self.file['tot/tot']
        self.tot_channel = self.file['tot/channel']

    def __load_counts_v0__(self):
        try:
            self.__load_counts_v2__()
        except KeyError:
            self.__load_counts_v1__()

    def __load_counts_v1__(self):
        self.counts_time = self.file['/rates/time']
        self.counts_ch0 = self.file['/rates/ch0']
        self.counts_ch1 = self.file['/rates/ch1']
        self.counts_ch3 = self.file['/rates/ch3']
        self.counts_ch5 = self.file['/rates/ch5']
        self.counts_ch6 = self.file['/rates/ch6']
        self.counts_ch7 = self.file['/rates/ch7']
        self.counts_ch8 = self.file['/rates/ch8']
        self.counts_ch9 = self.file['/rates/ch9']
        self.counts_ch10 = self.file['/rates/ch10']
        self.counts_ch11 = self.file['/rates/ch11']
        self.counts_ch12 = self.file['/rates/ch12']
        self.counts_ch13 = self.file['/rates/ch13']
        self.counts_ch15 = self.file['/rates/ch15']

    def __load_counts_v2__(self):
        self.counts_time = self.file['/counts/time']
        self.counts_ch0 = self.file['/counts/ch0']
        self.counts_ch1 = self.file['/counts/ch1']
        self.counts_ch3 = self.file['/counts/ch3']
        self.counts_ch5 = self.file['/counts/ch5']
        self.counts_ch6 = self.file['/counts/ch6']
        self.counts_ch7 = self.file['/counts/ch7']
        self.counts_ch8 = self.file['/counts/ch8']
        self.counts_ch9 = self.file['/counts/ch9']
        self.counts_ch10 = self.file['/counts/ch10']
        self.counts_ch11 = self.file['/counts/ch11']
        self.counts_ch12 = self.file['/counts/ch12']
        self.counts_ch13 = self.file['/counts/ch13']
        self.counts_ch15 = self.file['/counts/ch15']

    def __load_daq_v1__(self):
        """Old: daq '/padiwa/power' as '/daq/padiwa' """
        self.daq_frequency_readout = self.file['/daq/rate_readout']
        self.daq_state = self.file['/daq/state']
        self.daq_time = self.file['/daq/time']
        self.daq_trb = self.file['/daq/trb']
        self.padiwa_power = self.file['/daq/padiwa']

    def __load_daq_v2__(self):
        """CHANGES to V1:
        - daq '/daq/padiwa' -> '/padiwa/power'"""
        self.daq_frequency_readout = self.file['/daq/rate_readout']
        self.daq_state = self.file['/daq/state']
        self.daq_time = self.file['/daq/time']
        self.daq_trb = self.file['/daq/trb']

    def __load_daq_v3__(self):
        """CHANGES to V2:
        - daq '/daq/rate_readout' -> '/daq/frequency_readout'"""
        self.daq_frequency_readout = self.file['/daq/frequency_readout']
        self.daq_state = self.file['/daq/state']
        self.daq_time = self.file['/daq/time']
        self.daq_trb = self.file['/daq/trb']

    def __load_padiwa_v1__(self):
        """Old: no '/padiwa/power' in daq"""
        self.padiwa_time = self.file['/padiwa/time']
        self.padiwa_offset = self.file['/padiwa/offset']
        self.padiwa_th1 = self.file['/padiwa/th1']  # 350 nm
        self.padiwa_th2 = self.file['/padiwa/th2']  # 400 nm
        self.padiwa_th3 = self.file['/padiwa/th3']  # 425 nm
        self.padiwa_th4 = self.file['/padiwa/th4']  # 450 nm
        self.padiwa_th5 = self.file['/padiwa/th5']  # 460 nm
        self.padiwa_th6 = self.file['/padiwa/th6']  # 470 nm
        self.padiwa_th7 = self.file['/padiwa/th7']  # 480 nm
        self.padiwa_th8 = self.file['/padiwa/th8']  # 492 nm
        self.padiwa_th9 = self.file['/padiwa/th9']  # not connected
        self.padiwa_th10 = self.file['/padiwa/th10']  # not connected
        self.padiwa_th11 = self.file['/padiwa/th11']  # 510 nm
        self.padiwa_th12 = self.file['/padiwa/th12']  # 525 nm
        self.padiwa_th13 = self.file['/padiwa/th13']  # 550 nm
        self.padiwa_th14 = self.file['/padiwa/th14']  # NO FILTER
        self.padiwa_th15 = self.file['/padiwa/th15']  # not connected

    def __load_padiwa_v2__(self):
        """Old: with '/padiwa/power' """
        self.padiwa_time = self.file['/padiwa/time']
        self.padiwa_offset = self.file['/padiwa/offset']
        self.padiwa_power = self.file['/padiwa/power']
        self.padiwa_th1 = self.file['/padiwa/th1']  # 350 nm
        self.padiwa_th2 = self.file['/padiwa/th2']  # 400 nm
        self.padiwa_th3 = self.file['/padiwa/th3']  # 425 nm
        self.padiwa_th4 = self.file['/padiwa/th4']  # 450 nm
        self.padiwa_th5 = self.file['/padiwa/th5']  # 460 nm
        self.padiwa_th6 = self.file['/padiwa/th6']  # 470 nm
        self.padiwa_th7 = self.file['/padiwa/th7']  # 480 nm
        self.padiwa_th8 = self.file['/padiwa/th8']  # 492 nm
        self.padiwa_th9 = self.file['/padiwa/th9']  # not connected
        self.padiwa_th10 = self.file['/padiwa/th10']  # not connected
        self.padiwa_th11 = self.file['/padiwa/th11']  # 510 nm
        self.padiwa_th12 = self.file['/padiwa/th12']  # 525 nm
        self.padiwa_th13 = self.file['/padiwa/th13']  # 550 nm
        self.padiwa_th14 = self.file['/padiwa/th14']  # NO FILTER
        self.padiwa_th15 = self.file['/padiwa/th15']  # not connected
        self.padiwa_th16 = self.file['/padiwa/th16']  # not connected  # new
