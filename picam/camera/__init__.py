from fractions import Fraction
import logging
import time

import cv2
from PyQt5 import QtGui

from .settings import CameraSetting, ShutterSpeed
from ..presets import Preset

try:
    from picamera import PiCamera
    from picamera.array import PiRGBArray

    REAL_CAMERA = True
except ModuleNotFoundError:
    from .virtualcamera import FakePicamera as PiCamera
    from .virtualcamera import FakePiRGBArray as PiRGBArray

    REAL_CAMERA = False


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
        cv2_img = cv2.imread(filename)
        return Image(cv2_img)


class Camera:
    def __init__(self, resolution=None, framerate=None):
        self._camera = None
        self._raw_capture = None

        # settings
        self._settings = {
            CameraSetting.RESOLUTION: resolution,
            CameraSetting.FRAMERATE: framerate
        }
        print(self._settings)

    def set_setting(self, setting: CameraSetting, value):
        setattr(self._camera, setting.value.camera_setter_name, value)
        self._settings[setting] = value

    def get_setting(self, setting: CameraSetting):
        if setting in self._settings:
            return self._settings[setting]

        value = getattr(self._camera, setting.value.camera_getter_name)
        self._settings[setting] = value
        return value

    def refresh_settings(self):
        # TODO
        raise NotImplementedError

    def open(self):
        framerate = self.get_setting(CameraSetting.FRAMERATE)
        if not framerate:
            framerate = 30
        self._camera = PiCamera(
            resolution=self.get_setting(CameraSetting.RESOLUTION),
            framerate=framerate, sensor_mode=0)
        self._raw_capture = PiRGBArray(self._camera)

        self.set_setting(CameraSetting.SHUTTER_SPEED, ShutterSpeed.auto.value)

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

    def maximize_fps(self):
        current_shutter_speed = self.get_setting(CameraSetting.SHUTTER_SPEED)
        max_fps = Fraction(current_shutter_speed, 1000000)
        logging.getLogger(__name__).debug("Having exposure speed of %f, the"
                                          " maximum framerate is %s",
                                          current_shutter_speed, max_fps)
        self._camera.framerate = max_fps
        self.set_setting(CameraSetting.FRAMERATE, max_fps)

    def set_shutter_speed(self, value: str):
        if "/" in value:
            denom = int(value.split("/")[1])
            microseconds = int(1000000 / denom)
        else:
            seconds = float(value)
            microseconds = int(seconds * 1000000)

        if 1000000 / self._camera.framerate < microseconds:
            logging.getLogger(__name__).warning(
                "Framerate is too fast for this shutter speed")
            if self.get_setting(CameraSetting.FRAMERATE) is None:
                new_framerate = Fraction(1000000 / microseconds)
                logging.getLogger(__name__).info(
                    "Changing the framerate to be %s", new_framerate)
                self._camera.framerate = new_framerate

        logging.getLogger(__name__).debug("Set shutter speed value to %s (%d)",
                                          value, microseconds)
        self.set_setting(CameraSetting.SHUTTER_SPEED, microseconds)

    def take_picture(self, filename: str):
        logging.getLogger(__name__).debug("Take new picture")
        self._camera.capture(filename)

    def preview(self):
        for frame in self._camera.capture_continuous(self._raw_capture,
                                                     format="bgr",
                                                     use_video_port=True):
            image = Image(frame.array)
            # clear the stream for the next frame
            self._raw_capture.truncate(0)
            yield image

    def apply_preset(self, preset: Preset):
        self.set_setting(CameraSetting.AWB_GAINS, preset.awb_gains)
        self.set_setting(CameraSetting.AWB_MODE, preset.awb_mode)
        self.set_setting(CameraSetting.ISO, preset.iso)
        self.set_setting(CameraSetting.BRIGHTNESS, preset.brightness)
        self.set_setting(CameraSetting.CONTRAST, preset.contrast)
        self.set_setting(CameraSetting.EXPOSURE, preset.exposure)
        self.set_setting(CameraSetting.SHUTTER_SPEED, preset.shutter_speed)
        self.set_setting(CameraSetting.LED, preset.led)
