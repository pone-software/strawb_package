# STRAWb

STRAWb is a python module which simplifies and streamlines the work with the STRAWb data. It also targets the LRZ infrastructure which hosts a copy of all data (some TB) and provides computational infrastructure. For more information about the LRZ and the deployed system have a look to this [LRZ Readme](docs/LRZ_Readme.md) in the docs.

### Table of Contents
1. [Code Structure](#code-structure)
2. [Example](#example)
3. [Installation](#installation)
4. [ToDo-List](#todo-list)

## Code Structure
The code consists of several submodules. The following summarise the single parts briefly, for more documentation also have a look to the [docs directory](docs).

### Config Parser
Takes care of parsing configuration parameters for the package from a config file. The sample config file with all parameters is [here](config). If there is a config-file present at `~/.strawb/config` it reads the parameters from there. If not, it takes the sample config-file.

### ONCDownloader
Takes care of downloading the files from the ONC server to a local directory. [Readme of the submodule](docs/ONC_Readme.md).

### Sensors
STRAWb consists of several Modules with different configurations of sensors. The code of the DAQ and module controlling software (MCTL) is located in [this repository](https://gitlab.lrz.de/strawb/mctl) (TUM resource, but external users can be added. Contact someone of the TUM group for access). 

Most of the sensors use `hdf5` files to store the measurements. But some sensors use other file types like `txt`, `hld`, `raw` and `png`.

To keep this Readme short, each sensor has a separated readme in the [/docs](/docs).



## Example
For examples check out the [examples' folder](examples) which includes notebooks and scripts.
- [(Script) ONC download](examples/basic_onc_download.py)
- [(Notebook) ONC download and filter](examples/ONC_Downloader_Example.ipynb)
- [(Notebook) Explore hdf5 file](examples/explore_hdf5_file.ipynb)
- [(Notebook) Explore pandas_file_sync_db](examples/explore_pandas_file_sync_db.ipynb)

## Installation
For the installation you have two options.
### Installation directly from the repository
`Pip` can direclty install the package from the repository. As `pip` only compares the version number and not the code, uninstall an existing installation before you install it from the repository. For updating the package just rerun the same commands. You can also specify the branch by changing `master` accordingly. The commands are:
```bash
pip3 uninstall -y strawb  # Uninstall an existing installation
pip3 install -U git+git://github.com/pone-software/strawb_package.git@master  # Install it from the repro
```
### Installation for developers
This installation downloads the source code, and the package loads directly from the source code for every import. Therefore, any changes to the code will have direct effect after an import.

Go to the directory of [this README you are reading](README.md) is placed (basically, to the directory of the [pyproject.toml](pyproject.toml) file, but this should be the same). Depending on your Python installation adopt python3/pip3 to python/pip, however python3 is required. And run:
```bash
cd /path/to/repro
python3 -m build  # This will create the files located in the folder `.egg-info`
pip3 install -r requirements.txt  # install the required python packages
pip3 install -U --user -e .  # install the package in developer mode.
```
#### Known issued at installation
- **Anaconda installation**

If you use a Python-Anaconda installation, you have to install `opencv-python` manually as Anaconda hasn't listed `opencv-python` and therefore can install it.
Activate your environment in a terminal (`conda activate`) and run (or with `sudo` if this doesn't work):
```bash
pip install opencv-python
```

- **AssertionError: Egg-link**

In case you see an `AssertionError: Egg-link`, run:
```bash
rm ~/.local/lib/pythonX.X/site-packages/H5DAQ.egg-link
```
where X.X is your python version, e.g., 3.7 and run the command
```bash
pip3 install -U --user -e .
```
again.
This problem happens if you move the source code directory after you created the egg-link file.

## TODO List:
* [ ] add readme for every sensor typ
* [ ] add examples
* [ ] add all sensor types
