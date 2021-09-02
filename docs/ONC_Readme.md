# ONC Submodule

ONC downloads the data from the modules to their database (DB). There are two (maybe more) main technics to access the data:
1. One way to access this data is the [Oceans 2.0 webpage](https://data.oceannetworks.ca/home).
2. The ONC python package ([original repository](https://github.com/OceanNetworksCanada/api-python-client) and [forked with extended capabilities](https://github.com/FlyingAndrew/api-python-client))

Obviously but worth to mention, this repository makes use of the [forked ONC python package](https://github.com/FlyingAndrew/api-python-client).
However, the [Oceans 2.0 webpage](https://data.oceannetworks.ca/home) is listed here for the sake of completeness at the end.

## How to access the data within python
The download of files from the ONC DB there are basically two, and a half steps:
- The half is, that you need a valid token for any request to the ONC DB. This package comes with a token in the [default config file](../config), but it may not be valid anymore. Therefore, you [generate your personal token](#Where can I find my token?) and set the token in the config file (the one in your home directory), [here is how you do this](Config_File.md). Usually it has to be generated only once, unless you don't generate a new token, which makes the previous token invalid.

For the rest it is:
1. you ask the ONC DB with a filter for available files.
2. you download the files of interest.

Check out the examples.

### Where can I find my token?
On any of the [Oceans 2.0 pages](https://data.oceannetworks.ca), once you are logged in,
1. on the top right click on the Profile link
2. on the Web Services API tab
3. that will take you to your token.

### Examples
For examples check out the [examples' folder](../examples) which includes notebooks and scripts. For the ONC submodule this are:
- [(Script) ONC download](../examples/basic_onc_download.py)
- [(Notebook) ONC download and filter](../examples/ONC_Downloader_Example.ipynb)
- [(Notebook) Explore pandas_file_sync_db](../examples/explore_pandas_file_sync_db.ipynb)

### Filters
The package use filters to specify the search on the ONC DB. Functions take the filters as a python dict with specific keys. [This link](https://wiki.oceannetworks.ca/display/O2A/archivefiles) to the official ONC docs summarise the general usage. The following example and table summarise the usage and special keys for STRAWb.
``` python
import os
onc_downloader = strawb.ONCDownloader(showInfo=False)

# print posible dataProductCodes and dataProductName for the device
print(onc_downloader.getDataProducts({'deviceCode':'TUMPMTSPECTROMETER002'}))

# print posible dataProductCodes and dataProductName for the device only for hdf5-files
print(onc_downloader.getDataProducts({'deviceCode':'TUMPMTSPECTROMETER002', 'extension': 'hdf5'}))

# show posible dataProducts for deviceCategory
print(onc_downloader.getDataProducts({'deviceCategoryCode':'LIDAR', 'extension': 'hdf5'}))

# the following 2 lines are the same
print(onc_downloader.getDataProducts({'dataProductCode': 'LIDARSD'})
print(onc_downloader.getDataProducts({'dataProductName': 'LiDAR Sensor Data'})
```

A list of possible filter tags regarding STRAWb (created by Jeannette Bedard from ONC). In the following table `locationCode`, `deviceCategoryCode`, and `deviceCode` are keys whereas `Instrument` is not a key for a filter.

Instrument | locationCode | deviceCategoryCode | deviceCode 
---------- | ------------ | ------------------ |------------- 
LIDAR SN001             | STR3 | LIDAR           | TUMLIDAR001
LIDAR SN002             | STR10| LIDAR           | TUMLIDAR002
Mini Spectrometer SN001 | STR5 | BIOSPECTROMETER | TUMMINISPECTROMETER001
Muon Tracker            | STR6 | MUONTRACKER     | TUMMUONTRACKER001
PMT SN001               | STR2 | BIOSPECTROMETER | TUMPMTSPECTROMETER001 |
PMT SN002               | STR9 | BIOSPECTROMETER | TUMPMTSPECTROMETER002 |
Standard Module SN001   | STR4 | STANDARDMODULE  | TUMSTANDARDMODULE001
Standard Module SN004   | STR7 | STANDARDMODULE  | TUMSTANDARDMODULE004
Standard Module SN003   | STR8 | STANDARDMODULE  | TUMSTANDARDMODULE003
Wavelength Shifting Optical Module SN001 | STR1 | WAVELENGTHOPTICALMODULE | UMAINZWOM001


## Something went wrong? (Collect Errors)
### Connection timeout:
`
requests.exceptions.ConnectTimeout: HTTPSConnectionPool(host='data.oceannetworks.ca', port=443): Max retries exceeded with url: /api/archivefiles?token=0db751f8-9430-47af-bc11-ed6691b38e22&method=getFile&filename=TUMPMTSPECTROMETER002_20210627T110000.000Z-SDAQ-CAMERA.hdf5 (Caused by ConnectTimeoutError(<urllib3.connection.HTTPSConnection object at 0x1054de7c0>, 'Connection to data.oceannetworks.ca timed out. (connect timeout=60)'))
`

## How to access the data via the [Oceans 2.0 webpage](https://data.oceannetworks.ca/home)
Open the [Data Search tab on the Oceans 2.0 webpage](https://data.oceannetworks.ca/DataSearch), wait that the content loads completely and on the left navigate (by clicking on the icon left of the specific item)
`Ocean Networks Canada -> Pacific -> Northeast Pacific Ocean -> Cascadia Basin -> ODP 1027C` and select a module from one of the lines.
- STRAW - `Neutrino Project Mooring 01 (Yellow)`
- STRAW - `Neutrino Project Mooring 02 (Blue)`
- STRAWb - `Neutrino Project Mooring 03`

After you clicked on a module, click on `Select this data source` (window on the map), and finally a list with data-products appears. For more information on how to progress, check out the [Oceans 2.0 wiki](https://wiki.oceannetworks.ca/display/O2KB).
