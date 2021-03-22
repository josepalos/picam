# -*- coding: utf-8 -*-
import logging
import os
import os.path
import queue
import re
import sys
import time
import threading

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt, QTimer, QObject, QThread, pyqtSignal

import mainwindow
from camera import Camera, Image


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
        self._next_id = 0
        files = [f for f in os.listdir(self.path) if os.path.isfile(os.path.join(self.path, f))]
        img_regex = re.compile(f"IMG(\d+)\.{self.extension}")
        for f in files:
            if img_regex.match(f):
                img_id = int(img_regex.match(f).group(1))
                self._next_id = max(self._next_id, img_id + 1)

        if self._next_id != 0:
            logging.getLogger(__name__).info("Storage has found existing images, starting at id %d", self._next_id)
        else:
            logging.getLogger(__name__).info("Storage has not found any image. Starting at id 0")

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
        

class Window(QMainWindow, mainwindow.Ui_MainWindow):
    def __init__(self, cam: Camera, storage: Storage):
        super().__init__()
        self.setupUi(self)

        self.cam = cam
        logging.getLogger(__name__).info("Camera exposure speed is: %s", self.cam._camera.exposure_speed)
        self.storage = storage

        self.previewing = False
        self.preview_timer = QTimer(self)
        self.preview_timer.timeout.connect(self.show_preview_image)
        self.preview_queue = queue.Queue()
        self.preview_thread = None
        self._hide_image_timer = QTimer(self)
        self._hide_image_timer.timeout.connect(self._hide_image)

        self._shutter_thread = None
        self._shutter_worker = None

        self.btnShutter.clicked.connect(self.pressed_shutter)
        self.btnTogglePreview.clicked.connect(self.toggle_preview)

        self.comboboxIso.currentTextChanged.connect(lambda val: self.cam.set_iso(int(val)))
        self.comboboxDelay.currentTextChanged.connect(lambda val: self.cam.set_delay(int(val)))
        self.spinboxBrightness.valueChanged.connect(lambda val: self.cam.set_brightness(int(val)))
        self.spinboxContrast.valueChanged.connect(lambda val: self.cam.set_contrast(int(val)))
        self.comboboxShutterSpeed.currentTextChanged.connect(lambda val: self.cam.set_shutter_speed(val))
        self.checkboxLed.stateChanged.connect(self.set_led)

    def set_led(self, value):
        self.cam.set_led(bool(value))

    def _threaded_capture(self):
        for frame in self.cam.preview():
            self.preview_queue.put(frame)

            if not self.previewing:
                break

    def preview_window_dimensions(self):
        return self.labelImg.width(), self.labelImg.height()

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
        self._shutter_worker.captured.connect(lambda img: self._display_image(img, 5))


        # run the thread
        self._shutter_thread.start()
        
        # disable the button until the thread finishes
        self.btnShutter.setEnabled(False)
        self._shutter_thread.finished.connect(lambda: self.btnShutter.setEnabled(True))

    def toggle_preview(self):
        if self.previewing:
            self.previewing = False
            self.preview_timer.stop()
            self._hide_image()
            self.preview_thread.join()
        else:
            self.previewing = True
            self.preview_timer.start()
            self.preview_thread = threading.Thread(target=self._threaded_capture)
            self.preview_thread.start()

    def _display_image(self, image, timeout=None):
        qt_image = image.as_qtimage()
        pixmap = QtGui.QPixmap.fromImage(qt_image)

        width, height = self.preview_window_dimensions()
        pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio)

        self.labelImg.setPixmap(pixmap)

        if timeout is not None:
            self._hide_image_timer.start(timeout * 1000)
    
    def _hide_image(self):
        self.labelImg.setText("Preview disabled")
        self._hide_image_timer.stop()

    def show_preview_image(self):
        if self.preview_queue.empty():
            return

        image = self.preview_queue.get()
        self._display_image(image)

    

def window(cam: Camera, storage: Storage):
    app = QApplication(sys.argv)
    window = Window(cam, storage)

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
