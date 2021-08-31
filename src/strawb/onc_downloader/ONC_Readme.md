# ONC Package

### Where can I find my token?
On any of our Oceans 2.0 pages, once you are logged in,
1. on the top right click on the Profile link
2. on the Web Services API tab
3. that will take you to your token.

https://data.oceannetworks.ca/home?TREETYPE=1&LOCATION=11&TIMECONFIG=0

### Example

```python
from src.strawb.onc_downloader import ONCDownloader
from strawb import dev_codes_deployed

onc_downloader = ONCDownloader(showInfo=False)

# select dev_codes
dev_codes = list(dev_codes_deployed)
dev_codes.sort()

# get available from ONC server, `download=False` as we want to filter some files
pd_result = onc_downloader.download_structured(dev_codes=dev_codes[:2],
                                               extensions=None,
                                               date_from='2021-08-30T00:00:00.000',
                                               date_to='2021-08-30T01:00:00.000',
                                               download=False,
                                               )
# select only 5 files
pd_result_masked = pd_result[['filename', 'outPath']]
# prepare download
filters_or_result = dict(files=pd_result_masked.to_dict(orient='records'))
# download the files
onc_downloader.getDirectFiles(filters_or_result=filters_or_result)
```

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