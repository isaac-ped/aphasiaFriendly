import logging

logger = logging.getLogger(__name__)


class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    lightgreen = "\033[1;32m"
    lightcyan = "\033[1;36m"
    format_ = "%(levelname)s - %(message)s"

    FORMATS = {
        logging.DEBUG: lightcyan + format_ + reset,
        logging.INFO: lightgreen + format_ + reset,
        logging.WARNING: yellow + format_ + reset,
        logging.ERROR: red + format_ + reset,
        logging.CRITICAL: bold_red + format_ + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logging(level: int):
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setFormatter(CustomFormatter())

    # Set up logger' with level based on the passed in value
    if level == 0:
        logger.setLevel(logging.WARNING)
    elif level == 1:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.DEBUG)
    logger.addHandler(ch)

    # if level == 0:
    #     logging.basicConfig(level=logging.INFO, handlers=[ch])
    # elif level > 0:
    #     logging.basicConfig(level=logging.DEBUG, handlers=[ch])
