"""SOMA: a programming language for the simulation of embodied consciousness.

Public API:
    from soma import run_source, parse, sift, viz, query, observables
"""
from .parser import parse
from .interpreter import run_source, Interpreter, Result
from .checker import check, SomaTypeError, ConsentError
from . import winnow
from . import viz
from . import query
from . import observables
from . import mathlib

sift = winnow.sift
run_query = query.run_query


def run_file(path, *, title=None):
    """Parse and run a .soma file from disk, returning the interpreter Result.
    The file-based twin of `run_source`, for programs kept as files -- including
    files written in the playground's workspace."""
    with open(path) as f:
        text = f.read()
    if title is None:
        import os as _os
        title = _os.path.splitext(_os.path.basename(str(path)))[0]
    return run_source(text, title=title)

integrated_information = observables.integrated_information

__all__ = ["parse", "run_source", "run_file", "Interpreter", "Result", "check",
           "SomaTypeError", "ConsentError", "winnow", "viz", "sift",
           "query", "run_query", "observables", "integrated_information",
           "mathlib"]
__version__ = "0.27.0"
