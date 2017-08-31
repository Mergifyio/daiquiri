import logging

import daiquiri

daiquiri.setup(level=logging.INFO, outputs=('stdout', 'stderr'))

logger = daiquiri.getLogger(__name__)
logger.info("It works and logs to both stdout and stderr!")
