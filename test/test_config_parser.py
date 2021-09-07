from unittest import TestCase

from src.strawb.config_parser import Config


class TestConfigParser(TestCase):

    def test_basic(self):
        members = [attr for attr in dir(Config)
                   if not callable(getattr(Config, attr)) and not attr.startswith("__")]

        for i in members:
            value = Config.__getattribute__(Config, i)
            print(f'{i:30s} : {value}')

            if i == 'onc_download_threads':
                self.assertIsInstance(value, int)
            else:
                self.assertIsInstance(value, str)
