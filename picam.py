# -*- coding: utf-8 -*-
import logging
import os
import os.path
import re
import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QStackedWidget
from PyQt5.QtCore import Qt, QTimer, QObject, QThread, pyqtSignal

import mainwindow
import img_viewer
try:
    from camera import Camera, Image
except ModuleNotFoundError:
    from virtualcamera import Camera, Image


IMAGES_DIRECTORY = "./images"


class Storage:
    def __init__(self, path, extension, num_digits: int = 4):
        self.path = path
        self.extension = extension
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
        img_regex = re.compile(f"IMG(\d+)\.{self.extension}")
        for f in files:
            if img_regex.match(f):
                img_id = int(img_regex.match(f).group(1))
                self._next_id = max(self._next_id, img_id + 1)

        if self._next_id != 0:
            logger.info("Storage has found existing images, starting at id"
                        " %d", self._next_id)
        else:
            logger.info("Storage has not found any image. Starting at id 0")

    def get_new_name(self):
        img_name = f"IMG{self._next_id:0{self._num_digits}}.{self.extension}"
        self._next_id += 1
        return os.path.join(self.path, img_name)


class ShutterWorker(QObject):
    finished = pyqtSignal()
    captured = pyqtSignal(Image)

    def __init__(self, camera, filename):
        super().__init__()
        self.camera = camera
        self.filename = filename

    def run(self):
        self.camera.take_picture(self.filename)
        self.captured.emit(Image.from_file(self.filename))
        self.finished.emit()


class Settings(QWidget, mainwindow.Ui_Form):
    def __init__(self, cam: Camera, storage: Storage):
        super().__init__()
        self._init_camera(cam)
        self.storage = storage
        self.previewing = False

        # Setup UI
        self.setupUi(self)

        self.widgetImgViewer.set_camera(cam)

        self._hide_image_timer = QTimer(self)
        self._hide_image_timer.timeout.connect(self._hide_image)

        self._shutter_thread = None
        self._shutter_worker = None

        self.btnShutter.clicked.connect(self.pressed_shutter)
        self.btnTogglePreview.clicked.connect(self.toggle_preview)

        # Tabs:
        # (0) Image settings
        self.comboboxIso.currentTextChanged.connect(
                lambda val: self.cam.set_iso(int(val)))
        self.sliderAwbGain.valueChanged.connect(
                lambda v: self.cam.set_awb_gain(float(v)))
        self.comboboxAwbMode.currentTextChanged.connect(
                self._set_awb_mode)
        self.sliderBrightness.valueChanged.connect(
                lambda val: self.cam.set_brightness(int(val)))
        self.comboboxExposure.currentTextChanged.connect(
                self.cam.set_exposure)
        self.comboboxShutterSpeed.currentTextChanged.connect(
                lambda val: self.cam.set_shutter_speed(val))
        self.comboboxDelay.currentTextChanged.connect(
                lambda val: self.cam.set_delay(int(val)))
        # (1) Timelapse
        self.spinboxTimelapseDelay.valueChanged.connect(
                lambda val: print(val))
        self.spinboxTimelapseCount.valueChanged.connect(
                lambda val: print(val))
        # (2) Other
        self.checkboxLed.stateChanged.connect(self._set_led)
        self.checkboxDenoise.stateChanged.connect(
                lambda val: print(val))
        self.buttonMaxFps.clicked.connect(self.cam.maximize_fps)
        self.comboboxImageFormat.currentTextChanged.connect(
                lambda val: print(val))
        self.sliderSharpness.valueChanged.connect(
                lambda val: print(val))
        self.sliderSaturation.valueChanged.connect(
                lambda val: print(val))
        self.comboboxMetermode.currentTextChanged.connect(
                lambda val: print(val))
        self.sliderContrast.valueChanged.connect(
                lambda val: self.cam.set_contrast(int(val)))
        self.comboboxDrc.currentTextChanged.connect(
                lambda val: print(val))

    def _init_camera(self, cam):
        self.cam = cam
        logging.getLogger(__name__).info("Camera exposure speed is: %s",
                                         self.cam.get_exposure_speed())
        self.cam.set_led(False)

    def _set_awb_mode(self, value: str):
        self.sliderAwbGain.setEnabled(value == "Off")
        self.cam.set_awb_mode(value)

    def _set_led(self, value):
        self.cam.set_led(bool(value))

    def _set_denosie(self, value):
        value = bool(value)
        logging.getLogger(__name__).debug(f"Denoise: {value}")

    def pressed_shutter(self):
        if self.previewing:
            self.toggle_preview()
        filename = self.storage.get_new_name()

        # create the qthread and the worker
        self._shutter_thread = QThread()
        self._shutter_worker = ShutterWorker(self.cam, filename)
        # move the worker to the thread
        self._shutter_worker.moveToThread(self._shutter_thread)

        # connect signals and slots
        self._shutter_thread.started.connect(self._shutter_worker.run)
        self._shutter_worker.finished.connect(self._shutter_thread.quit)
        self._shutter_worker.finished.connect(self._shutter_worker.deleteLater)
        self._shutter_thread.finished.connect(self._shutter_thread.deleteLater)
        self._shutter_worker.captured.connect(
                lambda img: self._display_image(img, 5))

        # run the thread
        self._shutter_thread.start()
        
        # disable the button until the thread finishes
        self.btnShutter.setEnabled(False)
        self._shutter_thread.finished.connect(
                lambda: self.btnShutter.setEnabled(True))

    def toggle_preview(self):
        if self.previewing:
            self.previewing = False
            self.widgetImgViewer.stop_preview()
        else:
            self.previewing = True
            self.widgetImgViewer.start_preview()

    def _display_image(self, image, timeout=None):
        self.widgetImgViewer.set_image(image)

        if timeout is not None:
            self._hide_image_timer.start(timeout * 1000)
    
    def _hide_image(self):
        self.widgetImgViewer.hide_image()
        self.widgetImgViewer.set_info_message("Preview disabled")
        self._hide_image_timer.stop()


class Controller(QMainWindow):
    def __init__(self, cam, storage):
        super().__init__()

        self.cam = cam
        self.storage = storage

        # windows
        self.settings = Settings(self.cam, self.storage)

        self.full_preview = img_viewer.FullscreenViewer()
        self.full_preview.set_camera(self.cam)

        self.settings.widgetImgViewer.fullscreen_on.connect(
            lambda: self.toggle_fullscreen(True))
        self.full_preview.fullscreen_off.connect(
            lambda: self.toggle_fullscreen(False))

        self.pages = {
            "settings": (self.settings, 0),
            "preview": (self.full_preview, 1)
        }

        self.stack = QStackedWidget(self)
        
        for page, _ in self.pages.values():
            self.stack.addWidget(page)

        self.setCentralWidget(self.stack)

    def toggle_fullscreen(self, value: bool):
        if value is True:
            logging.getLogger(__name__).info("Open fullscreen preview")
            self.set_page("preview")
        else:
            logging.getLogger(__name__).info("Exit fullscreen")
            self.set_page("settings")

    def set_page(self, name: str):
        _, idx = self.pages[name]
        logging.getLogger(__name__).debug("Setting page with idx %d", idx)
        self.stack.setCurrentIndex(idx)


def window(cam: Camera, storage: Storage):
    app = QApplication(sys.argv)
    window = Controller(cam, storage)

    window.showFullScreen()

    return app.exec_()


def main():
    logging.basicConfig(level=logging.DEBUG)
    storage = Storage(IMAGES_DIRECTORY, "png")
    storage.start()

    with Camera() as cam:
        exit_code = window(cam, storage)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
