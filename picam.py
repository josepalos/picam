# -*- coding: utf-8 -*-
import logging
import os.path
import socket
from subprocess import Popen, PIPE
import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QStackedWidget, QScroller
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QFile, QIODevice

import mainwindow
import img_viewer
from storage import Storage
from camera import Camera, REAL_CAMERA


BASE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
IMAGES_DIRECTORY = os.path.join(BASE_DIRECTORY, "images")


def get_commit():
    # Stackoverflow 65076306
    process = Popen(["git", "rev-parse", "--short", "HEAD"],
                    cwd=BASE_DIRECTORY,
                    stderr=PIPE, stdout=PIPE)
    (commit_hash, err) = process.communicate()
    exit_code = process.wait()
    if exit_code != 0:
        logging.getLogger(__name__).warning("Could not detect commit hash")
        return None
    else:
        return commit_hash.decode().strip()


def get_ip():
    # Stackoverflow 166506 (answer from fatal_error)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("1.1.1.1", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


COMMIT = get_commit()


class SettingsWidget(QWidget, mainwindow.Ui_Form):
    def __init__(self, cam: Camera, shutter: img_viewer.Shutter):
        super().__init__()
        self._init_camera(cam)
        self._shutter = shutter
        self._shutter.captured.connect(lambda img: self._display_image(img, 5))

        self.previewing = False

        # Setup UI
        self.setupUi(self)

        self.widgetImgViewer.set_camera(cam)

        self._hide_image_timer = QTimer(self)
        self._hide_image_timer.timeout.connect(self._hide_image)

        self.btnShutter.clicked.connect(self.pressed_shutter)
        self.btnTogglePreview.clicked.connect(self.toggle_preview)

        # Tabs:
        # (0) Image settings
        self.comboboxIso.currentTextChanged.connect(
            lambda val: self.cam.set_iso(int(val)))
        self.sliderAwbGain.valueChanged.connect(
            lambda v: self.cam.set_awb_gain(float(v) / 10))
        self.comboboxAwbMode.currentTextChanged.connect(
            self._set_awb_mode)
        self.sliderBrightness.valueChanged.connect(
            lambda val: self.cam.set_brightness(int(val)))
        self.comboboxExposure.currentTextChanged.connect(
            lambda v: self.cam.set_exposure(v.lower()))
        self.comboboxShutterSpeed.currentTextChanged.connect(
            lambda val: self.cam.set_shutter_speed(val))
        self.comboboxDelay.currentTextChanged.connect(
            lambda val: self._shutter.set_delay(int(val)))
        # (1) Timelapse
        self.spinboxTimelapseDelay.valueChanged.connect(
            lambda val: print(val))
        self.spinboxTimelapseDelay.setEnabled(False)
        self.spinboxTimelapseCount.valueChanged.connect(
            lambda val: print(val))
        self.spinboxTimelapseCount.setEnabled(False)
        # (2) Other
        self.checkboxLed.stateChanged.connect(self._set_led)
        self.checkboxDenoise.stateChanged.connect(
            lambda val: print(val))
        self.checkboxDenoise.setEnabled(False)
        self.buttonMaxFps.clicked.connect(self.cam.maximize_fps)
        self.comboboxImageFormat.currentTextChanged.connect(
            self._set_extension)
        self._set_extension(self.comboboxImageFormat.currentText())

        self.sliderSharpness.valueChanged.connect(
            lambda val: print(val))
        self.sliderSharpness.setEnabled(False)
        self.sliderSaturation.valueChanged.connect(
            lambda val: print(val))
        self.sliderSaturation.setEnabled(False)
        self.comboboxMetermode.currentTextChanged.connect(
            lambda val: print(val))
        self.comboboxMetermode.setEnabled(False)
        self.sliderContrast.valueChanged.connect(
            lambda val: self.cam.set_contrast(int(val)))
        self.comboboxDrc.currentTextChanged.connect(
            lambda val: print(val))
        self.comboboxDrc.setEnabled(False)
        # enable scroll on the last tab
        QScroller.grabGesture(
            self.scrollAreaOtherSettings.viewport(), QScroller.LeftMouseButtonGesture
        )
        # (3) Info
        self.update_info()  # TODO call this periodically?

    def update_info(self):
        ip = get_ip()

        self.labelIp.setText(f"System IP: {ip}")
        self.labelCommit.setText(f"Project version (commit):\n{COMMIT}")
        self.labelRealCamera.setText(f"Using real camera: {REAL_CAMERA}")

    def _init_camera(self, cam):
        self.cam = cam
        logging.getLogger(__name__).info("Camera exposure speed is: %s",
                                         self.cam.get_exposure_speed())
        self.cam.set_led(False)

    def _set_extension(self, value: str):
        self._shutter.capture_format = value.lower()

    def _set_awb_mode(self, value: str):
        self.sliderAwbGain.setEnabled(value == "Off")
        self.cam.set_awb_mode(value.lower())

    def _set_led(self, value):
        self.cam.set_led(bool(value))

    def pressed_shutter(self):
        if self.previewing:
            self.toggle_preview()

        self.btnShutter.setEnabled(False)
        self.btnTogglePreview.setEnabled(False)
        self.widgetImgViewer.buttonFullscreen.setEnabled(False)
        self._shutter.take_picture()
        self._shutter.finished.connect(self._finished_shutter_thread)

    def _finished_shutter_thread(self):
        self.btnShutter.setEnabled(True)
        self.btnTogglePreview.setEnabled(True)
        self.widgetImgViewer.buttonFullscreen.setEnabled(True)

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
    def __init__(self, cam, shutter):
        super().__init__()

        # windows
        self.settings = SettingsWidget(cam, shutter)

        self.full_preview = img_viewer.FullscreenViewer()
        self.full_preview.set_camera(cam)

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
        widget, idx = self.pages[name]
        logging.getLogger(__name__).debug("Setting page with idx %d", idx)
        self.stack.setCurrentIndex(idx)
        widget.setFixedSize(480, 320)


def window(cam: Camera, storage: Storage):
    app = QApplication(sys.argv)
    window = Controller(cam, storage)

    window.showFullScreen()

    return app.exec_()


def load_stylesheet(app):
    qss_file = QFile(os.path.join(BASE_DIRECTORY, "stylesheet.qss"))
    if not qss_file.open(QIODevice.ReadOnly | QIODevice.Text):
        logging.getLogger(__name__).warning("Could not load stylesheet")
        return

    app.setStyleSheet(bytes(qss_file.readAll()).decode())


def main():
    logging.basicConfig(level=logging.DEBUG)
    storage = Storage(IMAGES_DIRECTORY)
    storage.start()

    with Camera() as cam:
        shutter = img_viewer.Shutter(cam, storage)

        app = QApplication(sys.argv)
        load_stylesheet(app)
        controller = Controller(cam, shutter)
        # controller.showFullScreen()
        controller.show()
        controller.resize(480, 320)
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
