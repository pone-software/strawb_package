## STRAWb

STRAWb is a python module which simplifies and streamlines the work with the STRAWb data.

#### Table of Contents
1. [Example](#example)
2. [Installation](#installation)
3. [Code Structure](#code-structure)
4. [ToDo-List](#todo-list)

## Example

```python
# Download files from the ONC server
import strawb
onc_downloader = strawb.ONCDownloader(showInfo=False)

filters = {'deviceCode': 'TUMPMTSPECTROMETER002',
           'dateFrom': '2021-05-01T19:00:00.000Z',
           'dateTo': '2021-05-01T21:59:59.000Z',
           'extension': 'hdf5'}

# download in foreground
onc_downloader.download_file(filters=filters, allPages=True)
```
For more examples have a lock in the [example folder](./examples).

## Installation

### Prepare Python package
Go to the directory of [this README you are reading](README.md) is placed (basically, to the directory of the [pyproject.toml](pyproject.toml) file, but this should be the same) and run:
```bash
python3 -m build
```
This will create the files located in the folder `.egg-info`.

### Install requirements
To install the required python packages run.
```bash
pip install -r requirements.txt
```

### Install with pip
Run the following command to install the package. In case you are not in the directory of the repository replace `.` with the root directory of the package. 
```bash
pip3 install -U --user -e .
```

#### Anaconda installation
If you use an python anaconda installation `conda activate` your environment in a terminal and run:
```bash
pip install opencv-python
```
or with `sudo` if this doesn't work.

#### AssertionError: Egg-link
In case you see an `AssertionError: Egg-link`, run:
```bash
rm ~/.local/lib/pythonX.X/site-packages/H5DAQ.egg-link
```
where X.X is your python version, e.g. 3.7 and run the command from **Install with pip** again.

This problem happens if you move the source code directory after the egg-link file is created.


## Code Structure

### ONCDownloader

### Sensors
Information on the data taking with the sensors can be currently found at https://gitlab.lrz.de/strawb/mctl (TUM ressource).
Here, the example folder contains an exemplary read-out of the hdf5 data (.ipynb).

## TODO List:
* [ ] add examples
* [ ] add all sensor types
