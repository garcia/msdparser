"""
This top-level module re-exports :func:`.parse_msd`, :class:`.MSDParameter`,
and :class:`.MSDParserError` for convenience.
"""
__version__ = "2.1.0rc1"
__all__ = ["MSDParserError", "MSDParameter", "parse_msd"]

from .parser import MSDParserError, parse_msd
from .parameter import MSDParameter
