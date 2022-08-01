from typing import Union

# from strawb.sensors.muontracker.muon_tracker_trb_rates import MuonTrackerTRBRates
from strawb.sensors.muontracker.file_handler import FileHandler


class MuonTracker:
    # FileHandler = FileHandler

    def __init__(self, file: Union[str, FileHandler] = None, name=''):
        self.name = name

        if isinstance(file, str):
            self.file_handler = FileHandler(file_name=file)
        else:
            self.file_handler = file

        # self.trb_rates = MuonTrackerTRBRates(file_handler=self.file_handler)
