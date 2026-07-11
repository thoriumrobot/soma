"""
Arc: a small helper for shaping a channel's value across a span of time.

Writing a long stimulus timeline by hand -- `at 1y: 9  at 3y: 2 ...` -- is the
kind of low-level bookkeeping this library exists to remove. An Arc describes
the *shape* of how something changes (a face that varies, a threat that ramps,
a signal that fades) and expands into the individual timed events.

    from soma.narrative import arc

    # a face that varies unpredictably for thirty years, then goes still
    story.at_arc(mira.face_events(
        arc.wobble(around=5, span="24y", every="2y") + arc.hold(0, at="25y")))

Arcs are plain lists of (time, value) pairs under the hood, so they compose with
`+` and can be mixed with hand-written beats.
"""
from __future__ import annotations


class Arc:
    """A sequence of (time_string, value) beats for one channel."""

    def __init__(self, beats=None):
        self.beats = list(beats or [])

    def __add__(self, other):
        if isinstance(other, Arc):
            return Arc(self.beats + other.beats)
        return NotImplemented

    def __iter__(self):
        return iter(self.beats)

    def __len__(self):
        return len(self.beats)


def _sec(t):
    if isinstance(t, (int, float)):
        return float(t)
    units = {"ms": 1e-3, "s": 1.0, "m": 60.0, "h": 3600.0, "d": 86400.0,
             "y": 31_536_000.0}
    t = str(t).strip()
    for u in ("ms", "s", "m", "h", "d", "y"):
        if t.endswith(u):
            return float(t[:-len(u)]) * units[u]
    return float(t)


def _fmt(sec, unit):
    v = sec / {"ms": 1e-3, "s": 1.0, "m": 60.0, "h": 3600.0,
               "d": 86400.0, "y": 31_536_000.0}[unit]
    v = int(v) if float(v).is_integer() else round(v, 3)
    return f"{v}{unit}"


def hold(value, *, at):
    """A single beat: set the channel to `value` at time `at`."""
    return Arc([(at, value)])


def ramp(frm, to, *, span, steps=5, start="0s", unit=None):
    """Linearly move a channel from `frm` to `to` across `span`."""
    unit = unit or _unit_of(span)
    t0 = _sec(start)
    total = _sec(span)
    beats = []
    for i in range(steps + 1):
        frac = i / steps
        t = t0 + frac * total
        val = frm + (to - frm) * frac
        beats.append((_fmt(t, unit), round(val, 3)))
    return Arc(beats)


def wobble(*, around, span, every, amplitude=None, start="1s", unit=None):
    """A value that oscillates unpredictably around a center -- a face that
    keeps being a living face. Alternates above/below `around`."""
    unit = unit or _unit_of(span)
    amp = amplitude if amplitude is not None else max(2, around)
    t0 = _sec(start)
    total = _sec(span)
    step = _sec(every)
    beats = []
    i = 0
    t = t0
    pattern = [amp, -amp, amp * 0.6, -amp * 0.6, amp * 0.9, -amp * 0.3]
    while t <= t0 + total + 1e-9:
        delta = pattern[i % len(pattern)]
        beats.append((_fmt(t, unit), round(max(0, around + delta), 3)))
        t += step
        i += 1
    return Arc(beats)


def fade(frm, *, span, to=0, steps=5, start="0s", unit=None):
    """A signal that decays toward `to` (grief thinning, a wound quieting)."""
    return ramp(frm, to, span=span, steps=steps, start=start, unit=unit)


def _unit_of(span):
    span = str(span).strip()
    for u in ("ms", "y", "d", "h", "m", "s"):
        if span.endswith(u):
            return u
    return "s"


# a module-level namespace object so `arc.wobble(...)` reads nicely
class _ArcNamespace:
    Arc = Arc
    hold = staticmethod(hold)
    ramp = staticmethod(ramp)
    wobble = staticmethod(wobble)
    fade = staticmethod(fade)


arc = _ArcNamespace()
