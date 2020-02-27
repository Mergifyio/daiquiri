import daiquiri

daiquiri.setup(set_excepthook=False)
logger = daiquiri.getLogger(__name__)

# This exception will not pass through Daiquiri:
raise Exception("Something went wrong")
