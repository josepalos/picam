from fractions import Fraction
import logging
import time

import cv2
from picamera import PiCamera
from picamera.array import PiRGBArray
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


class Camera:
    def __init__(self, resolution=None, framerate=None):
        self._camera = None
        self._raw_capture = None
        self._resolution = resolution
        self._framerate = framerate
        self._delay = 0

    def open(self):
        framerate = self._framerate
        if not framerate:
            framerate = 30
        self._camera = PiCamera(resolution=self._resolution,
                                framerate=framerate,
                                sensor_mode=0)
        self._raw_capture = PiRGBArray(self._camera)
        self.unfix_automatic_settings()
        self.shutter_speed = 0  # auto

        time.sleep(0.1)  # warm up

    def close(self):
        self._camera.close()
        self._camera = None
        self._raw_capture = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

    def fix_automatic_settings(self):
        self._camera.exposure_mode = "off"

    def unfix_automatic_settings(self):
        self._camera.exposure_mode = "auto"


    def set_iso(self, value: int):
        logging.getLogger(__name__).debug("Set iso value to %d", value)
        self._camera.iso = value
    
    def set_brightness(self, value: int):
        logging.getLogger(__name__).debug("Set brightness value to %d", value)
        self._camera.brightness = value

    def set_contrast(self, value: int):
        logging.getLogger(__name__).debug("Set contrast value to %d", value)
        self._camera.contrast = value

    def set_shutter_speed(self, value: str):
        if "/" in value:
            denom = int(value.split("/")[1])
            microseconds = int(1000000 / denom)
        else:
            seconds = float(value)
            microseconds = int(seconds * 1000000)

        if 1000000 / self._camera.framerate < microseconds:
            logging.getLogger(__name__).warning("Framerate is too fast for this shutter speed")
            if self._framerate is None:
                new_framerate = Fraction(1000000/microseconds)
                logging.getLogger(__name__).info("Changing the framerate to be %s", new_framerate)
                self._camera.framerate = new_framerate

        logging.getLogger(__name__).debug("Set shutter speed value to %s (%d)",
                                          value, microseconds)
        self._camera.shutter_speed = microseconds

    def set_delay(self, value: int):
        logging.getLogger(__name__).debug("Set delay value to %d", value)
        self._delay = value

    def set_led(self, value: bool):
        logging.getLogger(__name__).debug("Set led value to %d", value)
        self._camera.led = value

    def take_picture(self, filename: str):
        logging.getLogger(__name__).debug("Take new picture")
        time.sleep(self._delay)
        start = time.time()
        self._camera.capture(filename)
        end = time.time()
        logging.getLogger(__name__).info("Image saved at %s", filename)
        logging.getLogger(__name__).debug("Image took %d seconds", end - start)
    
    def preview(self):
        for frame in self._camera.capture_continuous(self._raw_capture,
                                                     format="bgr",
                                                     use_video_port=True):
            image = Image(frame.array)
            # clear the stream for the next frame
            self._raw_capture.truncate(0)
            yield image
            
