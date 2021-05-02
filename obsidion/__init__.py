"""Obsidion Minecraft Discord Bot."""
import logging
import sys as _sys

import sentry_sdk
from obsidion.core.config import get_settings

# Start logging

logging.basicConfig(level=get_settings().LOGLEVEL)

log = logging.getLogger("obsidion")

sentry_sdk.init(
    "https://cffd178fe41f46eeb652b691af9af56a@o404225.ingest.sentry.io/5267607",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,
)


MIN_PYTHON_VERSION = (3, 8, 1)

__all__ = [
    "MIN_PYTHON_VERSION",
    "__version__",
    "_update_event_loop_policy",
]

__version__ = "1.0.0"
log.info("Succesfully loaded bot version: %s", __version__)

# check wether the bot can run
if _sys.version_info < MIN_PYTHON_VERSION:
    log.critical(
        "Python %s is required to run Obsidion, but you have %s! Please update Python.",
        ".".join(map(str, MIN_PYTHON_VERSION)),
        _sys.version,
    )
    print(
        f"Python {'.'.join(map(str, MIN_PYTHON_VERSION))}",
        "is required to run Obsidion, but you have ",
        f"{_sys.version}! Please update Python.",
    )
    _sys.exit(1)


def _update_event_loop_policy() -> None:
    """Update loop policy to use uvloop if possible."""
    if _sys.implementation.name == "cpython":
        # Let's not force this dependency, uvloop is much faster on cpython
        try:
            import uvloop as _uvloop
        except ImportError:
            log.warning(
                "Unable to set event loop to use uvloop, using slower default instead."
            )
            pass
        else:
            _uvloop.install()
            log.info("Set event loop to use uvloop")
