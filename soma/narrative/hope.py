"""
hope.py -- Snyder's hope theory: will, ways, and the sea that says no.

Grounded in:

  * Snyder (1994, 2000, 2002): hope is a COGNITIVE structure, not a mood --
    goal-directed AGENCY (the will: the sustained sense that one can act and
    keep acting) times PATHWAYS (the ways: the capacity to generate routes,
    and new routes when a route is blocked). High-hope people are not the ones
    who never hit walls; they are the ones who reroute at walls.
  * Snyder (2002): agency is what channels the energy to *produce alternate
    pathways* at a blockage -- the two components are coupled, and both are
    necessary. Emotions are the OUTPUT of goal pursuit: progress feels like
    energy, blockage without a route feels like despair.
  * Ritschel & Sheppard (2017); the meta-analytic literature: goal blockage is
    the depression trigger, and hope's components buffer it -- which couples
    this layer to the learned-helplessness and network layers.
  * The reinforcement loop (Snyder; the intervention literature): each
    obstacle actually overcome feeds agency -- high-hope people carry "a
    richer catalog of their own past effectiveness."

The model is a small explicit goal-pursuit simulation (like the k-ToM minds
of 0.21): a voyage toward a far goal through a sequence of blockages. At each
blockage the traveler either finds a new route (probability set by pathways,
searched with energy set by agency) or stalls; stalling drains agency (the
helplessness coupling), overcoming feeds it (the catalog). The layer's
predictions are the surface of that machine:

  * voyage(agency, pathways, blockages=, seed=)   -- one crossing, traced
  * hope_surface(blockages=)                      -- who reaches the far shore
  * the dyad theorem: an agent with will but no ways fails by exhaustion; an
    agent with ways but no will fails by never leaving; two people who pool
    one's will and the other's ways cross as a single high-hope agent.

`hopes(char, goal, agency=, pathways=)` wires the same structure into a
character body for sift/prose integration.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import random as _random
from typing import Optional

from .story import Story, Character


# ---------------------------------------------------------------------------
# the machine
# ---------------------------------------------------------------------------

@dataclass
class Voyage:
    who: str
    agency0: float
    pathways: float
    reached: bool
    beats: int
    blockages_met: int
    blockages_passed: int
    agency_final: float
    trace: list                    # (beat, event) strings
    progress: list                 # progress per beat, for sparklines

    def render(self) -> str:
        from soma.viz import sparkline
        head = (f"VOYAGE — {self.who} (agency {self.agency0:.2f}, pathways "
                f"{self.pathways:.2f}): "
                + (f"REACHED in {self.beats} beats"
                   if self.reached else f"turned back at beat {self.beats}"))
        line = f"  progress {sparkline(self.progress, 40)}"
        tail = (f"  blockages passed {self.blockages_passed}/"
                f"{self.blockages_met}; agency {self.agency0:.2f} -> "
                f"{self.agency_final:.2f}"
                + (" (the catalog of past effectiveness, growing)"
                   if self.agency_final > self.agency0 + 0.05 else ""))
        return "\n".join([head, line, tail] +
                         [f"    {t}" for t in self.trace[:10]])


def voyage(agency: float, pathways: float, *, who: str = "traveler",
           blockages: int = 7, goal: float = 100.0, seed: int = 0,
           max_beats: int = 200, despair_limit: float = 9.0) -> Voyage:
    """One crossing. Progress advances by `8 * agency` per open beat. A
    blockage waits every `goal/blockages` of the way. At a blockage, each
    beat the traveler searches for a route: P(found) = pathways * (0.25 +
    0.75 * agency) -- the will channels the search (Snyder, 2002). While
    stalled, despair accumulates and agency erodes (the helplessness
    coupling: goal blockage is the trigger); if despair passes the limit the
    voyage is abandoned. Each blockage OVERCOME feeds agency by +0.06 (the
    catalog of past effectiveness). Deterministic per seed."""
    rng = _random.Random(seed)
    a = agency
    prog, despair = 0.0, 0.0
    gates = [goal * (i + 1) / (blockages + 1) for i in range(blockages)]
    next_gate = 0
    trace, progress = [], []
    met = passed = 0
    stalled = False
    for beat in range(1, max_beats + 1):
        if stalled:
            p_found = pathways * (0.25 + 0.75 * a)
            if rng.random() < p_found:
                stalled = False
                passed += 1
                a = min(1.0, a + 0.06)
                despair = max(0.0, despair - 3.0)
                trace.append(f"beat {beat}: a way through -- agency fed "
                             f"({a:.2f})")
            else:
                despair += 0.9
                a = max(0.05, a - 0.03)
                if despair >= despair_limit:
                    trace.append(f"beat {beat}: no way seen, and no will left "
                                 f"to look")
                    progress.append(prog)
                    return Voyage(who=who, agency0=agency, pathways=pathways,
                                  reached=False, beats=beat,
                                  blockages_met=met, blockages_passed=passed,
                                  agency_final=round(a, 2), trace=trace,
                                  progress=progress)
        else:
            prog += 8.0 * a
            if next_gate < len(gates) and prog >= gates[next_gate]:
                prog = gates[next_gate]
                next_gate += 1
                met += 1
                stalled = True
                trace.append(f"beat {beat}: the sea says no ({met} of "
                             f"{blockages})")
            if prog >= goal:
                progress.append(prog)
                trace.append(f"beat {beat}: the far shore")
                return Voyage(who=who, agency0=agency, pathways=pathways,
                              reached=True, beats=beat, blockages_met=met,
                              blockages_passed=passed,
                              agency_final=round(a, 2), trace=trace,
                              progress=progress)
        progress.append(prog)
    return Voyage(who=who, agency0=agency, pathways=pathways, reached=False,
                  beats=max_beats, blockages_met=met, blockages_passed=passed,
                  agency_final=round(a, 2), trace=trace, progress=progress)


# ---------------------------------------------------------------------------
# the surface: who reaches the far shore
# ---------------------------------------------------------------------------

@dataclass
class HopeSurface:
    grid: dict                     # (agency, pathways) -> reach fraction
    levels: tuple
    blockages: int

    def render(self) -> str:
        out = [f"THE HOPE SURFACE — share of crossings that reach the far "
               f"shore ({self.blockages} blockages)",
               "  (rows: agency, the will; columns: pathways, the ways)"]
        header = "            " + "  ".join(f"p={p:.1f}" for p in self.levels)
        out.append(header)
        for a in reversed(self.levels):
            cells = []
            for p in self.levels:
                v = self.grid[(a, p)]
                mark = ("#" if v >= 0.8 else "+" if v >= 0.4
                        else "·" if v > 0.05 else " ")
                cells.append(f"{v:4.0%}{mark}")
            out.append(f"  agency {a:.1f}: " + "  ".join(cells))
        out.append("  Will without ways exhausts; ways without will never "
                   "leave the harbor.\n  Hope is the product, not the sum.")
        return "\n".join(out)


def hope_surface(*, levels=(0.2, 0.5, 0.8), blockages: int = 7,
                 samples: int = 20, seed: int = 0) -> HopeSurface:
    """Sweep the (agency, pathways) plane; each cell is the fraction of
    seeded crossings that reach the far shore. Snyder's multiplicative claim,
    drawn as a surface."""
    grid = {}
    for a in levels:
        for p in levels:
            n = sum(1 for s in range(samples)
                    if voyage(a, p, blockages=blockages,
                              seed=seed * 1000 + s * 17).reached)
            grid[(a, p)] = n / samples
    return HopeSurface(grid=grid, levels=tuple(levels), blockages=blockages)


# ---------------------------------------------------------------------------
# the dyad: two half-hopes pooling into one
# ---------------------------------------------------------------------------

@dataclass
class DyadReport:
    alone_a: float                 # reach share, the agent of will
    alone_p: float                 # reach share, the agent of ways
    together: float

    def render(self) -> str:
        from soma.viz import bar
        return ("THE DYAD — two half-hopes, alone and pooled\n"
                f"  will without ways   (0.9, 0.2): "
                f"{bar(self.alone_a, 14)} {self.alone_a:.0%} reach\n"
                f"  ways without will   (0.2, 0.9): "
                f"{bar(self.alone_p, 14)} {self.alone_p:.0%} reach\n"
                f"  pooled as one agent (0.9, 0.9): "
                f"{bar(self.together, 14)} {self.together:.0%} reach\n"
                "  Will without ways shatters at the walls; ways without "
                "will drifts while the\n  stores run out. Two people who "
                "trust each other's missing half cross as one\n  high-hope "
                "agent -- a mechanical account of why some pairs survive what "
                "neither\n  person would.")


def dyad(*, blockages: int = 7, samples: int = 20, seed: int = 3,
         stores: int = 90) -> DyadReport:
    """`stores` is the clock: a real crossing cannot take forever. Under it,
    the two half-hopes fail differently -- will without ways shatters at the
    walls (despair at the blockages); ways without will drifts, and the
    stores run out under a traveler who cannot keep the pace."""
    def share(a, p):
        return sum(1 for s in range(samples)
                   if voyage(a, p, blockages=blockages, max_beats=stores,
                             seed=seed * 1000 + s * 17).reached) / samples
    return DyadReport(alone_a=share(0.9, 0.2), alone_p=share(0.2, 0.9),
                      together=share(0.9, 0.9))


# ---------------------------------------------------------------------------
# wiring hope into a character
# ---------------------------------------------------------------------------

def hopes(char: Character, goal: str, *, agency: float,
          pathways: float) -> dict:
    """Wire the hope structure into a character body: a `blockage` channel,
    and the two responses Snyder's theory predicts -- resolve (rerouting) if
    pathways are high, despair if they are not. Returns the derived dials so
    a study can read them back."""
    for name, v in (("agency", agency), ("pathways", pathways)):
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"{name} must be in [0, 1], got {v}")
    char.has_body_signal("resolve", baseline=40.0)
    char.has_body_signal("despair", baseline=10.0)
    char.senses("blockage", baseline=0.0)
    # high pathways: a wall is a cue to search -- resolve rises with the will
    char.appraises("blockage", when="blockage > 4", drives="resolve",
                   to=round(40.0 + 55.0 * pathways * agency, 1),
                   fades_to=40.0, precision=0.9, conviction=0.2,
                   feeling="resolve")
    # low pathways: the same wall is an ending -- despair scales inversely
    char.appraises("blockage", when="blockage > 4", drives="despair",
                   to=round(10.0 + 70.0 * (1.0 - pathways) * (1.0 - 0.5 * agency), 1),
                   fades_to=10.0, precision=0.9, conviction=0.2)
    return {"who": char.name, "goal": goal, "agency": agency,
            "pathways": pathways}
