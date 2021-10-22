#!/usr/bin/python3
# coding: utf-8

import random

import strawb
from strawb.tools import ShareJobThreads


def main(n_files=3):
    """ Search for files defined by the pattern and select n_files from those files.
    It pars each file to the function `parse_one_file` paralysed with ShareJobThreads.
    PARAMETER
    ---------
    pattern: str, optional
        The search pattern for glob, like in bash
    n_files: None, or int.
        The number of files which are processed. None, means all files found.
    """
    # in case execute db.load_entire_db_from_ONC() to load the entire db
    db = strawb.SyncDBHandler(file_name='Default')  # loads the db

    ending = 'CAMERA.hdf5'
    # mask by device
    mask = db.dataframe.fullPath.str.endswith(ending)  # filter by filename
    mask &= db.dataframe.synced  # mask un-synced hdf5 files
    mask &= db.dataframe.fileSize > 11000  # mask empty hdf5 files

    # get all files which match the pattern
    file_list = list(db.dataframe.fullPath[mask])

    if file_list is []:
        print(f'No file found which ends with: {ending}')
        return
    elif n_files is None or len(file_list) <= n_files:
        print(f'Process all {len(file_list)} files.')
        file_list_select = file_list
    else:
        file_list_select = random.sample(file_list, n_files)
        print(f'Out of {len(file_list)} files select {n_files} randomly')

    sjt = ShareJobThreads()
    sjt.do(parse_one_file, file_list_select)


def parse_one_file(full_path):
    # initialise the FileHandler and Images
    camera = strawb.sensors.Camera(full_path)

    return camera.images.image2png(exclude_invalid=False)


# execute only if run as a script
if __name__ == "__main__":
    main()
