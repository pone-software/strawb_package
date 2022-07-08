from .file_handler import FileHandler


class PowerDevice:
    def __init__(self, name, time, current, voltage):
        self.name = name
        self.time = time
        self.current = current
        self.voltage = voltage

    @property
    def watt(self):
        return self.current * self.voltage  # its hdf5.datasets -> [:]

    @property
    def power(self):
        return self.watt


class Power:
    def __init__(self, file):
        self.file_handler = None
        if isinstance(file, str):
            self.file_handler = FileHandler(file_name=file)
        else:
            self.file_handler = file

        self.odroid = None
        self.laser = None
        self.motor = None
        self.padiwa = None
        self.switch = None
        self.trb3sc = None

        if self.file_handler is not None:
            self.load_data()

    @property
    def all_devices_list(self):
        return [self.odroid, self.laser, self.motor, self.padiwa, self.switch, self.trb3sc]

    def dev_map(self, name, module=None):
        if module is not None:
            module = str(module)
        elif self.file_handler is not None:
            module = self.file_handler.module
        else:
            module = ''

        dev_map = {'c2': 'Odroid'}
        if 'pmtspec' in module.lower():
            dev_map.update({'laser': 'HV-PMT-Supplies',
                            'motor': 'Lucifer'})
        elif 'lidar' in module.lower():
            dev_map.update({'motor': 'Motor+Lucifer'})
        elif 'minispec' in module.lower():
            dev_map.update({'motor': 'Lucifer'})

        if name.lower() in dev_map:
            return dev_map[name.lower()]
        return name

    def load_data(self,):
        # Both pwrmoni_XXX_current and pwrmoni_XXX_voltage can be DataSets -> [:]
        # pwrmoni_XXX_current and pwrmoni_XXX_voltage are in units mA and mV, respecify -> / 1e3
        self.odroid = PowerDevice(name='C2',
                                  time=self.file_handler.pwrmoni_time[:],
                                  current=self.file_handler.pwrmoni_c2_current[:] / 1e3,
                                  voltage=self.file_handler.pwrmoni_c2_voltage[:] / 1e3)

        self.laser = PowerDevice(name='Laser',
                                 time=self.file_handler.pwrmoni_time[:],
                                 current=self.file_handler.pwrmoni_laser_current[:] / 1e3,
                                 voltage=self.file_handler.pwrmoni_laser_voltage[:] / 1e3)

        self.motor = PowerDevice(name='Motor',
                                 time=self.file_handler.pwrmoni_time[:],
                                 current=self.file_handler.pwrmoni_motor_current[:] / 1e3,
                                 voltage=self.file_handler.pwrmoni_motor_voltage[:] / 1e3)

        self.padiwa = PowerDevice(name='PADIWA',
                                  time=self.file_handler.pwrmoni_time[:],
                                  current=self.file_handler.pwrmoni_padiwa_current[:] / 1e3,
                                  voltage=self.file_handler.pwrmoni_padiwa_voltage[:] / 1e3)

        self.switch = PowerDevice(name='Switch',
                                  time=self.file_handler.pwrmoni_time[:],
                                  current=self.file_handler.pwrmoni_switch_current[:] / 1e3,
                                  voltage=self.file_handler.pwrmoni_switch_voltage[:] / 1e3)

        self.trb3sc = PowerDevice(name='TRB3sc',
                                  time=self.file_handler.pwrmoni_time[:],
                                  current=self.file_handler.pwrmoni_trb3sc_current[:] / 1e3,
                                  voltage=self.file_handler.pwrmoni_trb3sc_voltage[:] / 1e3)
