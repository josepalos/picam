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
    def __init__(self):
        self._camera = PiCamera()
        self._camera.resolution = (480, 320)
        self._camera.framerate = 15
        self._raw_capture = PiRGBArray(self._camera, size=self._camera.resolution)
        self._delay = 0

    def get_image(self) -> Image:
        logging.getLogger(__name__).debug("Get the image potato.jpg")
        return Image("potato.jpg")

    def set_iso(self, value: int):
        logging.getLogger(__name__).debug("Set iso value to %d", value)
        self._camera.iso = value
    
    def set_brightness(self, value: int):
        logging.getLogger(__name__).debug("Set brightness value to %d", value)
        self._camera.brightness = value

    def set_contrast(self, value: int):
        logging.getLogger(__name__).debug("Set contrast value to %d", value)
        self._camera.contrast = value

    def set_shutter_speed(self, value: int):
        logging.getLogger(__name__).debug("Set shutter speed value to %d", value)
        self._camera.shutter_speed = value

    def set_delay(self, value: int):
        logging.getLogger(__name__).debug("Set delay value to %d", value)
        self._delay = value

    def set_led(self, value: bool):
        logging.getLogger(__name__).debug("Set led value to %d", value)
        self._camera.led = value

    def take_picture(self) -> Image:
        logging.getLogger(__name__).debug("Take new picture")

        time.sleep(self._delay)
        self._camera.capture(self._raw_capture, format="bgr")
        image = self._raw_capture.array

        return Image(image)
    
    def preview(self):
        for frame in self._camera.capture_continuous(self._raw_capture,
                                                     format="bgr",
                                                     use_video_port=True):
            image = Image(frame.array)
            # clear the stream for the next frame
            self._raw_capture.truncate(0)
            yield image
            
    def close(self):
        self._camera.close()


if __name__ == "__main__":
    cam = Camera()

    time.sleep(0.1)

    for i, image in enumerate(cam.preview()):
        print("New frame %d" % i)
        cv2.imshow("Frame", image._image)
        cv2.waitKey(1)
    cam.close()

