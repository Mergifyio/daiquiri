import daiquiri
import daiquiri.formatter
import logging

daiquiri.setup(level=logging.INFO, outputs=(
    daiquiri.output.Stream(formatter=daiquiri.formatter.ColorFormatter(
        fmt="%(asctime)s [PID %(process)d] [%(levelname)s] "
        "%(name)s -> %(message)s")),
    ))

logger = daiquiri.getLogger(__name__)
logger.info("It works with a custom format!")
