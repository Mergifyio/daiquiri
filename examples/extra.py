import daiquiri

daiquiri.setup(outputs=(
    daiquiri.output.Stream(formatter=daiquiri.formatter.ColorFormatter(
        fmt=daiquiri.output.DEFAULT_FORMAT + " [%(subsystem)s is %(mood)s]")),
    ))

logger = daiquiri.getLogger(__name__, subsystem="example")
logger.info("It works and log to stderr by default with color!",
            mood="happy")
