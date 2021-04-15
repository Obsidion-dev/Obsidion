"""Obsidion Minecraft Discord Bot."""
import asyncio as _asyncio
import logging
import os
import sys as _sys

# Start logging

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

log = logging.getLogger("obsidion")


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
            log.info("Set event loop to use uvloop")
            _asyncio.set_event_loop_policy(_uvloop.EventLoopPolicy())
