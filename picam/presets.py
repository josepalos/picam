import dataclasses
import json
import logging
from fractions import Fraction
from typing import Tuple, Union, Any, List

from PyQt5 import QtWidgets, QtGui, QtCore

# Typing
from picam.layouts import FlowLayout

Gain = Tuple[float, Fraction]


@dataclasses.dataclass
class Preset:
    awb_gains: Union[Gain, Tuple[Gain, Gain]]
    awb_mode: Any
    iso: Any
    brightness: Any
    contrast: Any
    exposure: Any
    shutter_speed: Any
    led: Any

    @staticmethod
    def default():
        return Preset(
            None, None, None, None, None, None, None, None
        )

    def serialize(self):
        return {
            "shutter_speed": self.shutter_speed,
            "awb_gains": self.awb_gains,
            "awb_mode": self.awb_mode,
            "iso": self.iso,
            "brightness": self.brightness,
            "contrast": self.contrast,
            "exposure": self.exposure,
            "led": self.led
        }

    @classmethod
    def deserialize(cls, data):
        return cls(**data)

    def to_file(self, filename):
        with open(filename, "w") as file_:
            file_.write(json.dumps(self.serialize()))

    @classmethod
    def from_file(cls, filename):
        with open(filename, "r") as file_:
            data = json.loads(''.join(file_.readlines()))
        return cls.deserialize(data)


class PresetWidget(QtWidgets.QWidget):
    apply_preset = QtCore.pyqtSignal(Preset)
    delete_preset = QtCore.pyqtSignal(str)

    def __init__(self, preset_name: str, preset: Preset, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.preset_name = preset_name
        self.preset = preset

        # GUI elements
        self.button = QtWidgets.QPushButton("Apply preset")
        self.delete = QtWidgets.QPushButton("Delete preset")
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel(preset_name))
        layout.addWidget(self.button)
        layout.addWidget(self.delete)
        self.setLayout(layout)

        # Connections
        self.button.clicked.connect(self._apply_preset)
        self.delete.clicked.connect(self._delete)

    def _delete(self):
        self.delete_preset.emit(self.preset_name)

    def _apply_preset(self):
        self.apply_preset.emit(self.preset)

    def paintEvent(self, pe):
        opt = QtWidgets.QStyleOption()
        opt.initFrom(self)
        p = QtGui.QPainter(self)
        self.style().drawPrimitive(QtWidgets.QStyle.PE_Widget, opt, p, self)


class PresetsWidget(QtWidgets.QWidget):
    apply_preset = QtCore.pyqtSignal(Preset)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._presets = dict()

        self.layout = FlowLayout(self)
        self.setLayout(self.layout)

        for name, preset in self._load_presets():
            self.add_preset(name, preset)

    def add_preset(self, name, preset):
        if name in self._presets:
            raise Exception("Preset already exists")
        wPreset = PresetWidget(name, preset)

        self._presets[name] = wPreset
        self.layout.addWidget(wPreset)

        wPreset.apply_preset.connect(self.apply_preset)
        wPreset.delete_preset.connect(self.delete_preset)

    def delete_preset(self, name: str):
        if name not in self._presets:
            logging.getLogger(__name__).warning(
                "Trying to delete a non-existing preset")
            return

        messageBox = QtWidgets.QMessageBox.question(
            self, "Delete?", f"Are you sure to delete preset '{name}'?")
        if messageBox == QtWidgets.QMessageBox.Yes:
            wPreset = self._presets[name]
            del self._presets[name]
            self.layout.removeWidget(wPreset)

    def _load_presets(self) -> List[Tuple[str, Preset]]:
        return [
            (f"Preset_{i}", Preset.default())
            for i in range(5)
        ]
