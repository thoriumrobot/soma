"""
soma.narrative.counterfactual -- the smallest change that would have saved her.

A novelist's deepest structural question about a character is counterfactual:
what would have had to be different for the ending to turn? Not *a* difference --
anyone can rewrite a life wholesale -- but the *smallest* one, because the
smallest sufficient change is the one that identifies what the ending actually
turned on. If a tragic non-break becomes a break when conviction drops by 0.05
but needs a wholesale rewrite to move any other way, then the tragedy was
conviction, at that margin, and nothing else.

This is counterfactual analysis in the interventionist sense (Woodward; Pearl's
do-operator): hold the world fixed, reach in and set one dial, and read the
downstream effect. SOMA's whole design makes this legible -- one dial, re-run,
attributable difference -- and this module automates the search for the minimal
intervention: over a set of candidate dials and a target outcome, it finds the
single smallest displacement from the character's actual value that flips the
outcome across a threshold (a lie that held now breaks; a break that came now
never does), and reports it as the load-bearing margin of the ending.

    study = story.minimal_intervention(
        target=("break", 1.0),           # we want the lie to break
        dials={"the_lie_...conviction": (0.0, 0.99),
               "the_lie_...overwhelm":  (1.0, 20.0)},
        character="Blade")
    print(study.render())   # the least change to any one dial that turns it
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .insight import run_with, outcome


@dataclass
class Intervention:
    dial: str
    baseline: float
    counterfactual: float
    distance: float            # |counterfactual - baseline|, absolute
    rel_distance: float        # normalized by the dial's own range
    outcome_before: float
    outcome_after: float

    def render_line(self) -> str:
        short = self.dial.split(".")[-2:] if "." in self.dial else [self.dial]
        short = ".".join(short)
        return (f"  {short}: {self.baseline:.3g} → {self.counterfactual:.3g} "
                f"(Δ {self.distance:.3g}, {self.rel_distance*100:.0f}% of range) "
                f"flips {self.outcome_before:.3g} → {self.outcome_after:.3g}")


@dataclass
class CounterfactualReport:
    target_name: str
    target_value: float
    character: str
    baseline_outcome: float
    already_met: bool
    interventions: list        # Intervention, sorted by rel_distance
    notes: list = field(default_factory=list)

    @property
    def minimal(self):
        return self.interventions[0] if self.interventions else None

    def render(self) -> str:
        lines = [f"MINIMAL INTERVENTION — least single change to make "
                 f"'{self.target_name}' reach {self.target_value:g}"
                 + (f" for {self.character}" if self.character else "") + ":"]
        if self.already_met:
            lines.append(f"  the ending already meets the target "
                         f"(baseline = {self.baseline_outcome:g}); nothing to flip.")
            return "\n".join(lines)
        if not self.interventions:
            lines.append("  NO single dial in the given set and range flips the "
                         "outcome — the ending is robust to every one of them "
                         "on its own. (This is itself an insight: the result is "
                         "over-determined, not balanced on a margin.)")
            for n in self.notes:
                lines.append(f"  ({n})")
            return "\n".join(lines)
        best = self.minimal
        lines.append(f"  THE MARGIN: this ending turns on one dial —")
        lines.append(best.render_line())
        if len(self.interventions) > 1:
            lines.append("  other single-dial routes, by increasing size:")
            for iv in self.interventions[1:]:
                lines.append(iv.render_line())
        for n in self.notes:
            lines.append(f"  ({n})")
        return "\n".join(lines)


def _meets(value, target_value, direction):
    if direction == "reach_high":
        return value >= target_value
    if direction == "reach_low":
        return value <= target_value
    return abs(value - target_value) < 1e-9


def minimal_intervention(story, *, target, dials: dict, character=None,
                         channel="heart", mood=None, quale=None,
                         steps: int = 24):
    """Find the smallest single-dial change that makes `target` hold.

    target : (outcome_name, target_value). For "break" use (\"break\", 1.0) to
             force a break or (\"break\", 0.0) to prevent one; for timing use
             e.g. (\"break_time\", 6.0) meaning \"break by 6s\".
    dials  : {dial_name: (lo, hi)} search range for each candidate dial.

    For each dial we sweep its range on a grid, holding all others at baseline,
    and record the value nearest the baseline that flips the outcome to meet the
    target. The dial with the smallest normalized displacement is the margin.
    """
    outcome_name, target_value = target
    # figure out the comparison direction from the outcome's semantics
    if outcome_name == "break_time":
        direction = "reach_low"        # "break by T" = time <= T
    elif outcome_name in ("break", "feel", "peak", "arousal", "gap"):
        direction = "reach_high" if target_value >= 0.5 else "reach_low"
    else:
        direction = "reach_high"

    base_r = run_with(story)
    base_out = outcome(base_r, outcome_name, character=character,
                       channel=channel, mood=mood, quale=quale)
    if _meets(base_out, target_value, direction):
        return CounterfactualReport(outcome_name, target_value, character or "",
                                    base_out, True, [])

    # read each dial's baseline value from the compiled program
    baselines = _read_baselines(story, dials)

    found = []
    for dial, (lo, hi) in dials.items():
        b = baselines.get(dial)
        if b is None:
            continue
        best_here = None
        for i in range(steps + 1):
            v = lo + (hi - lo) * i / steps
            r = run_with(story, {dial: v})
            y = outcome(r, outcome_name, character=character, channel=channel,
                        mood=mood, quale=quale)
            if _meets(y, target_value, direction):
                dist = abs(v - b)
                if best_here is None or dist < best_here.distance:
                    rng = (hi - lo) or 1.0
                    best_here = Intervention(
                        dial=dial, baseline=b, counterfactual=round(v, 4),
                        distance=round(dist, 4), rel_distance=dist / rng,
                        outcome_before=base_out, outcome_after=y)
        if best_here:
            found.append(best_here)

    found.sort(key=lambda iv: iv.rel_distance)
    notes = ["'smallest' is normalized to each dial's own range, so dials on "
             "different scales compare fairly"]
    return CounterfactualReport(outcome_name, target_value, character or "",
                                base_out, False, found, notes)


def _read_baselines(story, dials):
    """Read the current value of each dial from the compiled program, so the
    counterfactual distance is measured from the character as written."""
    from soma.parser import parse
    prog = parse(story.source(), title=story.title)
    out = {}
    for dial in dials:
        name, _, field = dial.rpartition(".")
        val = None
        for lp in prog.loops:
            if lp.name == name or lp.name.endswith("." + name):
                if field in ("conviction", "precision"):
                    pv = getattr(lp, field, None)
                    val = getattr(pv, "value", pv)
                elif field in ("learn", "overwhelm"):
                    val = getattr(lp, field, None)
        for coll, attr in ((prog.workspaces, "threshold"),
                           (prog.attentions, "capacity"),
                           (prog.memories, "strength"),
                           (prog.allostats, "setpoint")):
            if field == attr:
                for x in coll:
                    if x.name == name or x.name.endswith("." + name):
                        val = getattr(x, attr, None)
        if val is not None:
            out[dial] = float(val)
    return out
