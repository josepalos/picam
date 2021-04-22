# -*- coding: utf-8 -*-

import logging

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTimer, QObject, QThread, pyqtSignal

try:
    from camera import Image
except ModuleNotFoundError:
    from virtualcamera import Image


class ImageWidget(QtWidgets.QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setScaledContents(True)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.MinimumExpanding
        )

    def set_image(self, image: Image):
        qt_image = image.as_qtimage()
        pixmap = QtGui.QPixmap.fromImage(qt_image)
        self.setPixmap(pixmap)

    def unset_image(self):
        logging.getLogger(__name__).debug("Remove image")
        self.clear()


class PreviewWorker(QObject):
    finished = pyqtSignal()
    new_frame = pyqtSignal(Image)

    def __init__(self, camera):
        super().__init__()
        self.camera = camera
        self._is_running = False

    def run(self):
        logging.getLogger(__name__).debug("Preview worker started")
        self._is_running = True

        for frame in self.camera.preview():
            logging.getLogger(__name__).debug("New image")
            self.new_frame.emit(frame)
            if not self._is_running:
                break

            self.finished.emit()

    def stop(self):
        self._is_running = False


class PreviewWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.camera = None
        self._preview_queue = None
        self._preview_thread = None
        self._preview_worker = None
        self._is_running = False

        # Qt elements
        self._image = ImageWidget()
        self._labelInfo = QtWidgets.QLabel()

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self._image)
        layout.addWidget(self._labelInfo)
        self.setLayout(layout)

    def set_camera(self, cam):
        self.camera = cam

    def set_image(self, image: Image):
        self._image.set_image(image)

    def hide_image(self):
        self._image.unset_image()

    def set_info_message(self, message: str):
        self._labelInfo.setText(message)

    def start_preview(self):
        logging.getLogger(__name__).debug("Start preview")
        self._preview_thread = QThread()
        self._preview_worker = PreviewWorker(self.camera)
        self._preview_worker.moveToThread(self._preview_thread)
        self._preview_thread.started.connect(self._preview_worker.run)
        self._preview_thread.finished.connect(self._preview_thread.deleteLater)
        self._preview_worker.finished.connect(self._preview_thread.quit)
        self._preview_worker.finished.connect(self._preview_worker.deleteLater)
        self._preview_worker.new_frame.connect(self._image.set_image)

        self._preview_thread.start()
        self._is_running = True

    def stop_preview(self):
        if self._is_running:
            logging.getLogger(__name__).debug("Stop preview")
            self._preview_worker.stop()
            self._preview_worker.new_frame.disconnect()
            self.hide_image()
            self._is_running = False

    def _show_preview_image(self):
        if self._preview_queue.empty():
            return

        image = self._preview_queue.get()
        self.set_image(image)

    def is_running(self):
        return self._is_running


class FullscreenViewer(QtWidgets.QWidget):
    fullscreen_off = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._preview = PreviewWidget()
        self._buttonFullscreen = QtWidgets.QPushButton("Exit fullscreen")
        self._buttonStartPreview = QtWidgets.QPushButton("Start preview")
        self._buttonStopPreview = QtWidgets.QPushButton("Stop preview")
        self._buttonStopPreview.setEnabled(False)

        self._buttonFullscreen.clicked.connect(self.exit_fullscreen)
        self._buttonStartPreview.clicked.connect(self.start_preview)
        self._buttonStopPreview.clicked.connect(self.stop_preview)

        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(self._preview, 0, 0, -1, 1)
        layout.addWidget(self._buttonFullscreen, 0, 1)
        layout.addWidget(self._buttonStartPreview, 1, 1)
        layout.addWidget(self._buttonStopPreview, 2, 1)
        self.setLayout(layout)

    def exit_fullscreen(self):
        self.stop_preview()
        self.fullscreen_off.emit()

    def set_camera(self, cam):
        self._preview.set_camera(cam)

    def start_preview(self):
        self._preview.start_preview()
        self._buttonStartPreview.setEnabled(False)
        self._buttonStopPreview.setEnabled(True)
        self._preview.set_info_message("Preview enabled")

    def stop_preview(self):
        self._preview.stop_preview()
        self._buttonStartPreview.setEnabled(True)
        self._buttonStopPreview.setEnabled(False)
        self._preview.set_info_message("Preview disabled")


class ImgViewer(QtWidgets.QWidget):
    fullscreen_on = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # QT elements
        self._preview = PreviewWidget()
        self.buttonFullscreen = QtWidgets.QPushButton("Fullscreen")

        self.buttonFullscreen.clicked.connect(self.open_fullscreen)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self._preview)
        layout.addWidget(self.buttonFullscreen)
        self.setLayout(layout)

    def open_fullscreen(self):
        self.stop_preview()
        self.fullscreen_on.emit()

    def set_camera(self, cam):
        self._preview.set_camera(cam)

    def set_image(self, image: Image):
        self._preview.set_image(image)

    def hide_image(self):
        self._preview.hide_image()

    def set_info_message(self, text: str):
        self._preview.set_info_message(text)

    def start_preview(self):
        self._preview.start_preview()

    def stop_preview(self):
        self._preview.stop_preview()
