"""Logging configuration shared by backend entry points."""

import logging


def configure_logging(level: str = "INFO") -> None:
    """Configure a concise default log format for local development."""

    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
