import daiquiri

daiquiri.setup(debug=False)

logger = daiquiri.getLogger(__name__)
logger.info("It works and log to stderr by default with color!")
