#!/usr/bin/python3
# coding: utf-8

import random

import strawb
from strawb.tools import ShareJobThreads


def main(n_files=3, pattern: str = '*-SDAQ-CAMERA.hdf5'):
    """ Search for files defined by the pattern and select n_files from those files.
    It pars each file to the function `parse_one_file` paralysed with ShareJobThreads.
    PARAMETER
    ---------
    pattern: str, optional
        The search pattern for glob, like in bash
    n_files: None, or int.
        The number of files which are processed. None, means all files found.
    """

    # get all files which match the pattern
    file_list = strawb.sensors.Camera.FileHandler.find_files_glob(file_pattern=pattern,
                                                                  directory=strawb.Config.raw_data_dir,
                                                                  recursive=True,
                                                                  raise_nothing_found=False)

    if file_list is []:
        print(f'No file found for the pattern: {pattern}')
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
    # initialise the FileHandler and PictureHandler
    cam_run = strawb.sensors.Camera.FileHandler(full_path)
    picture_handler = strawb.sensors.Camera.PictureHandler(cam_run)

    return picture_handler.image2png(exclude_invalid=False)


# execute only if run as a script
if __name__ == "__main__":
    main()
