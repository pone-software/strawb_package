# ONC Submodule

### Where can I find my token?
On any of the [Oceans 2.0 pages](https://data.oceannetworks.ca/home), once you are logged in,
1. on the top right click on the Profile link
2. on the Web Services API tab
3. that will take you to your token.

### Examples
For examples check out the [examples' folder](../examples) which includes notebooks and scripts.
- [(Script) ONC download](../examples/basic_onc_download.py)
- [(Notebook) ONC download and filter](../examples/ONC_Downloader_Example.ipynb)
- [(Notebook) Explore pandas_file_sync_db](../examples/explore_pandas_file_sync_db.ipynb)

### Filter tags
The list of possible filter tags by Jeannette Bedard from ONC.

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

The filer can also include a `dataProductCode` or `dataProductName`, i.e. `'dataProductCode': 'SMRD'` or `'dataProductName': 'Standard Module Raw Data'` for the `...-SDAQ-MODULE.hdf5` file.
To see the possible option for a device:
``` python
import os
onc_downloader = strawb.ONCDownloader(showInfo=False)

# print posible dataProductCodes and dataProductName for the device
print(onc_downloader.getDataProducts({'deviceCode':'TUMPMTSPECTROMETER002'}))
# print posible dataProductCodes and dataProductName for the device only for hdf5-files
print(onc_downloader.getDataProducts({'deviceCode':'TUMPMTSPECTROMETER002', 'extension': 'hdf5'}))
```


## When something went wrong
### Connection timeout:
`
requests.exceptions.ConnectTimeout: HTTPSConnectionPool(host='data.oceannetworks.ca', port=443): Max retries exceeded with url: /api/archivefiles?token=0db751f8-9430-47af-bc11-ed6691b38e22&method=getFile&filename=TUMPMTSPECTROMETER002_20210627T110000.000Z-SDAQ-CAMERA.hdf5 (Caused by ConnectTimeoutError(<urllib3.connection.HTTPSConnection object at 0x1054de7c0>, 'Connection to data.oceannetworks.ca timed out. (connect timeout=60)'))
`