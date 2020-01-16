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

from pythonjsonlogger import jsonlogger


DEFAULT_FORMAT = (
    "%(asctime)s [%(process)d] %(color)s%(levelname)-8.8s "
    "%(name)s: %(message)s%(color_stop)s"
)

DEFAULT_EXTRAS_FORMAT = (
    "%(asctime)s [%(process)d] %(color)s%(levelname)-8.8s "
    "%(name)s%(extras)s: %(message)s%(color_stop)s"
)


class ColorFormatter(logging.Formatter):
    """Colorizes log output"""

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
    """Formats extra keywords into %(extras)s placeholder.

    Any keywords passed to a logging call will be formatted into a
    "extras" string and included in a logging message.
    Example:
        logger.info('my message', extra='keyword')
    will cause an "extras" string of:
        [extra: keyword]
    to be inserted into the format in place of %(extras)s.

    The optional `keywords` argument must be passed into the init
    function to enable this functionality. Without it normal daiquiri
    formatting will be applied. Any keywords included in the
    `keywords` parameter will not be included in the "extras" string.

    Special keywords:

    keywords
      A set of strings containing keywords to filter out of the
      "extras" string.

    extras_template
      A format string to use instead of '[{0}: {1}]'

    extras_separator
      What string to "join" multiple "extras" with.

    extras_prefix and extras_suffix
      Strings which will be prepended and appended to the "extras"
      string respectively. These will only be prepended if the
      "extras" string is not empty.
    """

    def __init__(self,
                 keywords=None,
                 extras_template='[{0}: {1}]',
                 extras_separator=' ',
                 extras_prefix=' ',
                 extras_suffix='',
                 *args, **kwargs):
        self.keywords = set() if keywords is None else keywords
        self.extras_template = extras_template
        self.extras_separator = extras_separator
        self.extras_prefix = extras_prefix
        self.extras_suffix = extras_suffix
        super(ExtrasFormatter, self).__init__(*args, **kwargs)

    def add_extras(self, record):
        if not hasattr(record, '_daiquiri_extra_keys'):
            record.extras = ''
            return

        extras = self.extras_separator.join(
            self.extras_template.format(k, getattr(record, k))
            for k in record._daiquiri_extra_keys
            if k != '_daiquiri_extra_keys' and k not in self.keywords
        )
        if extras != '':
            extras = self.extras_prefix + extras + self.extras_suffix
        record.extras = extras

    def remove_extras(self, record):
        del record.extras

    def format(self, record):
        self.add_extras(record)
        s = super(ExtrasFormatter, self).format(record)
        self.remove_extras(record)
        return s


class ColorExtrasFormatter(ColorFormatter, ExtrasFormatter):
    """Combines functionality of ColorFormatter and ExtrasFormatter."""

    def format(self, record):
        self.add_color(record)
        s = ExtrasFormatter.format(self, record)
        self.remove_color(record)
        return s


class DatadogFormatter(jsonlogger.JsonFormatter):
    def __init__(self):
        super(DatadogFormatter, self).__init__(timestamp=True)

    def add_fields(self, log_record, record, message_dict):
        super(DatadogFormatter, self).add_fields(
            log_record, record, message_dict
        )
        log_record["status"] = record.levelname.lower()
        log_record["logger"] = {
            "name": record.name,
        }
        if record.exc_info:
            log_record["error"] = {
                "kind":  record.exc_info[0].__name__,
                "stack": message_dict.get("stack_info"),
                "message": message_dict.get("exc_info"),
            }
            log_record.pop("exc_info", None)
            log_record.pop("stack_info", None)


TEXT_FORMATTER = ColorExtrasFormatter(fmt=DEFAULT_EXTRAS_FORMAT)
JSON_FORMATTER = jsonlogger.JsonFormatter()
DATADOG_FORMATTER = DatadogFormatter()
