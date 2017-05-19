import daiquiri
import logging

daiquiri.setup(outputs=(
    daiquiri.output.Stream(formatter=logging.Formatter(
        fmt=daiquiri.output.DEFAULT_FORMAT + " [%(subsystem)s is %(mood)s]")),
    ))

logger = daiquiri.getLogger(__name__, subsystem="example")
logger.info("It works and log to stderr by default with color!",
            mood="happy")
