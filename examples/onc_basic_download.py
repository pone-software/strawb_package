# This examples shows who to download files from the ONC server
import strawb

onc_downloader = strawb.ONCDownloader(showInfo=False)

# get available from ONC server, `download=False` as we want to filter some files
# download_structured does:
#  1. download_structured checks for available files,
#  2. sets the directory for each file ('outPath'),
#  (3. if download=True, downloads the files)
#  4. returns the result as a pandas.DataFrame
pd_result = onc_downloader.download_structured(dev_codes=strawb.dev_codes_deployed[:2],
                                               # only 2 dev's for less data
                                               extensions=None,
                                               date_from='2021-08-30T00:00:00.000',
                                               date_to='2021-08-30T01:00:00.000',
                                               download=False,
                                               )
# select only 5 files
pd_result_masked = pd_result[:5]  # select only 5 files for less data
# download the files
onc_downloader.getDirectFiles(filters_or_result=pd_result_masked)
