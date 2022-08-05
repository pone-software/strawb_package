# Image Cluster Search

The workflow of to detect the Cluster in the Images is as follows.
The root directory of all generated files is located at: `<strawb.Config.proc_data_dir>/image_cluster_search/`
1. Download the files with the `strawb.SyncDBHandler`. The following functions will use all synchronised camera files.
2. Run [cluster_scan_all.ipynb](cluster_scan_all.ipynb) to generate the monthly DB for all devices and monthly where files are available.
   This notebook supports multiprocessing but still it can take ~2 days to finish when all files are processed.
    Files are named: `{dev_code}_{t_start}_{t_end}_image_cluster.gz`
3. The monthly files are ~50 MB in size. To reduce the size and generate one DB file for each module, run [cluster_db_compress.ipynb](cluster_db_compress.ipynb).
   Files are named: `{dev_code}_{t_start}_{t_end}_image_cluster_merge_npixel{min_n_pixel}.gz`
   where `min_n_pixel` is mininimum cluster size to keep. All smaller clusters are removed in the resulting file.


# Mask for the camera mounting

To get the coordinates of the camera mounting or a mask for an image where only the pixels that belong to the mounting are valid, run [mounting_coordinates.ipynb](mounting_coordinates.ipynb).
