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


class ImgViewer(QtWidgets.QWidget):
    fullscreen = QtCore.pyqtSignal(bool)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fullscreen = False
        self.camera = None

        self._preview_queue = None
        self._preview_thread = None
        self._preview_worker = None

        # QT elements
        self._image = ImageWidget()
        self._image.set_image(Image.from_file("potato.jpg"))  # TODO remove

        self._buttonFullscreen = QtWidgets.QPushButton("Fullscreen")
        self._buttonFullscreen.clicked.connect(self.toggle_fullscreen)

        self._labelInfo = QtWidgets.QLabel()

        self._setup_layout()

    def set_camera(self, camera):
        self.camera = camera

    def _setup_layout(self):
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._image)
        layout.addWidget(self._buttonFullscreen)
        layout.addWidget(self._labelInfo)
        self.setLayout(layout)

    def toggle_fullscreen(self):
        self.fullscreen.emit(self._fullscreen)
        self._fullscreen = not self._fullscreen

    def set_image(self, image: Image):
        self._image.set_image(image)

    def hide_image(self):
        self._image.unset_image()

    def set_info_message(self, text: str):
        self._labelInfo.setText(text)

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

    def stop_preview(self):
        logging.getLogger(__name__).debug("Stop preview")
        self._preview_worker.stop()
        self._preview_worker.new_frame.disconnect()
        self.hide_image()

    def _show_preview_image(self):
        if self._preview_queue.empty():
            return

        image = self._preview_queue.get()
        self.set_image(image)
