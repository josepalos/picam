import dataclasses
import json
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

    def __init__(self, preset_name: str, preset: Preset, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.preset_name = preset_name
        self.preset = preset

        # GUI elements
        self.button = QtWidgets.QPushButton("Apply preset")
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel(preset_name))
        layout.addWidget(self.button)
        self.setLayout(layout)

        # Connections
        self.button.clicked.connect(self._apply_preset)

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
        self._presets = self._load_presets()

        self.layout = FlowLayout(self)

        for name, preset in self._presets:
            wPreset = PresetWidget(name, preset)
            self.layout.addWidget(wPreset)
            wPreset.apply_preset.connect(self.apply_preset)

        self.setLayout(self.layout)

    def _load_presets(self) -> List[Tuple[str, Preset]]:
        return [
            (f"Preset_{i}", Preset.default())
            for i in range(20)
        ]
