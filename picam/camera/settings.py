from collections import namedtuple
from enum import Enum
from fractions import Fraction

Range = namedtuple("Range", "min max default")


ISOS = [100, 200, 320, 400, 500, 640, 800]

AWB_GAIN_RANGE = Range(0, 80, 0)


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


BRIGHTNESS_RANGE = Range(0, 99, 50)


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

SHUTTER_SPEEDS = [
    Fraction(1, 8000),
    Fraction(1, 4000),
    Fraction(1, 2000),
    Fraction(1, 1000),
    Fraction(1, 500),
    Fraction(1, 250),
    Fraction(1, 125),
    Fraction(1, 60),
    Fraction(1, 30),
    Fraction(1, 15),
    Fraction(1, 8),
    Fraction(1, 4),
    Fraction(1, 2),
    1,
    2,
    4,
    6
]

DELAYS = [0, 2, 10]

SHARPNESS_RANGE = Range(-100, 100, 0)

SATURATION_RANGE = Range(-100, 100, 0)


class MeterMode(Enum):
    AVERAGE = "Average"
    SPOT = "Spot"
    BACKLIT = "Backlit"
    MATRIX = "Matrix"


CONTRAST_RANGE = Range(-100, 100, 0)


class DrcStrength(Enum):
    OFF = "Off"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
