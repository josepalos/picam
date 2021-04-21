import logging
import os
import os.path
import re


IMAGES_DIRECTORY = "./images"
VALID_FILE_EXTENSIONS = ["jpeg", "png", "gif", "bmp", "yuv", "rgb", "rgba"]


class Storage:
    def __init__(self, path, num_digits: int = 4):
        self.path = path
        self._next_id = None
        self._num_digits = num_digits

    def start(self):
        os.makedirs(self.path, exist_ok=True)
        self._set_next_img_id()

    def _set_next_img_id(self):
        logger = logging.getLogger(__name__)
        self._next_id = 0
        files = [f for f in os.listdir(self.path)
                 if os.path.isfile(os.path.join(self.path, f))]
        extensions_match = "(" + "|".join(VALID_FILE_EXTENSIONS) + ")"
        img_regex = re.compile(r"IMG(\d+)\." + extensions_match)
        for f in files:
            if img_regex.match(f):
                img_id = int(img_regex.match(f).group(1))
                self._next_id = max(self._next_id, img_id + 1)

        if self._next_id != 0:
            logger.info("Storage has found existing images, starting at id"
                        " %d", self._next_id)
        else:
            logger.info("Storage has not found any image. Starting at id 0")

    def get_new_name(self, extension):
        if extension not in VALID_FILE_EXTENSIONS:
            raise Exception(f"Invalid extension {extension}")
        img_name = f"IMG{self._next_id:0{self._num_digits}}.{extension}"
        self._next_id += 1
        return os.path.join(self.path, img_name)


