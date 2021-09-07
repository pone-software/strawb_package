import configparser
import os


class Config:
    config = configparser.ConfigParser()
    path = os.path.expanduser('~/.strawb/config')

    # go back 3 times (the dir. structure in this repro): config_parser + strawb + src
    repository_home = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))

    # if this path doesn't exist, use the default from the repository
    if not os.path.exists(path):
        path = os.path.join(repository_home, 'config')

    config.read(path)

    for i in config['Paths']:
        path = config['Paths'][i]
        path = path.format(RepositoryHome=repository_home)
        path = os.path.abspath(os.path.expanduser(path))
        config.set('Paths', i, path)

    raw_data_dir = config.get('Paths', 'raw_data_dir')
    proc_data_dir = config.get('Paths', 'proc_data_dir')
    virtual_hdf5_dir = config.get('Paths', 'virtual_hdf5_dir')
    pandas_file_sync_db = os.path.join(raw_data_dir, 'pandas_file_sync_db.gz')

    # ONC
    onc_token = config.get('ONC', 'token')
    onc_download_threads = int(config.get('ONC', 'threads'))

    del i, config  # clean up non config variables
