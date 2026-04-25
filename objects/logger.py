"""Centrální logging pro ZM2_Mereni.

Úrovně:
    DEBUG   — podrobné informace o parsování a výpočtech (jen s --verbose)
    INFO    — normální výstup uživateli (výchozí)
    WARNING — varování (chybějící data, padnutý fit)
    ERROR   — chyby které brání pokračování
"""

import logging
import sys

_LOGGER_NAME = "zm2"
_configured = False


def get_logger(name: str = _LOGGER_NAME) -> logging.Logger:
    return logging.getLogger(name)


def configure(verbose: bool = False, quiet: bool = False, no_color: bool = False) -> None:
    """Nastaví úroveň a handler. Lze volat opakovaně, přepíše konfiguraci."""
    global _configured
    logger = logging.getLogger(_LOGGER_NAME)
    for h in list(logger.handlers):
        logger.removeHandler(h)

    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    if no_color:
        fmt = "%(message)s"
    else:
        fmt = "%(message)s"
    handler.setFormatter(logging.Formatter(fmt))
    logger.addHandler(handler)
    logger.propagate = False
    _configured = True


def is_configured() -> bool:
    return _configured
