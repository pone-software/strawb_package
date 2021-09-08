# Documentation
This is the documentation of the STRAWb-package but also the related infrastructure like ONC and LRZ.

**ONC** hosts a database (DB) with all data from the measurements of the deployed modules.

**LRZ** provides a storage system called DSS and a VM (virtual machine) hosting services (Compute Cloud). The DSS holds a daily synced copy of all files of the ONC DB related to STRAWb.

Please also have a look to the [repository's readme](/README.md) with information about installing the package and more.

## Table of Contents
1. [List of Files of the Documentation](#List-of-Files-of-the-Documentation)
1. [Code Structure](#Code-Structure)
1. [Example](#example)

## List of Files of the Documentation
1. **Code Structure**
   1. [Package Config File](/docs/Config_File.md)
    1. Sensor
        1. [Camera](Camera_Readme.md)
        1. (more to be added)
    1. [ONC - How to access the data](ONC_Readme.md)
1. [**SSH to Modules - How to access the modules**](/docs/ONC_ssh2modules.md)
1. [**LRZ - access the DSS and computational resources (VMs)**](LRZ_Readme.md)
    1. [How to mount the DSS container](LRZ_mount_DSS.md)
    
## Code Structure
The code consists of several submodules. The following summarise the single parts briefly, for more documentation also have a look to the [docs directory](/docs).

### Config Parser
Takes care of parsing configuration parameters for the package from a config file. The sample config file with all parameters is [here](/config). 
If there is a config-file present at `~/.strawb/config` it reads the parameters from there. If not, it takes the sample config-file.

### ONCDownloader
Takes care of downloading the files from the ONC server to a local directory. [Readme of the submodule](/docs/ONC_Readme.md).

### Sensors
STRAWb consists of several Modules with different configurations of sensors. The code of the DAQ and module controlling software (MCTL) is located in [this repository](https://gitlab.lrz.de/strawb/mctl) (TUM resource, but external users can be added. 
Contact someone of the TUM group for access). 

Most of the sensors use `hdf5` files to store the measurements. But some sensors use other file types like `txt`, `hld`, `raw` and `png`.

To keep this Readme short, each sensor has a separated readme in the [/docs](/docs).

## Example
For examples check out the [examples' folder](/examples) which includes notebooks and scripts.
- [(Script) ONC download](/examples/onc_basic_download.py)
- [(Notebook) ONC download and filter](/examples/onc_filter_download.ipynb)
- [(Notebook) Explore hdf5 file](/examples/explore_hdf5_file.ipynb)
- [(Notebook) Explore pandas_file_sync_db](/examples/pandas_file_sync_db_explorer.ipynb)