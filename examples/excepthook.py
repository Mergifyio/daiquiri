import daiquiri

daiquiri.setup(set_excepthook=False)
logger = daiquiri.getLogger(__name__)

raise Exception("Something went wrong") # This exception will not pass through Daiquiri
