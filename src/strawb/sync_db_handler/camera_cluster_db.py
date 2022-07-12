from strawb import Config
from strawb.sync_db_handler.base_db_handler import BaseDBHandler


class ImageClusterDB(BaseDBHandler):
    # set defaults
    _default_raw_data_dir_ = Config.raw_data_dir
    _default_file_name_ = Config.image_cluster_db
