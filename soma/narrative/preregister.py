"""
soma.narrative.preregister -- forecasts written down BEFORE the run.

The philosophy-of-science problem this solves: a model that is only ever read
*after* it runs cannot distinguish prediction from accommodation. Accommodation
is easy -- any sufficiently flexible model can be nudged until its output
matches what the author already wanted, and a match obtained that way confirms
nothing (Popper's complaint about theories that explain everything; Hitchcock &
Sober's overfitting analysis; Lipton's fudging). What raises a match into
evidence is that the claim was staked in advance, was specific enough to fail,
and the run was then given an honest chance to falsify it. That is
preregistration, and this module is its instrument for characters:

    audit = story.preregister()
    audit.expect_feeling("Nadia", "dread", by="4s")
    audit.expect_gap("Vera", at_least=0.5)
    audit.expect_break("Ink")
    audit.expect_no_break("Blade")
    audit.expect_mood("Soren", "weather", "falls")
    print(audit.check().render())

`check()` runs the story ONCE, after all claims are sealed, and returns a
verdict per claim -- CONFIRMED or FALSIFIED, each with the Chronicle evidence.
Adding a claim after check() is an error: that is the line between prediction
and postdiction, enforced.

The report also discloses ACCOMMODATIONS: anywhere a theory-derived default
(a coping style's conviction, an attachment style's parameter) was overridden
by hand, the override is listed, because a run that matches a hand-set dial is
a description, not a prediction. The disclosure does not forbid overriding --
a real person may be the exception the type does not cover -- it only keeps
the two kinds of match from being confused.

And the standing caveat, inherited from the whole prediction layer: every
verdict here is a claim about a MODEL of a character, falsifiable against the
model and against a reader's sense of the person -- never a measurement of any
real human being.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Optional


def _secs(v) -> Optional[float]:
    """'4s' | '2m' | 3 -> seconds (None passes through)."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    units = {"ms": 0.001, "s": 1.0, "m": 60.0, "h": 3600.0,
             "d": 86400.0, "y": 31557600.0}
    s = str(v).strip()
    for u in ("ms", "s", "m", "h", "d", "y"):
        if s.endswith(u):
            return float(s[:-len(u)]) * units[u]
    return float(s)


@dataclass
class Verdict:
    claim: str
    ok: bool
    evidence: str


@dataclass
class Report:
    verdicts: list
    accommodations: list

    @property
    def confirmed(self) -> int:
        return sum(1 for v in self.verdicts if v.ok)

    @property
    def falsified(self) -> int:
        return sum(1 for v in self.verdicts if not v.ok)

    @property
    def all_confirmed(self) -> bool:
        return self.falsified == 0

    def render(self) -> str:
        lines = ["PREREGISTERED FORECASTS — staked before the run, checked after"]
        for v in self.verdicts:
            mark = "✓" if v.ok else "✗"
            word = "CONFIRMED" if v.ok else "FALSIFIED"
            lines.append(f"  {mark} {word}: {v.claim}")
            lines.append(f"      {v.evidence}")
        lines.append(f"  {self.confirmed} confirmed, {self.falsified} falsified.")
        if self.accommodations:
            lines.append("  ACCOMMODATIONS (theory defaults overridden by hand; "
                         "matches involving these dials describe, they do not predict):")
            for a in self.accommodations:
                lines.append(f"    - {a}")
        lines.append("  (Verdicts are claims about this model of the character, "
                      "never about a real person.)")
        return "\n".join(lines)


