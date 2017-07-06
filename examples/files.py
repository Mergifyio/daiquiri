import daiquiri
import datetime
import logging

daiquiri.setup(
    level=logging.DEBUG,
    outputs=(
        daiquiri.output.File('errors.log', level=logging.ERROR),
        daiquiri.output.TimedRotatingFile(
            'everything.log',
            level=logging.DEBUG,
            interval=datetime.timedelta(hours=1))
    )
)

logger = daiquiri.getLogger(__name__)

logger.info('only to rotating file logger')
logger.error('both log files, including errors only')
