import h5py
import pandas


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

        self.version = None

    def __load_meta_data__(self, file):
        for i in [self.__load_meta_data_v2__]:
            try:
                i(file)  # try file versions
                return
            # version is detected because datasets in the hdf5 aren't present -> i() fails with KeyError
            except (KeyError, TypeError) as a:
                pass

        self.__load_meta_data_v1__(file)  # try with file default version

    def __load_meta_data_v1__(self, file):
        self.current = file[f'lucifer_{self.id}/current']
        self.duration = file[f'lucifer_{self.id}/duration']
        self.mode = file[f'lucifer_{self.id}/mode']
        self.time = file[f'lucifer_{self.id}/time']

        self.version = 1  # starts with 2 as it is a subclass

    def __load_meta_data_v2__(self, file):
        """
        CHANGES to v1:
        added: `current_mA` and `duration_seconds`
        """
        self.current = file[f'lucifer_{self.id}/current']
        self.duration = file[f'lucifer_{self.id}/duration']
        self.mode = file[f'lucifer_{self.id}/mode']
        self.time = file[f'lucifer_{self.id}/time']

        # some older versions doesn't have `current_mA` and `duration_seconds`
        self.current_mA = file[f'lucifer_{self.id}/current_mA']
        self.duration_seconds = file[f'lucifer_{self.id}/duration_seconds']

        self.version = 2  # starts with 2 as it is a subclass

    def get_dataframe(self):
        data_dict = {}
        for i in ['id', 'current', 'current_mA', 'duration', 'duration_seconds', 'mode', 'time']:
            if isinstance(self.__getattribute__(i), h5py.Dataset):
                if i is 'time':
                    data_dict.update({i: self.__getattribute__(i).asdatetime()[:]})
                else:
                    data_dict.update({i: self.__getattribute__(i)[:]})
            else:
                data_dict.update({i: self.__getattribute__(i)})
        return pandas.DataFrame(data_dict)
