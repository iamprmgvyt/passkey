# -*- coding: utf-8 -*-
"""Passkey Bot — Structured Logging Configuration."""
import logging
import sys

def setup_logger():
    logger = logging.getLogger("passkey")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(handler)
    return logger

log = setup_logger()
