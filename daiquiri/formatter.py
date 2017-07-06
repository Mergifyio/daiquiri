#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import logging

import six

try:
    from pythonjsonlogger import jsonlogger
except ImportError:
    jsonlogger = None


DEFAULT_FORMAT = (
    "%(asctime)s [%(process)d] %(color)s%(levelname)-8.8s "
    "%(name)s: %(message)s%(color_stop)s"
)


class Palette(object):
    """Object that represents TTY colors."""

    PREFIX = '\033['        # TTY prefix for a color code
    BASE_WHITE = 15         # default colors index 15 is white
    BASE_MOD = '00;%dm'     # default colors format is `00;00m`
    CHART_WHITE = 231       # 256-table colors index 231 is white
    CHART_MOD = '38;5;%dm'  # 256-table foreground `38;5;00m`

    LOG_LEVELS = (
        logging.DEBUG,
        logging.INFO,
        logging.WARN,
        logging.ERROR,
        logging.CRITICAL,
    )

    def __init__(self, debug, info, warn, error, critical,
                 base=False, name=None):
        """Create a new color palette from console values.

        Each argument (in `args`) corresponds to a logging level's color.

        :param debug: color for debug level
        :param info: color for info level
        :param warn: color for warning level
        :param error: color for error level
        :param critical: color for critical level
        :param base: (bool) use TTY defined colors instead of 256-color palette
        """
        self.name = name
        self.base = base
        self.colors = (debug, info, warn, error, critical)
        self._level_colors = None

    def __str__(self):
        colors = (c[1] if not isinstance(c, int) else c for c in self.colors)
        return '<Palette %s(%s)>' % (self.name if self.name else '',
                                     ', '.join(map(str, colors)))

    @property
    def level_colors(self):
        """Mapping of log levels to color prefixes.

        :rtype: dict
        """
        # deferred processing, read only
        if self._level_colors is None:
            self._level_colors = self._process_colors()
        return self._level_colors

    def _process_colors(self):
        """Process mapping of log levels.

        :rtype: dict
        """
        ret = {}
        # apply text formatting
        for level, color in zip(self.LOG_LEVELS, self.colors):
            if isinstance(color, tuple):
                # text-decoration modifier
                fmt, c_num = color
            elif isinstance(color, int):
                # no formatting
                fmt, c_num = '0;%s', color
            else:
                raise ValueError(color)

            if self.base:
                c = self.BASE_MOD % c_num
            else:
                c = self.CHART_MOD % c_num
            ret[level] = '%s%s' % (self.PREFIX, fmt % c)
        return ret

    @staticmethod
    def bold(n):
        """Bold color in Palette.

        :param n: (int)
        :rtype: tuple
        """
        return '1;%s', n

    @staticmethod
    def underline(n):
        """Underline color in Palette.

        :param n: (int)
        :rtype: tuple
        """
        return '4;%s', n


class SwatchMeta(type):
    """Swatches type.

    Used for attaching the palette name, defined in the Swatches
    object, to the Palette instance.
    """
    def __new__(cls, name, bases, dct):
        for k, v in dct.items():
            if isinstance(v, Palette):
                v.name = k
        return super(SwatchMeta, cls).__new__(cls, name, bases, dct)


class Swatches(six.with_metaclass(SwatchMeta, object)):
    """Collection of default colors. """

    # colors from the user defined tty color palette
    Default = Palette(32, 36, Palette.bold(33), Palette.bold(31),
                      Palette.bold(31), base=True)

    # colors from the 256-color table
    Blue = Palette(39, 32, 25, 24, Palette.bold(23))
    Bright = Palette(226, 220, 214, 202, Palette.bold(196))
    Cool = Palette(33, 45, 172, 203, Palette.bold(125))
    Purple = Palette(183, 141, 171, 90, Palette.bold(57))
    Warm = Palette(184, 154, 202, 208, Palette.bold(160))


class ColorFormatter(logging.Formatter):
    COLOR_STOP = '\033[0m'

    def __init__(self, fmt=None, datefmt=None, palette=Swatches.Default):
        super(ColorFormatter, self).__init__(fmt, datefmt)
        self.palette = palette

    def format(self, record):
        if getattr(record, "_stream_is_a_tty", False):
            record.color = self.palette.level_colors[record.levelno]
            record.color_stop = self.COLOR_STOP
        else:
            record.color = ""
            record.color_stop = ""
        s = super(ColorFormatter, self).format(record)
        del record.color
        del record.color_stop
        return s


TEXT_FORMATTER = ColorFormatter(fmt=DEFAULT_FORMAT)
if jsonlogger:
    JSON_FORMATTER = jsonlogger.JsonFormatter()
