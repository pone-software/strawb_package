import configparser
import os


class Config:
    config = configparser.ConfigParser()
    path = os.path.expanduser('~/.strawb/config')

    # if this path doesn't exist, use the default from the repro
    if not os.path.exists(path):
        path = os.path.dirname(__file__)  # the config and definitions.py are in the same directory
        path = os.path.abspath(os.path.join(path, '../../..'))  # go back 3 times: config_parser + strawb + src
        path = os.path.join(path, 'config')

    config.read(path)

    for i in config['Paths']:
        path = os.path.expanduser(config['Paths'][i])
        path = os.path.abspath(path)
        config.set('Paths', i, path)

    raw_data_dir = config.get('Paths', 'raw_data_dir')
    proc_data_dir = config.get('Paths', 'proc_data_dir')

    token = config.get('ONC', 'token')
