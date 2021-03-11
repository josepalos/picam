# -*- coding: utf-8 -*-
import sys

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow

WIDTH = 800
HEIGHT = 480

import mainwindow

class Camera:
    def __init__(self, cam_num):
        self.cam_num = cam_num

    def grab_images(self, queue):
        cap = cv2.VideoCapture(self.cam-num - 1 + CAP_API)


class Window(QMainWindow, mainwindow.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.count = 0

        self.pressMeButton.clicked.connect(self.pressed_press_me_button)

    def pressed_press_me_button(self):
        self.mainLabel.setText(f"{self.count}")
        self.count += 1


def window():
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    window()
