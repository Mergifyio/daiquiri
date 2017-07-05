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


if six.PY3:
    from itertools import zip_longest as zipl
else:
    from itertools import izip_longest as zipl

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

    PREFIX = '\033['
    BASE_WHITE = 15
    BASE_MOD = '00;%dm'
    CHART_WHITE = 231
    CHART_MOD = '38;5;%dm'

    def __init__(self, *args, base=False, name=None):
        """Create a new color palette from console values.

        :param args: a color value for each of the default logging levels.
        :param base: (bool) use TTY defined colors instead of 256-color palette.
        """
        self.name = name
        self.base = base
        self.colors = list(args)
        self._level_colors = None

    def __str__(self):
        colors = [c[1] if not isinstance(c, int) else c for c in self.colors]
        return '<Palette %s(%s)>' % (self.name if self.name else '',
                                     ', '.join(map(str, colors)))

    @property
    def level_colors(self):
        # deferred processing, read only
        if self._level_colors is None:
            self._level_colors = self._process_colors()
        return self._level_colors

    def _process_colors(self):
        ret = {}
        # account for custom logging levels, with potential additional colors
        logging_levels = tuple(sorted(logging._levelToName.keys(), reverse=False))

        # use `white` for all levels that extend beyond the palette's values
        white = self.BASE_WHITE if self.base else self.CHART_WHITE

        # create a tuple pair for each level and the palette's colors
        colors = zipl(logging_levels, [white] + self.colors, fillvalue=white)

        # apply text formatting
        for level, color in colors:
            if isinstance(color, tuple):
                # text-decoration modifier
                fmt, c_num = color
            elif isinstance(color, int):
                # no formatting
                fmt, c_num = normal(color)
            else:
                raise ValueError(color)

            if self.base:
                c = self.BASE_MOD % c_num
            else:
                c = self.CHART_MOD % c_num
            ret[level] = '%s%s' % (self.PREFIX, fmt % c)
        return ret


def bold(n):
    """Bold color in Palette.

    :param n: (int)
    """
    return '1;%s', n


def normal(n):
    """Normal, no decorations, color in Palette.

    :param n: (int)
    """
    return '0;%s', n


def underline(n):
    """Underline color in Palette.

    :param n: (int)
    """
    return '4;%s', n


class SwatchMeta(type):
    def __new__(cls, name, bases, dct):
        for k, v in dct.items():
            if isinstance(v, Palette):
                v.name = k
        return super(SwatchMeta, cls).__new__(cls, name, bases, dct)


class Swatches(six.with_metaclass(SwatchMeta, object)):
    """ Collection of default colors. """
    Default = Palette(32, 36, bold(33), bold(31), bold(31), base=True)

    Bright = Palette(226, 220, 214, 202, bold(196))
    Blue = Palette(39, 32, 25, 24, bold(23))
    Cool = Palette(33, 45, 172, 203, bold(125))
    Purple = Palette(183, 141, 171, 90, bold(57))
    Warm = Palette(184, 154, 202, 208, bold(160))


class ColorFormatter(logging.Formatter):
    LEVEL_COLORS = None
    COLOR_STOP = '\033[0m'

    def __init__(self, fmt=None, datefmt=None, style='%', palette=Swatches.Default):
        super(ColorFormatter, self).__init__(fmt, datefmt, style)
        self.palette = palette

    def format(self, record):
        if self.LEVEL_COLORS is None:
            palette = getattr(self, 'palette', Swatches.Default)
            self.LEVEL_COLORS = dict(palette.level_colors)

        if getattr(record, "_stream_is_a_tty", False):
            record.color = self.LEVEL_COLORS[record.levelno]
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
