from strawb.base_file_handler import BaseFileHandler


class FileHandler(BaseFileHandler):
    def __init__(self, *args, **kwargs):
        # TRB_DAQ
        self.daq_frequency_pmt = None
        self.daq_frequency_trigger = None
        self.daq_pmt = None
        self.daq_pulser_readout = None
        self.daq_pulser_trigger = None
        self.daq_state = None
        self.daq_time = None
        self.daq_trb = None

        # Gimbal
        self.gimbal_delay = None
        self.gimbal_pos_x = None
        self.gimbal_pos_y = None
        self.gimbal_power = None
        self.gimbal_time = None

        # Laser
        self.laser_diode = None
        self.laser_frequency = None
        self.laser_power = None
        self.laser_pulsewidth = None
        self.laser_set_adjust_x = None
        self.laser_set_adjust_y = None
        self.laser_time = None

        # comes last to load the data in case file_name is set
        BaseFileHandler.__init__(self, *args, **kwargs)

    def __load_meta_data__(self, ):
        # TRB_DAQ
        self.daq_frequency_pmt = self.file['daq/frequency_pmt']
        self.daq_frequency_trigger = self.file['daq/frequency_trigger']
        self.daq_pmt = self.file['daq/pmt']
        self.daq_pulser_readout = self.file['daq/pulser_readout']
        self.daq_pulser_trigger = self.file['daq/pulser_trigger']
        self.daq_state = self.file['daq/state']
        self.daq_time = self.file['daq/time']
        self.daq_trb = self.file['daq/trb']

        # Gimbal
        self.gimbal_delay = self.file['gimbal/delay']
        self.gimbal_pos_x = self.file['gimbal/pos_x']
        self.gimbal_pos_y = self.file['gimbal/pos_y']
        self.gimbal_power = self.file['gimbal/power']
        self.gimbal_time = self.file['gimbal/time']

        # Laser
        self.laser_diode = self.file['laser/diode']
        self.laser_frequency = self.file['laser/frequency']
        self.laser_power = self.file['laser/power']
        self.laser_pulsewidth = self.file['laser/pulsewidth']
        self.laser_set_adjust_x = self.file['laser/set_adjust_x']
        self.laser_set_adjust_y = self.file['laser/set_adjust_y']
        self.laser_time = self.file['laser/time']
