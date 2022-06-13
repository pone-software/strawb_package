#!/usr/bin/python3
# coding: utf-8

import os
import numpy as np
from glob import glob
from os.path import join
import cv2

from tqdm import tqdm
import pickle
from welford import Welford
import pandas as pd

import strawb.sensors.camera as camera
from strawb.config_parser import Config


## this function is also in camera.Images, but I adapted it a bit for this analysis
def rgb_standalone(cam_run, picture_handler, bit=8, look_at=None, **kwargs):
    if look_at is None:
        look_at = np.arange(cam_run.exposure_time.shape[0])
        print(look_at)
    rgb = picture_handler.load_rgb(index=np.atleast_1d(look_at), **kwargs)
    if rgb is None:
        return None
    # get bit's right, default is 16bit
    bit_dict = {8: np.uint8, 16: np.uint16}
    if bit == 8:
        rgb = rgb / 2 ** 16 * 2 ** 8  # - 1

    rgb[rgb == 2 ** bit] = rgb[rgb == 2 ** bit] - 1
    return rgb.astype(bit_dict[bit])

### find all files and dates
ff = sorted(
    glob(
        f'{Config.raw_data_dir}/tumpmtspectrometer001/????_??/TUMPMTSPECTROMETER001_*Z-SDAQ-CAMERA.hdf5'
    )
)
dates = []
for f in ff:
    dates.append(f.split("/")[5])
dates = np.unique(np.array(dates))
print(dates)


