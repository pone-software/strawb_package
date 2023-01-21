from unittest import TestCase

from src.strawb.sync_db_handler.tools import *


def shared_items(dict_a, dict_b):
    return {k: dict_a[k] for k in dict_a if k in dict_b and str(dict_a[k]) == str(dict_b[k])}


class TestDBHandlerTools(TestCase):
    def setUp(self) -> None:
        self.option_dict = {'key1': 'value1', 'key1b': 1, 'key1c': 1.1, 'key1d': 1.1j,
                            'key2': True, 'key2b': False, 'key2c': np.bool8(1), 'key2d': np.bool_(1),
                            'key3': ['value3.0', 'value3.1', 'value3.2'], 'key3b': np.arange(3)}
        self.option_str = 'key1-value1_key1b-1_key1c-1.1_key1d-1.1j_' \
                          'key2_key2c_key2d_' \
                          'key3-value3.0-value3.1-value3.2_key3b-0-1-2'

    def test_to_numeric(self):
        x = ['a', 1, 2., 3.j, 3e3]
        x_str = [str(i) for i in x]
        self.assertEqual(str(x), str(to_numeric(x)))

    def test_unpack_options(self):
        option_dict = unpack_options(self.option_str)
        test_dict = self.option_dict.copy()
        test_dict.pop('key2b')  # keys set to false are not added to the str
        option_dict['key3b'] = np.array(option_dict['key3b'])  # np.array are lists
        self.assertEqual(str(test_dict), str(option_dict))

    def test_options_str(self):
        option_str = options_str(**self.option_dict)
        self.assertEqual(option_str, self.option_str)
