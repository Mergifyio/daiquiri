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

try:
    from pythonjsonlogger import jsonlogger
except ImportError:
    jsonlogger = None


DEFAULT_FORMAT = (
    "%(asctime)s [%(process)d] %(color)s%(levelname)-8.8s "
    "%(name)s %(extras)s: %(message)s%(color_stop)s"
)


class ColorFormatter(logging.Formatter):
    # TODO(jd) Allow configuration
    LEVEL_COLORS = {
        logging.DEBUG: '\033[00;32m',  # GREEN
        logging.INFO: '\033[00;36m',  # CYAN
        logging.WARN: '\033[01;33m',  # BOLD YELLOW
        logging.ERROR: '\033[01;31m',  # BOLD RED
        logging.CRITICAL: '\033[01;31m',  # BOLD RED
    }

    COLOR_STOP = '\033[0m'

    def add_color(self, record):
        if getattr(record, "_stream_is_a_tty", False):
            record.color = self.LEVEL_COLORS[record.levelno]
            record.color_stop = self.COLOR_STOP
        else:
            record.color = ""
            record.color_stop = ""

    def remove_color(self, record):
        del record.color
        del record.color_stop

    def format(self, record):
        self.add_color(record)
        s = super(ColorFormatter, self).format(record)
        self.remove_color(record)
        return s


class ExtrasFormatter(logging.Formatter):
    def __init__(self,
                 fmt=None,
                 datefmt=None,
                 style='%',
                 keywords=None,
                 extras_template='[{0}: {1}]',
                 extras_separator=' '):
        self.keywords = keywords
        self.extras_separator = extras_separator
        self.extras_template = extras_template
        super(ExtrasFormatter, self).__init__(fmt=fmt,
                                              datefmt=datefmt,
                                              style=style)

    def add_extras(self, record):
        if self.keywords is None or not hasattr(record, '_daiquiri_extra'):
            return

        # Format any unknown keyword arguments into the extras string.
        extras_string = ''
        separator = ''
        for k, v in record._daiquiri_extra.items():
            if k != '_daiquiri_extra' and k not in self.keywords:
                extras_string += separator + self.extras_template.format(k, v)
                # Only set this after the first iteration to prevent a
                # leading space
                separator = self.extras_separator

        record.extras = extras_string

    def remove_extras(self, record):
        del record.extras

    def format(self, record):
        self.add_extras(record)
        s = super(ExtrasFormatter, self).format(record)
        self.remove_extras(record)
        return s


class ColorExtrasFormatter(ExtrasFormatter, ColorFormatter):
    def format(self, record):
        self.add_color(record)
        s = super(ColorExtrasFormatter, self).format(record)
        self.remove_color(record)
        return s


TEXT_FORMATTER = ColorExtrasFormatter(fmt=DEFAULT_FORMAT)
if jsonlogger:
    JSON_FORMATTER = jsonlogger.JsonFormatter()
