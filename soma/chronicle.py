"""
The Chronicle: SOMA's immutable, timestamped, causally-linked event log.

Everything a loop does is appended here. The novelist-facing layer (viz + the
Winnow-S sifter) reads *only* the Chronicle -- it is the single source of truth
about what happened, against which the narrator's story can be measured.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


class Qualia:
    """An opaque phenomenal value.

    You can create one (via `feel`), route it, log it, and ask whether it
    exists -- but there is deliberately NO accessor to its intrinsic content.
    The explanatory gap, made mechanical. Arithmetic/coercion on a Qualia is a
    type error caught by the checker; even at runtime we refuse to reveal a
    number.
    """
    __slots__ = ("kind",)

    def __init__(self, kind: str):
        self.kind = kind

    def __repr__(self):
        return f"Qualia<{self.kind}>"

    # Any attempt to use a quale as a number fails, at runtime too.
    def __float__(self):
        raise TypeError(f"a Qualia<{self.kind}> cannot be coerced to the physical")
    __add__ = __sub__ = __mul__ = __truediv__ = lambda self, o: self.__float__()


@dataclass
class Event:
    t: float                     # simulated time (seconds)
    frame: int
    kind: str                    # 'settle' | 'move' | 'emit' | 'mood' | 'narrate'
                                 #  | 'crash' | 'repair' | 'budget' | 'conflict'
    who: str                     # loop / body / narrator name
    detail: dict = field(default_factory=dict)

    def __repr__(self):
        d = " ".join(f"{k}={v}" for k, v in self.detail.items())
        return f"[t={self.t:>7.2f} #{self.frame:<3} {self.kind:<8} {self.who:<12}] {d}"


class Chronicle:
    def __init__(self):
        self._events: list[Event] = []

    def append(self, ev: Event):
        self._events.append(ev)

    def log(self, t, frame, kind, who, **detail):
        self.append(Event(t, frame, kind, who, detail))

    def __iter__(self):
        return iter(self._events)

    def __len__(self):
        return len(self._events)

    def where(self, **match):
        """Simple structural filter over events (kind=..., who=...)."""
        out = []
        for e in self._events:
            ok = True
            for k, v in match.items():
                if k in ("kind", "who", "t", "frame"):
                    if getattr(e, k) != v:
                        ok = False; break
                else:
                    if e.detail.get(k) != v:
                        ok = False; break
            if ok:
                out.append(e)
        return out

    def of_kind(self, kind: str):
        return [e for e in self._events if e.kind == kind]

    @property
    def events(self):
        return tuple(self._events)   # immutable view