## loop over all dates (ie. each month)
## and analyze the camera data
for ident in dates:
    print("analyzing", ident)
    key = f"TUMPMTSPECTROMETER001_{ident.replace('_', '')}??T"
    savepath = f"{Config.proc_data_dir}/pmtspectrometer001/dark_{ident}/"
    if os.path.isfile(join(savepath, f"{key}_biolumi_activity_info.pckl").replace("?", "x")):
        print("biolumi file already exists. continue...")
        continue
    pic_path = join(savepath, "pictures")
    if os.path.isdir(savepath):
        print("Savepath exists! cool:")
        print(savepath)
    else:
        os.mkdir(savepath)
        print("Made this path:")
        print(savepath)
    if os.path.isdir(pic_path):
        print("picpath exists! cool:")
        print(pic_path)
    else:
        os.mkdir(pic_path)
        print("Made this path:")
        print(pic_path)
    all_files = sorted(
        glob(
            f'/dss/strawb/raw_module_data/tumpmtspectrometer001/{ident}/{key}??????.???Z-SDAQ-CAMERA.hdf5'
        )
    )
    print("number of files:", len(all_files))



    ## read the data, convert to RGB and built a welford object 
    # this welford thingy is used to calculate mean and standard deviation iteratively so that not all data needs to be read at once
    # see https://pypi.org/project/welford/ and wiki links therein
    # mean and std per pixel are later used to identify outliers in the pictures
    ### alternatively: load the pre-processed file
    welford_filename = join(savepath, f"welford_{key}.pckl".replace("?", "x"))
    if os.path.exists(welford_filename):
        print("reading welford data")
        with open(welford_filename, "rb") as f:
            w = pickle.load(f)
    else:
        print("calculating welford data")
        w = Welford()
        broken_files = []
        ok_files = []
        for f in tqdm(all_files):
            try:
                cam_run = camera.FileHandler(f)
                ident = f.split("/")[-1].split(".")[0]
                filename = join(savepath, f"{ident}_rgb.pckl")
                ok_files.append({"fname": f, "n_frames_tot": len(cam_run.time)})
            except Exception as e:
                print("Could not load file:", f)
                raise e
                broken_files.append(f)
                continue
            # check if the RGB file already exists, and add it to the welford object
            if os.path.isfile(filename):
                with open(filename, "rb") as openf:
                    tmp, _ = pickle.load(openf)
                w.add_all(tmp)
                continue
            # if not, load the raw pictures and convert them to RGB
            picture_handler = camera.Images(cam_run)
            try:
                this = np.where(cam_run.lucifer_options[:,0] == -125)[0]
                ok_files[-1]["n_frames_selected"] = len(cam_run.time[this])
            except Exception as e:
                print(cam_run.lucifer_options)
                raise e
                continue
            if this.size==0:
                print("No good pictures found.")
                continue
            try:
                tmp = rgb_standalone(cam_run, picture_handler, look_at=this, subtract_dark=False)        
                ok_files[-1]["n_frames_rgb"] = len(tmp)
            except IndexError as e:
                print(this)
                print("Could not compute RGB")
                raise e
                continue
            # write the RBG data + timestamp to disc, so that it can be easier analyzed later on
            if tmp is not None:
                with open(filename, "wb") as openf:
                    pickle.dump([tmp, cam_run.time[this].astype('datetime64[s]')], openf)
                w.add_all(tmp)
            
            # free up some space
            del cam_run
            del picture_handler
            del tmp

        ### save the welford object, so that data needs to be read only once
        with open(welford_filename, "wb") as f:
            pickle.dump(w, f)

    ### get all rgb files
    # get the filenames of all previously processed and saved RGB picture files
    all_rgb_files = sorted(glob(join(savepath, f"{key}??????_rgb.pckl")))

    print("Starting the cluster search...")
    # Manhattan distance 
    # defined as $D_M = |\Delta x| + |\Delta y|$, i.e. a rectangular distance from eg. one pixel to another one
    # used to calculate distances of pixels that have a large bright std from the (dark) expectation
    std = np.sqrt(w.var_p)
    # settings for the cluster algorithm
    # these are somewhat guessed and adapted, but not fully optimized
    sigma_level = 5 # low threshold: 4; high threshold: 5
    max_dist = 5
    alt_max_dist = 4
    cl_pix = 25 # max pixel = 60
    alt_cl_pix = 15 # max pixel = 40

    ### CURRENTLY THE ALGORITHM IS ONLY BASED ON BLUE! 
    # (it is enough in most cases anyway)
    color = 2 # r: 0, g: 1, b: 2

    list_of_timestamps = []
    total_number_of_pictures = 0

    # loop over all RGB pictures and identify outliers based on parameters above
    for ff, f in tqdm(enumerate(all_rgb_files)):
        with open(f, "rb") as filo:
            tmp, times = pickle.load(filo)
            total_number_of_pictures += len(times)

        # select pixels where the brightness exceeds the mean by several std
        mask = tmp - w.mean > sigma_level * std
        # .. and prepare to count them
        mask = np.logical_and(mask, std > 0).astype(int)

        # mask contains all RGB files per camera file, loop over all pictures
        for im, m in enumerate(mask):
            fname_id = str(times[im]).replace(":", "-").replace("T", "_")
            filename = join(pic_path, f"{fname_id}.png")

            # if the picture is already analyzed and saved to disc, skip!
            # this needs to be removed when eg. changing the algorithm
            # such that it's re-analyzed
            if os.path.isfile(filename):
                print("file already exists:", filename)
                continue
            # just selecting the blue channel for now
            # shape: n_pixel x 2 (x and y coordinates of the picture)
            # get the x and y coordinates (=indices) from the mask
            indices = np.array(np.where(m[:, :, color])).T
            # catch pictures that are super bright, however that happened..??
            if indices.shape[0] > 1e4:
                print("Super bright picture:", fname_id)
                continue
            # calculate manhattan distance of bright selected pixels to each other
            # n_pixel x n_pixel
            manhattan_distance = np.abs(indices[:, :, np.newaxis] - indices.T).sum(axis=1)

            # select neighboring pixels within a max distances, per pixel
            cluster_sum_mask = np.logical_and(
                manhattan_distance <= max_dist,
                manhattan_distance > 0,  # ensure that the pixel itself is not counted
            )

            # count the neighboring pixels, per pixel
            cluster_sum = cluster_sum_mask.sum(axis=0)
            # define a cluster with cl_pix neighboring pixels or more
            number_of_clusters = np.count_nonzero(cluster_sum >= cl_pix)

            # if there are no clusters found, try some slightly different settings for the algorithm
            if number_of_clusters <= 1:
                # alternative criterion: smaller cluster, but 2 or more of them
                cluster_sum_mask = np.logical_and(
                    manhattan_distance <= alt_cl_pix, manhattan_distance > 0
                )
                cluster_sum = cluster_sum_mask.sum(axis=0)
                alt_number_of_clusters = np.count_nonzero(cluster_sum >= alt_cl_pix)

            if number_of_clusters >= 1 or alt_number_of_clusters >= 2:
                # count the number of clusters
                unq, ct = np.unique(cluster_sum, return_counts=True)

                # save all info
                list_of_timestamps.append(
                    {
                        "timestamp": times[im],
                        "cluster_type": "normal" if number_of_clusters >= 1 else "alt",
                        "n_bright_pix": indices.shape[0],
                        "largest_cluster": unq[-1],
                        "number_of_clusters": number_of_clusters if number_of_clusters >= 1 else alt_number_of_clusters,
                        "bright_pix_positions_x": indices[:,0],
                        "bright_pix_positions_y": indices[:,1],
                    }
                )
                # outreach material :)
                if unq[-1] > 57:
                    print("outreach material :)")
                    cv2.imwrite(filename, tmp[im,:,:,::-1])
    print("Done")
    pd_info = pd.DataFrame(list_of_timestamps)

    del indices
    del mask
    del tmp
    pd_info.to_pickle(join(savepath, f"{key}_biolumi_activity_info.pckl").replace("?", "x"))
