import daiquiri
import sys

# Log both to stdout and as JSON in a file called /dev/null
daiquiri.setup(outputs=(
    daiquiri.output.Stream(sys.stdout),
    daiquiri.output.File("/dev/null",
                         formatter=daiquiri.formatter.JSON_FORMATTER),
    ))

logger = daiquiri.getLogger(__name__, subsystem="example")
logger.info("It works and log to stdout and /dev/null with JSON")
