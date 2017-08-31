import logging

import daiquiri

daiquiri.setup(level=logging.INFO)

logger = daiquiri.getLogger(__name__)
logger.info("It works and log to stderr by default with color!")
