import logging

from PyQt5 import QtGui


class Image:
    def __init__(self, path):
        self.path = path

    def as_qtimage(self) -> QtGui.QImage:
        return QtGui.QImage(self.path)

class Camera:
    def get_image(self) -> Image:
        logging.getLogger(__name__).debug("Get the image potato.jpg")
        return Image("potato.jpg")

    def set_iso(self, value: int):
        logging.getLogger(__name__).debug("Set iso value to %d", value)
    
    def set_brightness(self, value: int):
        logging.getLogger(__name__).debug("Set brightness value to %d", value)

    def set_contrast(self, value: int):
        logging.getLogger(__name__).debug("Set contrast value to %d", value)

    def set_shutter_speed(self, value: int):
        logging.getLogger(__name__).debug("Set shutter speed value to %d", value)

    def set_delay(self, value: int):
        logging.getLogger(__name__).debug("Set delay value to %d", value)

    def set_led(self, value: bool):
        logging.getLogger(__name__).debug("Set led value to %d", value)

    def take_picture(self):
        logging.getLogger(__name__).debug("Take new picture")
