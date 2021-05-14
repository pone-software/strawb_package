import configparser
import os


class Config:
    config = configparser.ConfigParser()
    path = os.path.expanduser('~/.strawb/config')

    # go back 3 times: config_parser + strawb + src
    repository_home = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
    print(repository_home)
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

    token = config.get('ONC', 'token')

print(Config.raw_data_dir)