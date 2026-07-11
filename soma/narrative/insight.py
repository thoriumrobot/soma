"""
soma.narrative.insight -- the shared substrate for predictive-characterization
studies.

The prediction layer (schema, appraisal, attachment, circumplex, preregister)
makes single forecasts: given this character, what happens. This module is the
floor under the *study* layer -- sensitivity, discrimination, early warning,
counterfactual -- whose job is not to make one prediction but to ask which
predictions are load-bearing:

  * which parameter actually moves the outcome (sensitivity),
  * what probe would tell two readings of a character apart (discrimination),
  * whether a coming break is already legible in the run before it happens
    (early warning),
  * and what smallest change would have turned the ending (counterfactual).

All four need the same two primitives, kept here so they share one definition:

  run_with(story, overrides)   compile the story, apply zero or more
                               `loop.field=value` dials (the same grammar as
                               `perturb`), run once, return the Result.

  outcomes(result)             read a fixed vocabulary of scalar outcomes off a
                               Result -- did a lie break and when, peak and
                               final arousal, mood drift, confabulation gap,
                               feeling counts -- so a study can name an outcome
                               by string and get a number back.

Keeping the outcome vocabulary in one place is what lets a sensitivity study and
a counterfactual study talk about "the same ending": they resolve the outcome
name through this module, not through ad hoc chronicle-walking at each call site.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Optional


# ---------------------------------------------------------------------------
# running a story with parameter overrides
# ---------------------------------------------------------------------------

def run_with(story, overrides: Optional[dict] = None):
    """Compile `story`, apply each override (`"loop.field": value`, or the string
    form `"loop.field=value"`), and run once. Returns a soma Result.

    Overrides use the perturb grammar, so anything perturb can move -- a loop's
    precision/conviction/learn/overwhelm/mode, a workspace threshold, an
    attention capacity, a memory strength, an allostat setpoint, a couple's
    gain/lag -- can be swept or counterfactualized here.

    Implementation mirrors soma.perturb exactly: parse to an AST, mutate it in
    place with apply_set, and interpret the mutated program directly (no
    round-trip back to source, which not every node needs to support)."""
    from soma.parser import parse
    from soma.perturb import apply_set
    from soma.interpreter import Interpreter

    prog = parse(story.source(), title=story.title)
    applied = []
    if overrides:
        for key, val in overrides.items():
            spec = key if "=" in str(key) else f"{key}={val}"
            applied.append(apply_set(prog, spec))
    result = Interpreter(prog).run()
    result._overrides_applied = applied
    return result


# ---------------------------------------------------------------------------
# reading outcomes off a run
# ---------------------------------------------------------------------------

def _owner_match(who: str, character: Optional[str], multi: bool) -> bool:
    if character is None or not multi:
        return True
    return who.split(".")[0] == character


def outcome(result, name: str, *, character: Optional[str] = None,
            channel: str = "heart", mood: Optional[str] = None,
            quale: Optional[str] = None) -> float:
    """Read one scalar outcome off a Result. Names:

      "break"        1.0 if a revelation was logged, else 0.0
      "break_time"   time of first revelation, or +inf if none (so "earlier
                     break" is "smaller number" and no-break sorts last)
      "peak"         max of `channel`
      "final"        mean of the last 3 samples of `channel`
      "arousal"      peak minus the channel's own first sample (spike size)
      "mood_drift"   end-minus-start of `mood` (needs mood=...)
      "gap"          largest narrate confabulation gap
      "feel"         count of emits of `quale` (needs quale=...)
      "settle_ratio" recovery fraction of `channel` after its peak (0..1)
      "perceive_frac" fraction of the character's settle beats routed to
                     `perceive` -- how often the world still gets in. The
                     arbitration signature of openness vs. armor, and often a
                     truer vital sign than any feeling count, since a loop can
                     go on emitting while it has stopped letting anything move
                     it.
    """
    multi = any("." in k for k in result.channel_hist)

    def ch(cn):
        if character and multi:
            return result.channel_hist.get(f"{character}.{cn}", [])
        return (result.channel_hist.get(cn)
                or result.channel_hist.get(f"{result_first_owner(result)}.{cn}", []))

    if name == "break":
        return 1.0 if any(e.kind == "revelation"
                          and _owner_match(e.who, character, multi)
                          for e in result.chronicle) else 0.0
    if name == "break_time":
        ts = [e.t for e in result.chronicle if e.kind == "revelation"
              and _owner_match(e.who, character, multi)]
        return min(ts) if ts else float("inf")
    if name in ("peak", "final", "arousal", "settle_ratio"):
        h = ch(channel)
        if not h:
            return 0.0
        if name == "peak":
            return max(h)
        if name == "final":
            return sum(h[-3:]) / min(3, len(h))
        if name == "arousal":
            return max(h) - h[0]
        # settle_ratio
        peak = max(h)
        base = h[0]
        final = sum(h[-3:]) / min(3, len(h))
        return (peak - final) / (peak - base) if peak > base else 1.0
    if name == "mood_drift":
        assert mood, "outcome('mood_drift') needs mood=..."
        key = (f"{character}_{mood}" if character else None)
        h = (result.mood_hist.get(key)
             or result.mood_hist.get(mood)
             or next((v for k, v in result.mood_hist.items()
                      if k.endswith(f"_{mood}")), []))
        if len(h) < 2:
            return 0.0
        return (sum(h[-3:]) / min(3, len(h))) - h[0]
    if name == "perceive_frac":
        routes = [e.detail.get("route") for e in result.chronicle
                  if e.kind == "settle"
                  and _owner_match(e.who, character, multi)]
        return (routes.count("perceive") / len(routes)) if routes else 0.0
    if name == "gap":
        gaps = [e.detail.get("gap", 0) for e in result.chronicle
                if e.kind == "narrate" and _owner_match(e.who, character, multi)]
        return max(gaps) if gaps else 0.0
    if name == "feel":
        assert quale, "outcome('feel') needs quale=..."
        return float(sum(1 for e in result.chronicle if e.kind == "emit"
                         and quale in str(e.detail.get("quale", ""))
                         and _owner_match(e.who, character, multi)))
    raise ValueError(f"unknown outcome {name!r}")


def result_first_owner(result):
    for k in result.channel_hist:
        if "." in k:
            return k.split(".")[0]
    return ""


def series(result, channel: str, *, character: Optional[str] = None):
    """The time series of a channel, for early-warning analysis."""
    multi = any("." in k for k in result.channel_hist)
    if character and multi:
        return list(result.channel_hist.get(f"{character}.{channel}", []))
    return list(result.channel_hist.get(channel)
                or result.channel_hist.get(
                    f"{result_first_owner(result)}.{channel}", []))


def debt_series(result, *, character: Optional[str] = None,
                loop_contains: str = ""):
    """The overwhelm-debt trajectory of a suppressing loop: the accumulating
    disconfirming surprise the lie is holding down, read from its `settle`
    events. This is the destabilizing variable in the strict sense -- the break
    fires exactly when it crosses the loop's threshold -- so it is the correct
    place to look for critical slowing down: as the debt approaches threshold,
    the loop's grip weakens and it takes longer to relax the debt back down
    after each new piece of evidence. Returns (times, debts)."""
    multi = any("." in k for k in result.channel_hist)
    pts = []
    for e in result.chronicle:
        if e.kind != "settle":
            continue
        if character and multi and e.who.split(".")[0] != character:
            continue
        if loop_contains and loop_contains not in e.who:
            continue
        d = e.detail.get("debt")
        if d is not None:
            pts.append((e.t, d))
    pts.sort()
    return [t for t, _ in pts], [v for _, v in pts]


def error_series(result, *, character: Optional[str] = None,
                 loop_contains: str = ""):
    """The prediction-error trajectory of a suppressing loop, read from its
    `settle` events. This is the signal that carries a lie's approach to
    breaking: a high-conviction loop routes to `act` (suppress) while the
    unattended error accumulates, and it is in that accumulating,
    increasingly-hard-to-hold error that critical slowing down appears -- the
    system takes longer to relax back after each new piece of evidence. Returns
    (times, errors)."""
    multi = any("." in k for k in result.channel_hist)
    pts = []
    for e in result.chronicle:
        if e.kind != "settle":
            continue
        if character and multi and e.who.split(".")[0] != character:
            continue
        if loop_contains and loop_contains not in e.who:
            continue
        err = e.detail.get("error")
        if err is not None:
            pts.append((e.t, abs(err)))
    pts.sort()
    return [t for t, _ in pts], [v for _, v in pts]
