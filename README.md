# STRAWb

STRAWb is a python module which simplifies and streamlines the work with the STRAWb data. Beside this Readme, there is more documentation at the [repository Wiki page](https://github.com/pone-software/strawb_package/wiki).

## Installation
For the installation you have two options.
### Installation directly from the repository
`Pip` can directly install the package from the repository. As `pip` only compares the version number and not the code, uninstall an existing installation before you install it from the repository. For updating the package just rerun the same commands. You can also specify the branch by changing `master` accordingly. The commands are:
```bash
pip3 uninstall -y strawb  # Uninstall an existing installation
pip3 install -U git+https://github.com/pone-software/strawb_package.git@master  # Install it from the repository
```

### Installation for developers
This installation downloads the source code, and the package loads directly from the source code for every import. Therefore, any changes to the code will have direct effect after an import.

Go to the directory of [this README you are reading](/README.md) is placed (basically, to the directory of the [pyproject.toml](/pyproject.toml) file, but this should be the same).
Depending on your Python installation adopt python3/pip3 to python/pip, however python3 is required. Run:
  ```bash
  mkdir /path/to/repros  # adopted the path, be aware that git clone creates a directory with the repository name
  cd /path/to/repros # enter the directory
  
  # clone/download the repository
  git clone https://github.com/pone-software/strawb_package.git  # downloads the repository
  cd strawb_package  # enter the repository directory
  
  # install the package
  python3 -m build  # This will create the files located in the folder `.egg-info`
  pip3 install -U -r requirements.txt  # install the required python packages
  pip3 install -U --user -e .  # install the package in developer mode.
  ```

#### Known issued at installation
- **Missing hdf5 installation**
If you see an error like
```text
...
  Loading library to get build settings and version: libhdf5.so
  error: Unable to load dependency HDF5, make sure HDF5 is installed properly
  error: libhdf5.so: cannot open shared object file: No such file or directory
  ----------------------------------------
  ERROR: Failed building wheel for h5py
 ...
```
hdf5 isn't installed. On Linux/Ubuntu, run
```commandline
sudo apt-get install libhdf5-dev
```


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
where X.X is your python version, e.g., 3.7 and run the following command again.
```bash
pip3 install -U -e .
```
This problem happens if you move the source code directory after you created the egg-link file.

## TODO List:
* [ ] add readme for every sensor typ
* [ ] add examples
* [ ] add all sensor types
