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
    "%(name)s: %(message)s%(color_stop)s"
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

    def format(self, record):
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
