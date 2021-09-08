from strawb.base_file_handler import BaseFileHandler


class Lucifer:
    # The following parameters are from the data sheet of the LM2759. A LED adjustable current driver.
    # https://www.ti.com/lit/ds/symlink/lm2759.pdf?ts=1619016957182&ref_url=https%253A%252F%252Fwww.ti.com%252Fproduct%252FLM2759
    # In TORCH mode the current mapping is different to FLASH, i.e. torch_current_dict vs. flash_current_dict
    # In TORCH mode the duration of the flash is NOT limited and has to be done manually with OFF.
    # !! Do not wait too long to send the OFF signal as 180 mA is still quite a lot. !!
    # In FLASH mode the duration is limited with an adjustable timeout aka. 'duration', i.e. flash_timeout_dict
    # In FLASH mode still the OFF cmd can be sent before the timeout to disable the flash.

    # Flasher Modes
    mode_dict = {'OFF': 0, 'TORCH': 1, 'FLASH': 2}

    # Unit: [A]; From: lm2759 Data-Sheet -> p12 -> Table 2. Flash Current Table (Reg xB0)
    flash_current_dict = {0x00: .080,
                          0x01: .150,
                          0x02: .220,
                          0x03: .280,
                          0x04: .350,
                          0x05: .410,
                          0x06: .470,
                          0x07: .530,
                          0x08: .590,
                          0x09: .650,
                          0x0A: .710,
                          0x0B: .770,
                          0x0C: .830,
                          0x0D: .890,
                          0x0E: .950,
                          0x0F: 1.010}

    # Unit: [A]; From: lm2759 Data-Sheet -> p13 -> Table 3. Torch Current Table (Reg xA0)
    torch_current_dict = {0x00: .015,
                          0x01: .030,
                          0x02: .040,
                          0x03: .050,
                          0x04: .065,
                          0x05: .080,
                          0x06: .090,
                          0x07: .100,
                          0x08: .110,
                          0x09: .120,
                          0x0A: .130,
                          0x0B: .140,
                          0x0C: .150,
                          0x0D: .160,
                          0x0E: .170,
                          0x0F: .180}

    # Unit: [seconds]; From: lm2759 Data-Sheet -> p13 -> Table 4. Flash Timeout Duration (Reg xC0)
    flash_timeout_dict = {0x00: .060,
                          0x01: .125,
                          0x02: .250,
                          0x03: .375,
                          0x04: .500,
                          0x05: .625,
                          0x06: .750,
                          0x07: 1.100}

    def __init__(self, lucifer_id=None):
        self.id = lucifer_id  # i.e. 51, 52, 53, 54
        self.current = None
        self.current_mA = None
        self.duration = None
        self.duration_seconds = None
        self.mode = None
        self.time = None

    def __load_meta_data__(self, file):
        self.current = file[f'lucifer_{self.id}/current']
        self.duration = file[f'lucifer_{self.id}/duration']
        self.mode = file[f'lucifer_{self.id}/mode']
        self.time = file[f'lucifer_{self.id}/time']

        # some older versions doesn't have `current_mA` and `duration_seconds`
        try:
            self.current_mA = file[f'lucifer_{self.id}/current_mA']
        except KeyError:
            pass

        try:
            self.duration_seconds = file[f'lucifer_{self.id}/duration_seconds']
        except KeyError:
            pass


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
