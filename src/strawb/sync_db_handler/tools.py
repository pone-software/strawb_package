import numpy as np


def to_numeric(value):
    """Try to convert a string to a numeric type."""
    out = value
    if isinstance(value, str):
        try:
            out = complex(value)
        except ValueError:
            pass
        else:
            if 'j' not in value:
                if '.' in value or 'e' in value.lower():
                    out = float(value)
                else:
                    out = int(value)
    return out


def unpack_options(option_str, convert_numeric=True):
    """Converts a string to dictionary. The string is interpreted as follows:
    - Each item (i.e.: key: value) is seperated by a '_'
    - The key and value is seperated by a '-'. It also supports Flags, (e.g. '_key2_')
      or arrays (e.g.: 'key3-value3.0-value3.1-value3.2')

    PARAMETER
    ---------
    option_str: str
        string to unpack to options from
    RETURN
    ------
    option_dict: dict
        dictionary with options extracted from the string

    EXAMPLE
    -------
    Input: 'key1-value1_key2_key3-value3.0-value3.1-value3.2'
    Output: {'key1': 'value1', 'key2': True, 'key3': ['value3.0', 'value3.1', 'value3.2']}
    """
    def parse_values(value):
        if convert_numeric:
            return to_numeric(value)
        return value

    option_dict = {}
    if isinstance(option_str, str):
        for j in option_str.split('_'):
            j_split = j.split('-')
            if len(j_split) == 1:
                option_dict[j_split[0]] = True
            elif len(j_split) == 2:
                option_dict[j_split[0]] = parse_values(j_split[1])
            elif len(j_split) >= 2:
                option_dict[j_split[0]] = [parse_values(m) for m in j_split[1:]]
            else:
                option_dict[j] = None

    return option_dict


def options_str(**option_dict):
    """Converts a dictonary to a string. The string is generated as follows:
    - Each item (i.e.: key: value) is seperated by a '_'
    - The key and value is seperated by a '-'. It also suports Flags (e.g. '_key2_')
      or arrays (e.g.: 'key3-value3.0-value3.1-value3.2')

    EXAMPLE
    -------
    >>> options = {'key1': 'value1', 'key1b': 1, 'key1c': 1.1, 'key1d': 1.1j,
    >>>           'key2': True, 'key2b': False, 'key2c': np.bool8(1), 'key2d': np.bool_(1),
    >>>           'key3': ['value3.0', 'value3.1', 'value3.2'], 'key3b': np.arange(3)}

    >>> options_str(**options)
    'key1-value1_key1b-1.1j_key2_key2c_key2d_key3-value3.0-value3.1-value3.2_key3b-0-1-2'
    """
    items = []
    for key_i, value_i in option_dict.items():
        if isinstance(value_i, (bool, np.bool_)):
            if value_i:
                items.append(key_i)
            else:
                pass
        elif value_i is False:
            pass
        elif isinstance(value_i, (list, tuple, np.ndarray)):
            str_i = [str(key_i)]
            for j in value_i:
                str_i.append(str(j))
            items.append('-'.join(str_i))
        else:
            items.append(f'{key_i}-{value_i}')

    return '_'.join(items)
