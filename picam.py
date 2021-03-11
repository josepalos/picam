# -*- coding: utf-8 -*-
import queue
import sys

import cv2
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow

import mainwindow


class Window(QMainWindow, mainwindow.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.count = 0

        self.btnPressMe.clicked.connect(self.pressed_press_me_button)
        self.btnShowImg.clicked.connect(lambda: self.set_image("potato.jpg"))

    def pressed_press_me_button(self):
        self.labelMain.setText(f"{self.count}")
        self.count += 1

    def set_image(self, img_path):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape

        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h,
                                            bytes_per_line,
                                            QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.display_width,
                                        self.display_height,
                                        Qt.KeepAspectRatio)

        img = QtGui.QPixmap.fromImage(p)
        self.labelMain.setPixmap(img)


def window():
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())


def main():
    window()


if __name__ == "__main__":
    main()
