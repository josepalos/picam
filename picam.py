# -*- coding: utf-8 -*-
import logging
import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QStackedWidget, QScroller
from PyQt5.QtCore import Qt, QTimer, QObject, QThread, pyqtSignal, QFile, QIODevice

import mainwindow
import img_viewer
from storage import Storage, IMAGES_DIRECTORY
from camera import Camera, Image


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


class SettingsWidget(QWidget, mainwindow.Ui_Form):
    def __init__(self, cam: Camera, storage: Storage):
        super().__init__()
        self._init_camera(cam)
        self.storage = storage
        self.previewing = False
        self._extension_selected = None

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
                lambda val: self.cam.set_delay(int(val)))
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

    def _init_camera(self, cam):
        self.cam = cam
        logging.getLogger(__name__).info("Camera exposure speed is: %s",
                                         self.cam.get_exposure_speed())
        self.cam.set_led(False)

    def _set_extension(self, value: str):
        self._extension_selected = value.lower()

    def _set_awb_mode(self, value: str):
        self.sliderAwbGain.setEnabled(value == "Off")
        self.cam.set_awb_mode(value.lower())

    def _set_led(self, value):
        self.cam.set_led(bool(value))

    def _set_denosie(self, value):
        value = bool(value)
        logging.getLogger(__name__).debug(f"Denoise: {value}")

    def pressed_shutter(self):
        if self.previewing:
            self.toggle_preview()
        filename = self.storage.get_new_name(self._extension_selected)

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
        self.settings = SettingsWidget(self.cam, self.storage)

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
    qss_file = QFile("stylesheet.qss")
    if not qss_file.open(QIODevice.ReadOnly | QIODevice.Text):
        logging.getLogger(__name__).warning("Could not load stylesheet")
        return

    app.setStyleSheet(bytes(qss_file.readAll()).decode())



def main():
    logging.basicConfig(level=logging.DEBUG)
    storage = Storage(IMAGES_DIRECTORY)
    storage.start()

    with Camera() as cam:
        app = QApplication(sys.argv)
        load_stylesheet(app)
        controller = Controller(cam, storage)
        # controller.showFullScreen()
        controller.show()
        controller.resize(480, 320)
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
