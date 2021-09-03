# STRAWb

STRAWb is a python module which simplifies and streamlines the work with the STRAWb data. Beside this Readme, there is more documentation in the [docs directory](docs).

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
where X.X is your python version, e.g., 3.7 and run the following command again.
```bash
pip3 install -U --user -e .
```
This problem happens if you move the source code directory after you created the egg-link file.

## TODO List:
* [ ] add readme for every sensor typ
* [ ] add examples
* [ ] add all sensor types
