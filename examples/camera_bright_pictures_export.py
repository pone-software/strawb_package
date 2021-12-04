#!/usr/bin/python3
# coding: utf-8

import random

import numpy as np

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
    # in case execute db.load_onc_db_entirely() to load the entire db
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


def parse_one_file(full_path, threshold=5e3):
    # initialise the FileHandler and Images
    camera = strawb.sensors.Camera(full_path)

    mode_list, mask_list = camera.images.get_lucifer_mask()
    mask_lucifer = np.any(mask_list, axis=0)

    mask = (camera.images.integrated_minus_dark > threshold) & camera.images.invalid_mask & ~mask_lucifer
    index = np.argsort(camera.images.integrated_minus_dark)
    index = index[mask[index]]  # remove invalid items  & cam_module.invalid_mask
    index = index[::-1]  # revers the order

    return camera.images.image2png(index=index, f_name_formatter='{i}_{datetime}.png')


# execute only if run as a script
if __name__ == "__main__":
    main()
