from strawb.basefilehandler import BaseFileHandler
import h5py


class FileHandler(BaseFileHandler):
    def __init__(self, *args, **kwargs):
        # accel
        self.accel_time = None
        self.accel_x = None
        self.accel_y = None
        self.accel_z = None

        # magneto
        self.magneto_time = None
        self.magneto_x = None
        self.magneto_y = None
        self.magneto_z = None

        # pth
        self.pth_time = None
        self.pth_humidity = None
        self.pth_pressure = None
        self.pth_temperature = None

        # pwrmoni
        self.pwrmoni_c2_current = None
        self.pwrmoni_c2_voltage = None
        self.pwrmoni_laser_current = None
        self.pwrmoni_laser_voltage = None
        self.pwrmoni_motor_current = None
        self.pwrmoni_motor_voltage = None
        self.pwrmoni_padiwa_current = None
        self.pwrmoni_padiwa_voltage = None
        self.pwrmoni_switch_current = None
        self.pwrmoni_switch_voltage = None
        self.pwrmoni_time = None
        self.pwrmoni_trb3sc_current = None
        self.pwrmoni_trb3sc_voltage = None

        # temperatures: attrs = {}
        self.temperatures_time = None
        self.temperatures_temp1 = None
        self.temperatures_temp2 = None
        self.temperatures_temp3 = None

        # comes last to load the data in case file_name is set
        BaseFileHandler.__init__(self, *args, **kwargs)

    def load_meta_data(self, ):
        with h5py.File(self.file_name, 'r') as f:
            # accel
            self.accel_time = self.timestamp2datetime64(f['accel/time'][:])
            self.accel_x = f['accel/x'][:]
            self.accel_y = f['accel/y'][:]
            self.accel_z = f['accel/z'][:]

            # magneto
            self.magneto_time = self.timestamp2datetime64(f['magneto/time'][:])
            self.magneto_x = f['magneto/x'][:]
            self.magneto_y = f['magneto/y'][:]
            self.magneto_z = f['magneto/z'][:]

            # pth
            self.pth_time = self.timestamp2datetime64(f['pth/time'][:])
            self.pth_humidity = f['pth/humidity'][:]
            self.pth_pressure = f['pth/pressure'][:]
            self.pth_temperature = f['pth/temperature'][:]

            # pwrmoni
            self.pwrmoni_time = self.timestamp2datetime64(f['pwrmoni/time'][:])
            self.pwrmoni_c2_current = f['pwrmoni/c2_current'][:]
            self.pwrmoni_c2_voltage = f['pwrmoni/c2_voltage'][:]
            self.pwrmoni_laser_current = f['pwrmoni/laser_current'][:]
            self.pwrmoni_laser_voltage = f['pwrmoni/laser_voltage'][:]
            self.pwrmoni_motor_current = f['pwrmoni/motor_current'][:]
            self.pwrmoni_motor_voltage = f['pwrmoni/motor_voltage'][:]
            self.pwrmoni_padiwa_current = f['pwrmoni/padiwa_current'][:]
            self.pwrmoni_padiwa_voltage = f['pwrmoni/padiwa_voltage'][:]
            self.pwrmoni_switch_current = f['pwrmoni/switch_current'][:]
            self.pwrmoni_switch_voltage = f['pwrmoni/switch_voltage'][:]
            self.pwrmoni_trb3sc_current = f['pwrmoni/trb3sc_current'][:]
            self.pwrmoni_trb3sc_voltage = f['pwrmoni/trb3sc_voltage'][:]

            # temperatures: attrs = {}
            self.temperatures_time = self.timestamp2datetime64(f['temperatures/time'][:])
            self.temperatures_temp1 = f['temperatures/temp1'][:]
            self.temperatures_temp2 = f['temperatures/temp2'][:]
            self.temperatures_temp3 = f['temperatures/temp3'][:]
