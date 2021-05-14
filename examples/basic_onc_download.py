# This examples shows who to download files from the ONC server
import strawb

onc_downloader = strawb.ONCDownloader(showInfo=False)

filters = {'deviceCode': 'TUMPMTSPECTROMETER002',
           'dateFrom': '2021-05-01T19:00:00.000Z',
           'dateTo': '2021-05-01T21:59:59.000Z',
           'extension': 'hdf5'}

# download in foreground
onc_downloader.download_file(filters=filters, allPages=True)

# download in background, same as above but the download happens in a thread -> cmd is non blocking
# onc_downloader.start(filters=filters, allPages=True)


