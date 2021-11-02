import pandas

from strawb.base_file_handler import BaseFileHandler


class FileHandler(BaseFileHandler):
    def __init__(self, *args, **kwargs):
        # TRB_DAQ
        self.daq_time = None
        self.daq_measured_frequency_pmt = None  # Removed from hdf5 ~05.10.2021, as moved to counts reading
        self.daq_measured_frequency_trigger = None  # Removed from hdf5 ~05.10.2021, as moved to counts reading
        self.daq_pmt = None  # PMT is; 0: OFF; 1: ON
        self.daq_frequency_readout = None  # the frequency when the TRB counts up counts channel 0
        self.daq_frequency_trigger = None  # the frequency of the trigger pin controlled by the TRB
        self.daq_state = None  # 0: TRB not ready; 1: TRB ready; 2: TRB takes hld
        self.daq_trb = None  # TRB power; 0: OFF; 1: ON

        # Gimbal
        self.gimbal_time = None
        self.gimbal_delay = None  # delay between two steps (TODO: should be checked what it is exactly)
        self.gimbal_pos_x = None  # TODO: theta or phi
        self.gimbal_pos_y = None  # TODO: theta or phi
        self.gimbal_power = None  # if the power is en-/disabled

        # Laser
        self.laser_time = None
        self.laser_diode = None  # diode readings to calibrate the intensity. Gimbal is be in calibration position.
        self.laser_frequency = None  # if the power is en-/disabled
        self.laser_power = None  # if the laser power is en-/disabled
        self.laser_pulsewidth = None  # sets the intensity
        self.laser_set_adjust_x = None  # sets the laser alignment in X with the PMT axis
        self.laser_set_adjust_y = None  # sets the laser alignment in Y with the PMT axis

        # PMT TOT (time over threshold), each entry is a separated event. Added to hdf5 ~05.10.2021.
        # -> File version 2
        self.tot_time = None  # absolute timestamps in seconds for the event
        self.tot_time_ns = None  # timestamps from trb in seconds for the event, not absolut and with overflow
        self.tot_tot = None  # time over threshold (tot) in ns for the event

        # Counter, similar to PMTSpectrometer. Added to hdf5 ~05.10.2021.
        # -> File version 2
        self.counts_time = None  # absolute timestamps in seconds for each counts reading
        self.counts_ch0 = None  # channel which counts up at a constant frequency -> PMT Spectrometer
        self.counts_ch17 = None  # the readout/PMT channel.
        self.counts_ch18 = None  # the Laser trigger channel.

        # Measurement step log. To store the beginning and end of a measurement step. Introduced at 11.10.2021.
        # -> File version 3
        self.measurement_time = None
        self.measurement_step = None

        # holds the file version
        self.file_version = None

        # comes last to load the data in case file_name is set
        BaseFileHandler.__init__(self, *args, **kwargs)

    def __load_meta_data__(self, ):
        # order is important, tries to load newest first and oldest latest.
        for i in [self.__load_meta_data_v4__, self.__load_meta_data_v3__, self.__load_meta_data_v2__]:
            try:
                i()  # try file versions
                return
            # version is detected because datasets in the hdf5 aren't present -> i() fails with KeyError
            except KeyError as a:
                pass

        self.__load_meta_data_v1__()  # try with file default version

    # ---- The functions for different versions ----
    def __load_meta_data_v1__(self, ):
        """Loads the initial SDAQ-hdf5 File Version"""

        # load the single hdf5 groups
        self.__load_meta_data_daq_v1__()  # TRB_DAQ
        self.__load_meta_data_gimbal__()  # Gimbal
        self.__load_meta_data_laser__()  # Laser
        self.file_version = 1

    def __load_meta_data_v2__(self, ):
        """Loads the SDAQ-hdf5 version 2 introduced beginning of October 2021.

        CHANGES in respect to version 1
        -------------------------------
        removed: @TRB_DAQ - 'daq/frequency_pmt' and 'daq/frequency_trigger'
        added: TOT - tot_time, tot_time_ns, tot_tot
        added: COUNTS - counts_ch0, counts_ch17, counts_ch18, counts_time
        """
        # load the single hdf5 groups
        self.__load_meta_data_daq_v2__()  # TRB_DAQ
        self.__load_meta_data_gimbal__()  # Gimbal
        self.__load_meta_data_laser__()  # Laser
        self.__load_meta_data_counts__()  # counts
        self.__load_meta_data_tot__()  # TOT
        self.file_version = 2

    def __load_meta_data_v3__(self, ):
        """Loads the SDAQ-hdf5 version 3 introduced from 11th of October 2021.

        CHANGES in respect to version 2
        -------------------------------
        added: measurement - measurement_time, measurement_step
        """
        self.__load_meta_data_measurement__()
        self.__load_meta_data_v2__()
        self.file_version = 3

    def __load_meta_data_v4__(self, ):
        """Loads the SDAQ-hdf5 version 4 introduced from 25th of October 2021.

        CHANGES in respect to version 3
        -------------------------------
        renamed: @TRB_DAQ - 'daq/pulser_readout' -> 'daq/frequency_readout'
        renamed: @TRB_DAQ - 'daq/pulser_trigger' -> 'daq/frequency_trigger'
        """
        # load the single hdf5 groups
        self.__load_meta_data_daq_v3__()  # TRB_DAQ
        self.__load_meta_data_gimbal__()  # Gimbal
        self.__load_meta_data_laser__()  # Laser
        self.__load_meta_data_counts__()  # counts
        self.__load_meta_data_tot__()  # TOT
        self.__load_meta_data_measurement__()
        self.file_version = 4

    # ---- Helper functions for load ----
    def __load_meta_data_gimbal__(self):
        # Gimbal
        self.gimbal_delay = self.file['gimbal/delay']
        self.gimbal_pos_x = self.file['gimbal/pos_x']
        self.gimbal_pos_y = self.file['gimbal/pos_y']
        self.gimbal_power = self.file['gimbal/power']
        self.gimbal_time = self.file['gimbal/time']

    def __load_meta_data_laser__(self):
        # Laser
        self.laser_diode = self.file['laser/diode']
        self.laser_frequency = self.file['laser/frequency']
        self.laser_power = self.file['laser/power']
        self.laser_pulsewidth = self.file['laser/pulsewidth']
        self.laser_set_adjust_x = self.file['laser/set_adjust_x']
        self.laser_set_adjust_y = self.file['laser/set_adjust_y']
        self.laser_time = self.file['laser/time']

    def __load_meta_data_tot__(self):
        # TOT
        self.tot_time = self.file['tot/time']
        self.tot_time_ns = self.file['tot/time_ns']
        self.tot_tot = self.file['tot/tot']

    def __load_meta_data_counts__(self):
        # Counter
        self.counts_ch0 = self.file['counts/ch0']
        self.counts_ch17 = self.file['counts/ch17']
        self.counts_ch18 = self.file['counts/ch18']
        self.counts_time = self.file['counts/time']

    def __load_meta_data_measurement__(self):
        self.measurement_time = self.file['measurement/time']
        self.measurement_step = self.file['measurement/step']

    def __load_meta_data_daq_v1__(self):
        """Load the data from the TRB_DAQ hdf5 group (DAQJob). Original version."""
        self.daq_measured_frequency_pmt = self.file['daq/frequency_pmt']
        self.daq_measured_frequency_trigger = self.file['daq/frequency_trigger']
        self.daq_pmt = self.file['daq/pmt']
        self.daq_frequency_readout = self.file['daq/pulser_readout']
        self.daq_frequency_trigger = self.file['daq/pulser_trigger']
        self.daq_state = self.file['daq/state']
        self.daq_time = self.file['daq/time']
        self.daq_trb = self.file['daq/trb']

    def __load_meta_data_daq_v2__(self):
        """Load the data from the TRB_DAQ hdf5 group (DAQJob).
        CHANGES to v1: removed - 'daq/frequency_pmt' and 'daq/frequency_trigger'
        """
        self.daq_pmt = self.file['daq/pmt']
        self.daq_frequency_readout = self.file['daq/pulser_readout']
        self.daq_frequency_trigger = self.file['daq/pulser_trigger']
        self.daq_state = self.file['daq/state']
        self.daq_time = self.file['daq/time']
        self.daq_trb = self.file['daq/trb']

    def __load_meta_data_daq_v3__(self):
        """Load the data from the TRB_DAQ hdf5 group (DAQJob).
        CHANGES to v2: renamed
          - 'daq/pulser_readout' -> 'daq/frequency_readout'
          - 'daq/pulser_trigger' -> 'daq/frequency_trigger'
        """
        self.daq_pmt = self.file['daq/pmt']
        self.daq_frequency_readout = self.file['daq/frequency_readout']
        self.daq_frequency_trigger = self.file['daq/frequency_trigger']
        self.daq_state = self.file['daq/state']
        self.daq_time = self.file['daq/time']
        self.daq_trb = self.file['daq/trb']

    # ---- Define pandas DataFrame export helpers ----
    def get_pandas_daq(self):
        if self.file_version == 1:
            return pandas.DataFrame(dict(time=self.daq_time.asdatetime()[:],
                                         measured_frequency_pmt=self.daq_measured_frequency_pmt,
                                         measured_frequency_trigger=self.daq_measured_frequency_trigger,
                                         pmt=self.daq_pmt,
                                         frequency_readout=self.daq_frequency_readout,
                                         frequency_trigger=self.daq_frequency_trigger,
                                         state=self.daq_state,
                                         trb=self.daq_trb))

        elif self.file_version >= 2:
            return pandas.DataFrame(dict(time=self.daq_time.asdatetime()[:],
                                         pmt=self.daq_pmt,
                                         frequency_readout=self.daq_frequency_readout,
                                         frequency_trigger=self.daq_frequency_trigger,
                                         state=self.daq_state,
                                         trb=self.daq_trb))

    def get_pandas_gimbal(self):
        return pandas.DataFrame(dict(time=self.gimbal_time.asdatetime()[:],
                                     delay=self.gimbal_delay,
                                     pos_x=self.gimbal_pos_x,
                                     pos_y=self.gimbal_pos_y,
                                     power=self.gimbal_power, )
                                )

    def get_pandas_laser(self):
        return pandas.DataFrame(dict(time=self.laser_time.asdatetime()[:],
                                     diode=self.laser_diode,
                                     frequency=self.laser_frequency,
                                     power=self.laser_power,
                                     pulsewidth=self.laser_pulsewidth,
                                     set_adjust_x=self.laser_set_adjust_x,
                                     set_adjust_y=self.laser_set_adjust_y, )
                                )

    def get_pandas_counts(self):
        if self.file_version >= 2:
            return pandas.DataFrame(dict(time=self.counts_time.asdatetime()[:],
                                         ch0=self.counts_ch0,
                                         ch17=self.counts_ch17,
                                         ch18=self.counts_ch18)
                                    )

    def get_pandas_tot(self):
        if self.file_version >= 2:
            return pandas.DataFrame(dict(time=self.tot_time.asdatetime()[:],
                                         time_ns=self.tot_time_ns,
                                         tot=self.tot_tot,
                                         )
                                    )

    def get_pandas_measurement(self):
        if self.file_version >= 3:
            return pandas.DataFrame(dict(time=self.measurement_time.asdatetime()[:],
                                         step=self.measurement_step,
                                         )
                                    )
