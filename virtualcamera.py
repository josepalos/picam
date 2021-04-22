import os.path
import shutil
import time
from fractions import Fraction

import cv2



BASE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
FAKE_IMAGE = os.path.join(BASE_DIRECTORY, "potato.jpg")


class FakePicamera:
    class FakeFrame:
        def __init__(self, frame):
            self.array = frame

    def __init__(self, resolution, framerate, sensor_mode):
        self.resolution = resolution
        self.framerate = framerate
        self.sensor_mode = sensor_mode

        self.awb_mode = None
        self.iso = None
        self.brightness = None
        self.contrast = None
        self.exposure_mode = None
        self.shutter_speed = Fraction(1, 1000)
        self.led = None

    @property
    def exposure_speed(self):
        return self.shutter_speed

    def close(self):
        pass

    def capture(self, filename):
        shutil.copy(FAKE_IMAGE, filename)

    def capture_continuous(self, raw_capture, format, use_video_port):
        while True:
            frame = cv2.imread(FAKE_IMAGE)

            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(frame, f"{time.time()}",
                        (100, 100), font, 3, (0, 255, 0), 2, cv2.LINE_AA)
            yield self.FakeFrame(frame)



class FakePiRGBArray:
    def __init__(self, camera):
        pass

    def truncate(self, size):
        pass
