from strawb.base_file_handler import BaseFileHandler


class Lucifer:
    def __init__(self, id=None):
        self.id = id  # i.e. 51, 52, 53, 54
        self.current = None
        self.current_mA = None
        self.duration = None
        self.duration_seconds = None
        self.mode = None
        self.time = None

    def __load_meta_data__(self, file):
        self.current = file[f'lucifer_{self.id}/current']
        self.current_mA = file[f'lucifer_{self.id}/current_mA']
        self.duration = file[f'lucifer_{self.id}/duration']
        self.duration_seconds = file[f'lucifer_{self.id}/duration_seconds']
        self.mode = file[f'lucifer_{self.id}/mode']
        self.time = file[f'lucifer_{self.id}/time']


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

        # list of lucifer instances
        self.lucifer_list = None

        # comes last to load the data in case file_name is set
        BaseFileHandler.__init__(self, *args, **kwargs)

    def __load_meta_data__(self, ):
        # accel
        self.accel_time = self.file['accel/time']
        self.accel_x = self.file['accel/x']
        self.accel_y = self.file['accel/y']
        self.accel_z = self.file['accel/z']

        # magneto
        self.magneto_time = self.file['magneto/time']
        self.magneto_x = self.file['magneto/x']
        self.magneto_y = self.file['magneto/y']
        self.magneto_z = self.file['magneto/z']

        # pth
        self.pth_time = self.file['pth/time']
        self.pth_humidity = self.file['pth/humidity']
        self.pth_pressure = self.file['pth/pressure']
        self.pth_temperature = self.file['pth/temperature']

        # pwrmoni
        self.pwrmoni_time = self.file['pwrmoni/time']
        self.pwrmoni_c2_current = self.file['pwrmoni/c2_current']
        self.pwrmoni_c2_voltage = self.file['pwrmoni/c2_voltage']
        self.pwrmoni_laser_current = self.file['pwrmoni/laser_current']
        self.pwrmoni_laser_voltage = self.file['pwrmoni/laser_voltage']
        self.pwrmoni_motor_current = self.file['pwrmoni/motor_current']
        self.pwrmoni_motor_voltage = self.file['pwrmoni/motor_voltage']
        self.pwrmoni_padiwa_current = self.file['pwrmoni/padiwa_current']
        self.pwrmoni_padiwa_voltage = self.file['pwrmoni/padiwa_voltage']
        self.pwrmoni_switch_current = self.file['pwrmoni/switch_current']
        self.pwrmoni_switch_voltage = self.file['pwrmoni/switch_voltage']
        self.pwrmoni_trb3sc_current = self.file['pwrmoni/trb3sc_current']
        self.pwrmoni_trb3sc_voltage = self.file['pwrmoni/trb3sc_voltage']

        # temperatures: attrs = {}
        self.temperatures_time = self.file['temperatures/time']
        self.temperatures_temp1 = self.file['temperatures/temp1']
        self.temperatures_temp2 = self.file['temperatures/temp2']
        self.temperatures_temp3 = self.file['temperatures/temp3']

        # create lucifer instances, depending on which are available in the file, Lucifer(ID) from hdf5 group lucifer_ID
        self.lucifer_list = []
        for i in self.file:
            if 'lucifer' in i:
                lucifer_i = Lucifer(int(i.replace('lucifer_', '')))
                lucifer_i.__load_meta_data__(self.file)
                self.lucifer_list.append(lucifer_i)
