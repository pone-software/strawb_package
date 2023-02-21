import os


class DatasetHandler:
    """
    Basic class to load a Dataset.

    config_parameters is a DataFrame with the columns:
    time-ns,optical_power-mW,label

    Class must be inherited and adopted with (see the example with x and y which is commented out):
    - overloading _load_data_ see the example commented out
    - define the properties and supply docstrings
    """
    local_path = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    config_parameters = None  # should be overloaded with: pandas.read_csv(os.path.join(local_path,file_name))
    available_labels = []  # should be overloaded with: list(config_parameters['label'].unique())

    def __init__(self, label=None):
        # set the label and check if it is a valid label
        self.label = label

    # example if the dataset has two values: x and y
    # the properties block setting the values from outside and provide a docstring with help
    # @property
    # def x(self):
    #     """x in m (meter)"""
    #     return self._x_

    # @property
    # def y(self):
    #     """x in m (meter)"""
    #     return self._y_

    def _load_data_(self, mask):
        """Must be overloaded to map the data to the correct properties"""
        # self._x_ = self.config_parameters.x[mask]
        # self._y_ = self.config_parameters.y[mask]
        pass

    def _free_data_(self):
        """Must be overloaded to free the data"""
        # self._x_ = None
        # self._y_ = None
        pass

    @property
    def label(self):
        """label of the data in the config_parameters dataset"""
        return self._label_

    @label.setter
    def label(self, label):
        """Set the label and loads the data from the config_parameters dataset
        Label must be a value in config_parameters.label or None."""
        if label is None:
            self._free_data_()
        elif label is not None:
            if label not in self.available_labels:
                raise ValueError(f'label must be one of: {self.available_labels}. Got: {label}')
            mask = self.config_parameters['label'] == label
            self._label_ = label
            self._load_data_(mask)
