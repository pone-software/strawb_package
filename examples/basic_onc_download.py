# This examples shows who to download files from the ONC server
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
