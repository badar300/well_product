"""PyInstaller runtime hook: ensure stdlib logging.config is loadable before app code."""

import importlib.util

if importlib.util.find_spec("logging.config") is not None:
    import logging.config  # noqa: F401
