import enum
from collections import namedtuple
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from numbers import Number
from typing import Any


@dataclass
class _Setting:
    camera_getter_name: str
    camera_setter_name: str
    default: Any


@dataclass
class _RangeSetting(_Setting):
    min: Number
    max: Number


@dataclass
class _ChoiceSetting(_Setting):
    choices: enum.Enum.__class__


class Iso(enum.Enum):
    iso100 = 100
    iso200 = 200
    iso320 = 320
    iso400 = 400
    iso500 = 500
    iso640 = 640
    iso800 = 800


class AwbMode(Enum):
    OFF = "Off"
    AUTO = "Auto"
    SUNLIGHT = "Sunlight"
    CLOUDY = "Cloudy"
    SHADE = "Shade"
    TUNGSTEN = "Tungsten"
    FLUORESCENT = "Fluorescent"
    INCANDESCENT = "Incandescent"
    FLASH = "Flash"
    HORIZON = "Horizon"


class Exposure(Enum):
    OFF = "Off"
    AUTO = "Auto"
    NIGHT = "Night"
    NIGHT_PREVIEW = "Nightpreview"
    BACKLIGHT = "Backlight"
    SPOTLIGHT = "Spotlight"
    SPORTS = "Sports"
    SNOW = "Snow"
    BEACH = "Beach"
    VERY_LING = "Veryling"
    FIXED_FPS = "Fixedfps"
    ANTI_SHAKE = "Antishake"
    FIREWORKS = "Fireworks"


class ShutterSpeed(enum.Enum):
    s_1_8000 = Fraction(1, 8000)
    s_1_4000 = Fraction(1, 4000)
    s_1_2000 = Fraction(1, 2000)
    s_1_1000 = Fraction(1, 1000)
    s_1_500 = Fraction(1, 500)
    s_1_250 = Fraction(1, 250)
    s_1_125 = Fraction(1, 125)
    s_1_60 = Fraction(1, 60)
    s_1_30 = Fraction(1, 30)
    s_1_15 = Fraction(1, 15)
    s_1_8 = Fraction(1, 8)
    s_1_4 = Fraction(1, 4)
    s_1_2 = Fraction(1, 2)
    s_1 = 1
    s_2 = 2
    s_4 = 4
    s_6 = 6


class CameraSetting(enum.Enum):
    RESOLUTION = _Setting("resolution", "resolution", None)
    FRAMERATE = _Setting("framerate", "framerate", None)
    AWB_GAINS = _RangeSetting("awb_gain", "awb_gain", 0, 0, 80)  # TODO accept pairs of values
    AWB_MODE = _ChoiceSetting("awb_mode", "awb_mode", AwbMode.AUTO, AwbMode)
    ISO = _ChoiceSetting("iso", "iso", Iso.iso100, Iso)
    BRIGHTNESS = _RangeSetting("brightness", "brightness", 50, 0, 99)
    CONTRAST = _RangeSetting("contrast", "contrast", 0, -100, 100)
    EXPOSURE = _ChoiceSetting("exposure", "exposure", Exposure.AUTO, Exposure)
    SHUTTER_SPEED = _ChoiceSetting("shutter_speed", "exposure_speed", None, ShutterSpeed)
    LED = _Setting("led", "led", True)


Range = namedtuple("Range", "min max default")

DELAYS = [0, 2, 10]

SHARPNESS_RANGE = Range(-100, 100, 0)

SATURATION_RANGE = Range(-100, 100, 0)


class MeterMode(Enum):
    AVERAGE = "Average"
    SPOT = "Spot"
    BACKLIT = "Backlit"
    MATRIX = "Matrix"


class DrcStrength(Enum):
    OFF = "Off"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
