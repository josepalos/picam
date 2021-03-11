# -*- coding: utf-8 -*-
import logging
import queue
import sys

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt

import mainwindow
from virtualcamera import Camera

class Window(QMainWindow, mainwindow.Ui_MainWindow):
    def __init__(self, camera: Camera):
        super().__init__()
        self.setupUi(self)

        self.camera = camera
        self.preview_enabled = False

        self.btnShutter.clicked.connect(self.pressed_shutter)
        self.btnTogglePreview.clicked.connect(self.toggle_preview)

        self.comboboxIso.currentTextChanged.connect(lambda val: self.camera.set_iso(int(val)))
        self.comboboxDelay.currentTextChanged.connect(lambda val: self.camera.set_delay(int(val)))
        self.spinboxBrightness.valueChanged.connect(lambda val: self.camera.set_brightness(int(val)))
        self.spinboxContrast.valueChanged.connect(lambda val: self.camera.set_contrast(int(val)))
        self.spinboxShutterSpeed.valueChanged.connect(lambda val: self.camera.set_shutter_speed(int(val)))

    def preview_window_dimensions(self):
        return self.labelImg.width(), self.labelImg.height()

    def pressed_shutter(self):
        self.camera.take_picture()
        # TODO show in the image frame the last taken image

    def toggle_preview(self):
        self.preview_enabled = not self.preview_enabled

        if self.preview_enabled:
            image = self.camera.get_image()
            qt_image = image.as_qtimage()
            pixmap = QtGui.QPixmap.fromImage(qt_image)

            width, height = self.preview_window_dimensions()
            pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio)

            self.labelImg.setPixmap(pixmap)
        else:
            self.labelImg.setText("Preview disabled")
    

def window(camera: Camera):
    app = QApplication(sys.argv)
    window = Window(camera)

    window.show()
    sys.exit(app.exec_())


def main():
    logging.basicConfig(level=logging.DEBUG)
    camera = Camera()
    window(camera)


if __name__ == "__main__":
    main()
