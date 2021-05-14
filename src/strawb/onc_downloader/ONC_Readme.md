# ONC Package

### Where can I find my token?
On any of our Oceans 2.0 pages, once you are logged in,
1. on the top right click on the Profile link
2. on the Web Services API tab
3. that will take you to your token.

https://data.oceannetworks.ca/home?TREETYPE=1&LOCATION=11&TIMECONFIG=0

### Example

```python
import strawb
import os

onc_downloader = strawb.ONCDownloader('0db751f8-9430-47af-bc11-ed6691b38e22', showInfo=False)

filters = {'deviceCode': 'TUMPMTSPECTROMETER002',
           'dateFrom': '2021-05-10T19:00:00.000Z',
           'dateTo': '2021-05-10T21:59:59.000Z',
           'extension': 'hdf5'}

# in background
# onc_downloader.start(filters=filters, allPages=True)

# in foreground
onc_downloader.download_file(filters=filters, allPages=True)

# and print all downloaded files
for i in onc_downloader.result['downloadResults']:
    full_path = os.path.join(onc_downloader.outPath, i['file'])
    print(os.path.exists(full_path))
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
