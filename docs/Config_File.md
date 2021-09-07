# Config File

This package use a file to define some basic settings like directories for the files, ONC token, and more. If there is a file `~/.strawb/config` it takes the parameters from there. If the file doesn't exist, it takes the default [config file](/config) from the repository which come with the code.

The config file needs the following shape and entries.
```bash
# Config File for the STRAWb package; see `docs/Config_File.md` for more information

[Paths]
home_dir: {RepositoryHome}
# home_dir: ~/strawb
raw_data_dir: %(home_dir)s/raw_module_data
proc_data_dir: %(home_dir)s/processed_data

[ONC]
token: 0db751f8-9430-47af-bc11-ed6691b38e22
threads: 4
```

## General Usage
The [config parser](/src/strawb/config_parser/__init__.py) use the [configparser](https://docs.python.org/3/library/configparser.html) which comes with every Python installation. Some points for a simple start:
- To comment a line use `#` like in Python
- Strings like `{RepositoryHome}` are placeholders like in a Python string ` 'a={a:.2}'.format(a=1.234)`. The config parser replace those strings, i.e., with something like `.format(RepositoryHome=repository_home)`
- `%(home_dir)s` is the "interpolation of values" done by the [configparser](https://docs.python.org/3/library/configparser.html). It enables values to contain format strings which refer to other values in the same section.

## Paths
| key | explanation
|---|---|
| home_dir | Is the STRAWb home dir to make relative path within the config file possible like `raw_data_dir` and `proc_data_dir`. By default its the `RepositoryHome`.|
| raw_data_dir | The place where the files downloaded form the ONC DB end up. And its also the place where the code looks for the raw files when processing the data.|
| proc_data_dir | The directory to store processed date | 
| virtual_hdf5_dir | The directory to the virtual hdf5 files |

## ONC
| key | explanation
|---|---|
| token | our personal onc token. [Where can I find my token?](/docs/ONC_Readme.md#Where can I find my token?) |
| threads | The number of threads for the ONC download. Threads share a CPU ( and the same network connection) therefore, higher numbers aren't faster. But some threads do the job faster than only one.|

