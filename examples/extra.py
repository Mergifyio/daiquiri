import daiquiri
import logging

daiquiri.setup(targets=(
    daiquiri.target.Stream(formatter=logging.Formatter(
        fmt=daiquiri.target.DEFAULT_FORMAT + " [%(subsystem)s is %(mood)s]")),
    ))

logger = daiquiri.getLogger(__name__, subsystem="example")
logger.info("It works and log to stderr by default with color!",
            mood="happy")
