import logging


def setup_logger():
    logger = logging.getLogger("TS_AUTOMATION")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.propagate = False  # prevents duplicate logs

    return logger


logger = setup_logger()