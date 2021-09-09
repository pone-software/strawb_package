# Author: Kilian Holzapfel <kilian.holzapfel@tum.de>

from .file_handler import FileHandler
from .picture_handler import PictureHandler


class Camera:
    FileHandler = FileHandler
    PictureHandler = PictureHandler
