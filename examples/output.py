import daiquiri
import sys


daiquiri.setup(outputs=(
    daiquiri.output.Stream(sys.stdout),
    daiquiri.output.File("/dev/null",
                         formatter=daiquiri.output.JSON_FORMATTER),
    ))

logger = daiquiri.getLogger(__name__, subsystem="example")
logger.info("It works and log to stdout and /dev/null with JSON")
