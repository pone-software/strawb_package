import numpy as np

class Config:
    def __init__(self, device_code) -> None:
        self.mask_mounting = None
        
        # [x, y] coordinate of the module above the camera
        self.position_module = None
        
        # [x, y] coordinates of the data cable close to the camera
        # and it goes to self.position_module
        self.position_data_cable = None
        
        # [x, y] coordinates of the steel cable close to the camera
        # and it goes to self.position_module
        self.position_steel_cable = None
        
        # load data and set parameters
        with np.load('mounting_mask.npz') as f:
            if device_code in f:
                self.mask_mounting = f[device_code]
        
        if device_code == 'TUMPMTSPECTROMETER001':
            self.position_module = np.array([355.20968475,
                                             690.49202575])
            
            self.position_data_cable = np.array([625, 300])
            self.position_steel_cable = np.array([678, 320])
        
        elif device_code == 'TUMPMTSPECTROMETER002':
            pass
        
        elif device_code == 'TUMMINISPECTROMETER001':
            pass

    @staticmethod
    def get_line(p_0, p_1):
        """Combine two points into a line. p_i = [x, y]; line = [[x_0, x_1], [y_0, y_1]]"""
        return np.array([p_0, p_1]).T
    
    @property
    def data_cable(self):
        """Start and stop coordinates of the data cable."""
        if self.position_module is not None and self.position_data_cable is not None:
            return np.array([self.position_module, self.position_data_cable]).T
        else:
            return None
    
    @property
    def steel_cable(self):
        """Start and stop coordinates of the steel cable."""
        if self.position_module is not None and self.position_steel_cable is not None:
            return np.array([self.position_module, self.position_steel_cable]).T
        else:
            return None