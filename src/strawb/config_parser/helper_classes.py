import configparser
import os
import types


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


class ConfigItem:
    """ Holds a config Item, basically a 'name': 'value' pair"""
    def __init__(self, name, value):
        self._name_ = name
        self._value_ = value

    def __repr__(self):
        return "<%s.%s: %r>" % (
            self.__class__.__name__, self._name_, self._value_)

    def __str__(self):
        return "%s.%s" % (self.__class__.__name__, self._name_)

    @types.DynamicClassAttribute
    def name(self):
        """The name of the Enum member."""
        return self._name_

    @types.DynamicClassAttribute
    def value(self):
        """The value of the Enum member."""
        return self._value_