class Preregistration:
    """A sealed list of claims about a story that has not yet been run."""

    def __init__(self, story):
        self.story = story
        self._claims: list = []      # (description, fn(result) -> (ok, evidence))
        self._checked = False

    # ---- registering claims -------------------------------------------------
    def _add(self, desc, fn):
        if self._checked:
            raise RuntimeError(
                "this preregistration has already been checked; a claim added "
                "after seeing the run is a postdiction, not a prediction. "
                "Start a new preregistration for a new run.")
        self._claims.append((desc, fn))
        return self

    def _q(self, who, name):
        """Qualify a name with the character when the story has several."""
        return f"{who}.{name}" if len(self.story.characters) > 1 else name

    def expect_feeling(self, who: str, quale: str, *, present: bool = True,
                       by=None):
        """The character will (or will not) feel `quale`, optionally by time `by`."""
        t_by = _secs(by)
        word = "feels" if present else "never feels"
        desc = f"{who} {word} {quale}" + (f" by {by}" if by else "")

        def fn(r):
            hits = [e for e in r.chronicle
                    if e.kind == "emit" and quale in str(e.detail.get("quale", ""))
                    and (e.who.startswith(f"{who}.") or len(self.story.characters) == 1)
                    and (t_by is None or e.t <= t_by)]
            if present:
                return (bool(hits),
                        f"first at {hits[0].t}s ({len(hits)} in all)" if hits
                        else "no such feeling in the Chronicle")
            return (not hits,
                    "no such feeling in the Chronicle" if not hits
                    else f"felt at {hits[0].t}s ({len(hits)} in all)")
        return self._add(desc, fn)

    def expect_gap(self, who: str, *, at_least: float = 0.4,
                   present: bool = True):
        """The narrator's account will (or will not) split from the record by a
        confabulation gap of at least `at_least`."""
        word = "narrates over a gap" if present else "narrates with no gap"
        desc = f"{who} {word} (>= {at_least})"

        def fn(r):
            # narrate events are logged by the narrator, whose name is
            # "self_<Character>" (or bare in a single-character story), so match
            # that convention rather than the "<who>." loop prefix.
            single = len(self.story.characters) == 1
            def mine(w):
                return (single or w == f"self_{who}" or w.startswith(f"{who}."))
            hits = [e for e in r.chronicle
                    if e.kind == "narrate" and mine(e.who)
                    and e.detail.get("gap", 0) >= at_least]
            if present:
                return (bool(hits),
                        f"gap {max(e.detail['gap'] for e in hits)} at "
                        f"{hits[0].t}s" if hits else "no gap that wide")
            return (not hits, "no gap that wide" if not hits
                    else f"gap {hits[0].detail['gap']} at {hits[0].t}s")
        return self._add(desc, fn)

    def expect_break(self, who: str, *, lie_contains: str = "",
                     by=None):
        """A lie of this character's will break -- a `revelation` will be logged."""
        t_by = _secs(by)
        desc = (f"{who}'s lie breaks (self-revelation)"
                + (f" [{lie_contains}]" if lie_contains else "")
                + (f" by {by}" if by else ""))

        def fn(r):
            hits = [e for e in r.chronicle
                    if e.kind == "revelation"
                    and (e.who.startswith(f"{who}.") or len(self.story.characters) == 1)
                    and lie_contains in e.who
                    and (t_by is None or e.t <= t_by)]
            return (bool(hits),
                    f"revelation at {hits[0].t}s in {hits[0].who}" if hits
                    else "no revelation logged")
        return self._add(desc, fn)

    def expect_no_break(self, who: str, *, lie_contains: str = ""):
        """The lie holds: no revelation. The strongest falsification target of
        all, because a single revelation event anywhere in the run defeats it."""
        desc = (f"{who}'s lie holds (no self-revelation)"
                + (f" [{lie_contains}]" if lie_contains else ""))

        def fn(r):
            hits = [e for e in r.chronicle
                    if e.kind == "revelation"
                    and (e.who.startswith(f"{who}.") or len(self.story.characters) == 1)
                    and lie_contains in e.who]
            return (not hits, "no revelation logged" if not hits
                    else f"revelation at {hits[0].t}s in {hits[0].who}")
        return self._add(desc, fn)

    def expect_mood(self, who: str, mood: str, direction: str, *,
                    margin: float = 0.5):
        """A mood ends meaningfully higher ('rises'), lower ('falls'), or within
        `margin` of where it began ('holds')."""
        assert direction in ("rises", "falls", "holds")
        desc = f"{who}'s mood '{mood}' {direction}"

        def fn(r):
            # the compiler qualifies moods with an underscore ("Nadia_grief")
            h = (r.mood_hist.get(f"{who}_{mood}")
                 or r.mood_hist.get(f"{who}.{mood}")
                 or r.mood_hist.get(mood) or [])
            if len(h) < 2:
                return (False, "mood was never recorded")
            head = sum(h[:3]) / min(3, len(h))
            tail = sum(h[-3:]) / min(3, len(h))
            delta = tail - head
            got = f"delta {delta:+.2f} ({head:.2f} -> {tail:.2f})"
            ok = (delta > margin if direction == "rises" else
                  delta < -margin if direction == "falls" else
                  abs(delta) <= margin)
            return (ok, got)
        return self._add(desc, fn)

    def expect_peak(self, who: str, channel: str, *, at_least: float):
        """A body channel will peak at or above `at_least` -- e.g. the heart's
        record contradicting a narrated calm."""
        desc = f"{who}'s {channel} peaks >= {at_least}"

        def fn(r):
            h = (r.channel_hist.get(f"{who}.{channel}")
                 or r.channel_hist.get(channel) or [])
            if not h:
                return (False, "channel never recorded")
            return (max(h) >= at_least, f"peak {max(h):.1f}")
        return self._add(desc, fn)

    def expect(self, description: str, fn: Callable):
        """An arbitrary claim: fn(result) -> bool or (bool, evidence). Marked
        as custom in the report."""
        def wrap(r):
            out = fn(r)
            if isinstance(out, tuple):
                return out
            return (bool(out), "custom check")
        return self._add(f"[custom] {description}", wrap)

    # ---- the run ------------------------------------------------------------
    def check(self, *, functional_only: bool = False) -> Report:
        """Seal the claims, run the story once, and return the verdicts."""
        self._checked = True
        r = self.story._result(functional_only=functional_only)
        verdicts = []
        for desc, fn in self._claims:
            try:
                ok, ev = fn(r)
            except Exception as ex:            # a claim that errors is falsified
                ok, ev = False, f"check raised {type(ex).__name__}: {ex}"
            verdicts.append(Verdict(claim=desc, ok=ok, evidence=ev))
        return Report(verdicts=verdicts,
                      accommodations=list(self.story._accommodations))
