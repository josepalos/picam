import logging
import time

import cv2
from PyQt5 import QtGui


class Image:
    def __init__(self, cv2_img):
        self._image = cv2_img

    def as_qtimage(self) -> QtGui.QImage:
        rgb_image = cv2.cvtColor(self._image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape

        bytes_per_line = ch * w
        return QtGui.QImage(rgb_image.data, w, h, bytes_per_line,
                            QtGui.QImage.Format_RGB888)

    @staticmethod
    def from_file(filename):
        cv2_img = cv2.imread("potato.jpg")

        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(cv2_img, f"{time.time()}", (100, 100), font, 3, (0, 255, 0), 2, cv2.LINE_AA)

        return Image(cv2_img)


class Camera:
    def __init__(self, resolution=None, framerate=None):
        self._delay = 0

    def open(self):
        pass

    def close(self):
        logging.getLogger(__name__).debug("Close camera")
        pass

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()
    
    def set_awb_gain(self, gain: float):
        logging.getLogger(__name__).debug("Setting AWB gain to: %f", gain)

    def set_awb_mode(self, mode: str):
        logging.getLogger(__name__).debug("Setting AWB mode to: %s", mode)

    def set_iso(self, value: int):
        logging.getLogger(__name__).debug("Set iso value to %d", value)
    
    def set_brightness(self, value: int):
        logging.getLogger(__name__).debug("Set brightness value to %d", value)

    def set_contrast(self, value: int):
        logging.getLogger(__name__).debug("Set contrast value to %d", value)
    
    def set_exposure(self, value):
        logging.getLogger(__name__).debug("Set exposure to %s", value)

    def maximize_fps(self):
        logging.getLogger(__name__).debug("Maximizing FPS")

    def set_shutter_speed(self, value: str):
        if "/" in value:
            denom = int(value.split("/")[1])
            microseconds = int(1000000 / denom)
        else:
            seconds = float(value)
            microseconds = int(seconds * 1000000)

        logging.getLogger(__name__).debug("Set shutter speed value to %s (%d)",
                                          value, microseconds)

    def set_delay(self, value: int):
        logging.getLogger(__name__).debug("Set delay value to %d", value)

    def set_led(self, value: bool):
        logging.getLogger(__name__).debug("Set led value to %s", value)

    def get_exposure_speed(self):
        return 10000

    def take_picture(self, filename: str):
        logging.getLogger(__name__).debug("Take new picture")
        time.sleep(self._delay)
        logging.getLogger(__name__).info("Image saved at %s", filename)
    
    def preview(self):
        while True:
            yield Image.from_file("potato.jpg")
