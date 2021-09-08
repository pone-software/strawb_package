from unittest import TestCase

from src.strawb.config_parser import Config


class TestConfigParser(TestCase):
    def test_basic(self):
        """Very basic test. Just checks the correct types."""
        for member in Config:
            # # show all parameters
            # print(f'{member.name:30s} : {member.value}')

            # check that types are correct
            if member.name in ['onc_download_threads']:
                self.assertIsInstance(member.value, int)
            else:
                self.assertIsInstance(member.value, str)
