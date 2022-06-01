from strawb.config_parser.helper_classes import ConfigParser, ConfigItem


class Config:
    """
    Holds all configuration parameter for the python package.

    Examples
    --------
    You can list all parameters with:
    >>> print(Config())  # also without print in Notebooks
    or
    >>> for config_item in Config.to_list():
    >>>     print(f'{config_item.name:30s} : {config_item.value}')
    """

    # PATH
    raw_data_dir = ConfigParser.config.get('Paths', 'raw_data_dir')
    proc_data_dir = ConfigParser.config.get('Paths', 'proc_data_dir')
    virtual_hdf5_dir = ConfigParser.config.get('Paths', 'virtual_hdf5_dir')
    pandas_file_sync_db = ConfigParser.config.get('Paths', 'pandas_file_sync_db')

    # ONC
    onc_token = ConfigParser.config.get('ONC', 'token')
    onc_download_threads = ConfigParser.config.get('ONC', 'threads', dtype=int)

    @classmethod
    def to_list(cls):
        """Returns a list with [ConfigItem(variable name, variable value),...] of all variables in the Config class"""
        return [ConfigItem(name=attr, value=getattr(cls, attr)) for attr in dir(cls) if
                not callable(getattr(cls, attr)) and not attr.startswith("__")]

    @classmethod
    def to_dict(cls):
        """Returns a dict with {variable name: variable value} of all variables in the Config class"""
        return {attr: getattr(cls, attr) for attr in dir(cls) if
                not callable(getattr(cls, attr)) and not attr.startswith("__")}

    def __repr__(self):
        out = 'STRAWb Config\n-------------\n'
        out += '\n'.join([f'{k:21}: {v}' for k, v in self.to_dict().items()])
        return out