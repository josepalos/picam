# -*- coding: utf-8 -*-
import logging
import queue
import sys
import threading

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt, QTimer

import mainwindow
from camera import Camera


class Window(QMainWindow, mainwindow.Ui_MainWindow):
    def __init__(self, camera: Camera):
        super().__init__()
        self.setupUi(self)

        self.camera = camera

        self.previewing = False
        self.preview_timer = QTimer(self)
        self.preview_timer.timeout.connect(self.show_preview_image)
        self.preview_queue = queue.Queue()
        self.preview_thread = None

        self.btnShutter.clicked.connect(self.pressed_shutter)
        self.btnTogglePreview.clicked.connect(self.toggle_preview)

        self.comboboxIso.currentTextChanged.connect(lambda val: self.camera.set_iso(int(val)))
        self.comboboxDelay.currentTextChanged.connect(lambda val: self.camera.set_delay(int(val)))
        self.spinboxBrightness.valueChanged.connect(lambda val: self.camera.set_brightness(int(val)))
        self.spinboxContrast.valueChanged.connect(lambda val: self.camera.set_contrast(int(val)))
        self.spinboxShutterSpeed.valueChanged.connect(lambda val: self.camera.set_shutter_speed(int(val)))

    def _threaded_capture(self):
        for frame in self.camera.preview():
            self.preview_queue.put(frame)

            if not self.previewing:
                break

    def preview_window_dimensions(self):
        return self.labelImg.width(), self.labelImg.height()

    def pressed_shutter(self):
        self.camera.take_picture()
        # TODO show in the image frame the last taken image

    def toggle_preview(self):
        if self.previewing:
            self.previewing = False
            self.preview_timer.stop()
            self.labelImg.setText("Preview disabled")
            self.preview_thread.join()
        else:
            self.previewing = True
            self.preview_timer.start()
            self.preview_thread = threading.Thread(target=self._threaded_capture)
            self.preview_thread.start()

    def _display_image(self, image):
        qt_image = image.as_qtimage()
        pixmap = QtGui.QPixmap.fromImage(qt_image)

        width, height = self.preview_window_dimensions()
        pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio)

        self.labelImg.setPixmap(pixmap)


    def show_preview_image(self):
        if self.preview_queue.empty():
            return

        image = self.preview_queue.get()
        self._display_image(image)

    

def window(camera: Camera):
    app = QApplication(sys.argv)
    window = Window(camera)

    window.showFullScreen()
    sys.exit(app.exec_())


def main():
    logging.basicConfig(level=logging.DEBUG)
    camera = Camera()
    window(camera)

    camera.close()


if __name__ == "__main__":
    main()
