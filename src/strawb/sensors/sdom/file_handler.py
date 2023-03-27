# Author: Kilian Holzapfel <kilian.holzapfel@tum.de>
import numpy as np

from strawb.base_file_handler import BaseFileHandler


class FileHandler(BaseFileHandler):
    def __init__(self, *args, **kwargs):
        """The File Handler of the PMTSpectrometer hdf5 data."""
        # TODO: adopt to SDOM file, for simplification keep the naming where possible, i.e. self.counts_
        # Counter
        self.counts_time = None  # absolute timestamps in seconds for each counter reading
        self.counts_ch0 = None  # channel which counts up at a constant frequency -> PMT Spectrometer
        self.counts_ch1 = None  # the PMT channel 1.
        self.counts_ch3 = None  # the PMT channel
        self.counts_ch5 = None  # the PMT channel
        self.counts_ch6 = None  # the PMT channel
        self.counts_ch7 = None  # the PMT channel
        self.counts_ch8 = None  # the PMT channel
        self.counts_ch9 = None  # the PMT channel
        self.counts_ch10 = None  # the PMT channel
        self.counts_ch11 = None  # the PMT channel
        self.counts_ch12 = None  # the PMT channel
        self.counts_ch13 = None  # the PMT channel
        self.counts_ch15 = None  # the PMT channel

        # interpolated rates. Based on the `counts` and interpolated to fit an artificial readout frequency.
        self.interp_frequency = None  # artificially readout frequency
        self.interp_time = None  # absolute timestamps. Shape: [time_j]
        self.interp_rates = None  # rates a s a 2d array. Shape: [channel_i, time_j]

        # Padiwa Settings thresholds
        self.padiwa_time = None
        self.padiwa_th1 = None  # 350 nm
        self.padiwa_th2 = None  # 400 nm
        self.padiwa_th3 = None  # 425 nm
        self.padiwa_th4 = None  # 450 nm
        self.padiwa_th5 = None  # 460 nm
        self.padiwa_th6 = None  # 470 nm
        self.padiwa_th7 = None  # 480 nm
        self.padiwa_th8 = None  # 492 nm
        self.padiwa_th9 = None  # not connected
        self.padiwa_th10 = None  # not connected
        self.padiwa_th11 = None  # 510 nm
        self.padiwa_th12 = None  # 525 nm
        self.padiwa_th13 = None  # 550 nm
        self.padiwa_th14 = None  # NO FILTER
        self.padiwa_th15 = None  # not connected
        self.padiwa_th16 = None  # not connected
        self.padiwa_offset = None
        self.padiwa_power = None

        # HV-PMT Settings
        self.hv_time = None
        self.hv_ch0 = None  # 350 nm
        self.hv_ch1 = None  # 400 nm, 480 nm
        self.hv_ch2 = None  # 425 nm
        self.hv_ch3 = None  # 450 nm, 470 nm
        self.hv_ch4 = None  # 460 nm, 492 nm
        self.hv_ch5 = None  # 510 nm, 550 nm
        self.hv_ch6 = None  # 525 nm
        self.hv_ch7 = None  # NO FILTER
        self.hv_ch8 = None  # not connected
        self.hv_ch9 = None  # not connected
        self.hv_ch10 = None  # not connected
        self.hv_ch11 = None  # not connected
        self.hv_ch12 = None  # not connected
        self.hv_ch13 = None  # not connected
        self.hv_ch14 = None  # not connected
        self.hv_ch15 = None  # not connected
        self.hv_power = None

        # TRB Settings
        self.daq_frequency_readout = None
        self.daq_state = None
        self.daq_time = None
        self.daq_trb = None

        # comes last to load the data in case file_name is set
        BaseFileHandler.__init__(self, *args, **kwargs)

    def __load_meta_data__(self, ):
        # TODO: adopt to SDOM - probably there is only one file version -> `for i in [self.__load_meta_data_v1__]`
        # 'counts' (older files 'rates') is the measurement data and most important group
        if not ('counts' in self.file or 'rates' in self.file):
            raise KeyError('missing important group')

        err_list = []
        for i in [self.__load_meta_data_v2__, self.__load_meta_data_v1__]:
            try:
                i()  # try file versions
                return
            # version is detected because datasets in the hdf5 aren't present -> i() fails with KeyError
            except (TypeError, KeyError) as a:
                err_list.append(a.args[0])

        raise KeyError('; '.join(err_list))

    def __load_meta_data_v1__(self, ):
        """In older versions, only the counts have been written.
        `padiwa`, `hv`, and `daq` not, because there was no change. Support it here.
        This version has no: `padiwa`, `hv`, and `daq`."""
        # TODO: adopt to SDOM
        self.__load_counts_v1__()
        self.file_version = 1

        # it's the default frequency to fix files where writing failed
        self.daq_frequency_readout = np.array([10000.], dtype=np.float32)

    def __load_meta_data_v2__(self, ):
        """In older versions, only the counts have been written.
        `padiwa`, `hv`, and `daq` not, because there was no change. Support it here.
        This version has `padiwa`, `hv`, and `daq`."""
        # TODO: adopt to SDOM
        self.__load_counts_v1__()
        self.__load_daq_v1__()
        self.file_version = 2

    def __load_counts_v1__(self):
        # TODO: adopt to SDOM
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
        # TODO: adopt to SDOM
        """Old: daq '/padiwa/power' as '/daq/padiwa' """
        self.daq_frequency_readout = self.file['/daq/rate_readout']
        self.daq_state = self.file['/daq/state']
        self.daq_time = self.file['/daq/time']
        self.daq_trb = self.file['/daq/trb']
        self.padiwa_power = self.file['/daq/padiwa']


class ProcessedFileHandler(BaseFileHandler):
    def __init__(self, *args, **kwargs):
        """File handler of the pre-processed STRAW file."""
        self._time_ = None
        self._trb_rate_up_0_ = None
        self._trb_rate_down_0_ = None

        # comes last to load the data in case file_name is set
        BaseFileHandler.__init__(self, *args, **kwargs)

    @property
    def time(self, ):
        """Absolut timestamp as seconds since epoch"""
        return self._time_

    @property
    def rate_up(self, ):
        """Rate in Hz of the upwards facing PMT in the SDOM."""
        return self._trb_rate_up_0_

    @property
    def rate_down(self, ):
        """Rate in Hz of the downwards facing PMT in the SDOM."""
        return self._trb_rate_down_0_

    def __load_meta_data__(self, ):
        """Try to load the file with different versions."""
        err_list = []
        for i in [self.__load_meta_data_v1__]:
            try:
                i()  # try file versions
                return
            # version is detected because datasets in the hdf5 aren't present -> i() fails with KeyError
            except (TypeError, KeyError) as a:
                err_list.append(a.args[0])

        raise KeyError('; '.join(err_list))

    def __load_meta_data_v1__(self, ):
        """Load a pre-processed STRAW / SDOM file."""
        self.file_version = 1

        self._time_ = self.file['trb_time']
        self._trb_rate_up_0_ = self.file['trb_rate_up_0']
        self._trb_rate_down_0_ = self.file['trb_rate_down_0']
