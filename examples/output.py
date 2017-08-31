import logging
import sys

import daiquiri

# Log both to stdout and as JSON in a file called /dev/null. (Requires
# `python-json-logger`)
daiquiri.setup(level=logging.INFO, outputs=(
    daiquiri.output.Stream(sys.stdout),
    daiquiri.output.File("/dev/null",
                         formatter=daiquiri.formatter.JSON_FORMATTER),
    ))

logger = daiquiri.getLogger(__name__, subsystem="example")
logger.info("It works and log to stdout and /dev/null with JSON")
