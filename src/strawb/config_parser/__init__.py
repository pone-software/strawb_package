import configparser
import os
from enum import Enum


class ModConfigParser(configparser.ConfigParser):
    """Adds type conversation to configparser.ConfigParser.get"""
    def get(self, *args, dtype: type = str, **kwargs):
        """Adds type conversation to configparser.ConfigParser.get"""
        value = configparser.ConfigParser.get(self, *args, **kwargs)
        return dtype(value)


class ConfigParser:
    """Pars the config file and detects the location of the config file
    (either at '~/.strawb/config' or repository home."""
    config = ModConfigParser()
    config_path = os.path.expanduser('~/.strawb/config')

    # go back 3 times (the dir. structure in this repro): config_parser + strawb + src
    repository_home = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))

    # if this path doesn't exist, use the default from the repository
    if not os.path.exists(config_path):
        config_path = os.path.join(repository_home, 'config')

    # read the config file
    config.read(config_path)

    # replace the {RepositoryHome} and make all Path absolute.
    for i in config['Paths']:
        config_path = config['Paths'][i]
        config_path = config_path.format(RepositoryHome=repository_home)
        config_path = os.path.abspath(os.path.expanduser(config_path))
        config.set('Paths', i, config_path)


class Config(Enum):
    """
    Holds all configuration parameter for the python package.

    Examples
    --------
    It inherits from enum.Enum, therefore you can list all parameters with:
    >>> for member in Config:
    >>>     print(f'{member.name:30s} : {member.value}')
    """

    # PATH
    raw_data_dir = ConfigParser.config.get('Paths', 'raw_data_dir')
    proc_data_dir = ConfigParser.config.get('Paths', 'proc_data_dir')
    virtual_hdf5_dir = ConfigParser.config.get('Paths', 'virtual_hdf5_dir')
    pandas_file_sync_db = ConfigParser.config.get('Paths', 'pandas_file_sync_db')

    # ONC
    onc_token = ConfigParser.config.get('ONC', 'token')
    onc_download_threads = ConfigParser.config.get('ONC', 'threads', dtype=int)
