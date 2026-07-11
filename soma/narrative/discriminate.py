"""
soma.narrative.discriminate -- the probe that tells two readings apart.

Two hypotheses about a character can fit everything the author has written so
far and still be different people underneath -- a man who yields because he is
warm, and a man who yields because he is afraid, behave identically until the
situation that separates them. The empirical question is: what situation is
that? In cognitive science this is model discrimination, and its modern answer
is adaptive design optimization -- rather than gathering more data of the same
kind, *design the single experiment* under which the competing models most
disagree, because the most informative design is the one that maximizes the
divergence of their predictions.

This module does that over SOMA characterizations. Given two versions of a
character (two parameterizations, or two whole builds) and a menu of candidate
probes -- stimuli the author could put to them -- it runs both characters on
each probe and scores how sharply their outcomes diverge. The probe with the
greatest divergence is the scene to write: the one place their two natures come
apart on the page. It is the constructive dual of the sensitivity study --
sensitivity asks which dial matters, discrimination asks which *situation*
reveals that it does.

    study = story.discriminate(
        who="Coat",
        version_a={"...conviction": 0.9},   # the proud reading
        version_b={"...conviction": 0.3},   # the yielding reading
        probes={"equal_regard": [3, 6, 9], "open_contempt": [3, 6, 9]},
        outcome="break_time")
    print(study.render())   # ranks probes by how far apart the two come
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .insight import run_with, outcome


@dataclass
class DiscriminationReport:
    who: str
    outcome_name: str
    rows: list                 # list[(probe_label, ya, yb, divergence)]
    best: tuple                # the winning (label, ya, yb, divergence)
    notes: list = field(default_factory=list)

    def render(self) -> str:
        lines = [f"DISCRIMINATION — the scene that separates two readings of "
                 f"{self.who} (outcome: {self.outcome_name}):"]
        lines.append("  probe                          reading A   reading B   apart")
        for label, ya, yb, div in self.rows:
            lines.append(f"  {label:<28s} {_fmt(ya):>9s}   {_fmt(yb):>9s}   "
                         f"{div:5.2f}")
        if self.best and self.best[3] > 1e-9:
            lines.append(f"  -> WRITE THIS SCENE: {self.best[0]} — the two "
                         f"natures come apart most here.")
        else:
            lines.append("  -> no probe in this menu separates the two readings; "
                         "on these outcomes they are the same person.")
        for n in self.notes:
            lines.append(f"  ({n})")
        return "\n".join(lines)


def _fmt(v):
    if v == float("inf"):
        return "never"
    return f"{v:.1f}"


def _divergence(ya, yb, spread):
    """Normalized absolute divergence of two outcomes. 'never' (inf) vs a finite
    time is maximal divergence (they qualitatively differ)."""
    if ya == float("inf") and yb == float("inf"):
        return 0.0
    if (ya == float("inf")) != (yb == float("inf")):
        return 1.0
    return min(1.0, abs(ya - yb) / spread) if spread > 1e-9 else 0.0


def discriminate(story, who, *, version_a: dict, version_b: dict,
                 probes: dict, outcome_name: str = "break_time",
                 beats: int = 8, character=None, channel="heart",
                 mood=None, quale=None):
    """Find the probe that maximizes the divergence between two readings.

    version_a / version_b : override dicts defining the two characterizations
    probes                : {channel: [values]} candidate stimuli to put to them
    outcome_name          : the outcome on which to measure divergence

    Runs both versions on each probe by temporarily injecting the stimulus (the
    same way Story.predict does) and reading the chosen outcome.
    """
    name = who if isinstance(who, str) else who.name
    character = character or name
    from soma.parser import parse
    from soma.perturb import apply_set
    from soma.interpreter import Interpreter

    multi = len(story.characters) > 1

    def run_version(overrides, probe_channel, probe_val):
        # build source, strip scripted stimuli, inject the single probe, apply
        # the version's parameter overrides, interpret.
        src = story.source()
        kept = [ln for ln in src.splitlines()
                if not ln.lstrip().startswith("stimulus ")]
        scoped = f"{name}.{probe_channel}" if multi else probe_channel
        body = "  ".join(f"at {i}s: {probe_val}" for i in range(1, beats + 1))
        probe_src = "\n".join(kept + ["", f"stimulus {scoped} {{ {body} }}"]) + "\n"
        prog = parse(probe_src, title=f"{story.title}__disc")
        for key, val in (overrides or {}).items():
            apply_set(prog, key if "=" in str(key) else f"{key}={val}")
        return Interpreter(prog).run()

    # first pass to find the outcome spread across everything, for normalization
    raw = []
    for pch, vals in probes.items():
        for v in vals:
            ra = run_version(version_a, pch, v)
            rb = run_version(version_b, pch, v)
            ya = outcome(ra, outcome_name, character=character, channel=channel,
                         mood=mood, quale=quale)
            yb = outcome(rb, outcome_name, character=character, channel=channel,
                         mood=mood, quale=quale)
            raw.append((f"{pch}={v}", ya, yb))
    finite = [y for _, ya, yb in raw for y in (ya, yb) if y != float("inf")]
    spread = (max(finite) - min(finite)) if len(finite) >= 2 else 1.0
    spread = spread or 1.0

    rows = [(label, ya, yb, _divergence(ya, yb, spread))
            for (label, ya, yb) in raw]
    rows.sort(key=lambda r: -r[3])
    best = rows[0] if rows else None
    notes = ["divergence 1.00 = the two readings differ qualitatively "
             "(one breaks, one never does) — the sharpest possible separation"]
    return DiscriminationReport(name, outcome_name, rows, best, notes)
