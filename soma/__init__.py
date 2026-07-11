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
integrated_information = observables.integrated_information

__all__ = ["parse", "run_source", "Interpreter", "Result", "check",
           "SomaTypeError", "ConsentError", "winnow", "viz", "sift",
           "query", "run_query", "observables", "integrated_information",
           "mathlib"]
__version__ = "0.9.0"
