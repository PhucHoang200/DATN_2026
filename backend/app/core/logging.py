import logging


def setup_logger(name: str = "ASATBackend") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False

    return logger