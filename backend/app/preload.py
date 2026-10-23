"""Loaded only by the isolated fork server, before it accepts worker requests."""
from .engine import analyzer
analyzer()

from .languages import identifier
identifier()
