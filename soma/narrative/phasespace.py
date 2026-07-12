"""
soma.narrative.phasespace -- the marriage as a dynamical system: attractors,
basins, the separatrix, the smallest repair, and the road back.

`soma.narrative.gottman` rebuilt the famous typology and the thin-slice
forecast. This module rebuilds the part of Gottman & Murray's *The Mathematics
of Marriage* (2002) that makes counterfactuals about a relationship COMPUTABLE
rather than asserted -- the dynamical-systems core: phase space, influence
functions, null clines, uninfluenced and influenced STABLE STEADY STATES
(attractors), basins of attraction separated by a SEPARATRIX, repair and
damping terms, and the catastrophe-theoretic reading under which falling and
recovering are not symmetric.

The model is the book's coupled difference equations. Each partner's next
affect is their uninfluenced pull home plus their partner's influence:

    A(t+1) = (1-r_A)*s_A + r_A*A(t) + I_A(B(t)) + repair_A(B(t)) - damp_A(B(t))

where s is the UNINFLUENCED STEADY STATE (where this person's affect settles
alone), r is EMOTIONAL INERTIA (carryover), and I is the bilinear INFLUENCE
FUNCTION with a NEGATIVE THRESHOLD: positivity influences in proportion, but
negativity has no bite until it sinks past the threshold -- the dial Gottman
found closer to zero (thinner-skinned) in couples headed for divorce. REPAIR
is a bid that switches on when the partner's affect drops below the repair
threshold; DAMPING trims runaway positivity.

What the geometry buys the novelist -- each of these is a *prediction about the
couple*, none of it typed in:

  attractors(dyad)        where this marriage CAN end. One positive attractor
                          is a marriage; one negative attractor is a divorce
                          in progress; BOTH AT ONCE (bistability) is the
                          marriage that could have held -- the good ending
                          exists in their phase space whether or not they
                          reach it.

  basins(dyad)            which evenings end warm: the share of starting
                          states that flow to the positive attractor, and the
                          basin map with the separatrix between the futures.
                          The same couple, two openings, two endings -- and
                          the boundary between them has coordinates.

  minimal_repair(...)     the smallest repair term that carries a given
                          opening to the positive attractor: THE MARRIAGE
                          THAT COULD HAVE HELD, derived. Verified both sides
                          of the boundary (just-below must fail, just-above
                          must hold) so the claim is falsified by simulation
                          if the bisection lied.

  hysteresis(...)         the catastrophe-theory reading: sweep stress up
                          until the couple falls, sweep it back down, and the
                          recovery point is NOT the fall point. The road back
                          is longer than the road down; some marriages do not
                          mend when the hard year ends, but only under active
                          support past neutral -- and the model says how much.

  stress_season(...)      Karney & Bradbury's Vulnerability-Stress-Adaptation
                          model (1995) run through the geometry: external
                          stress pulls each partner's uninfluenced steady
                          state down in proportion to their enduring
                          VULNERABILITY; whether the couple returns when the
                          stress passes depends on whether the season pushed
                          them across the separatrix -- adaptation (repair) is
                          the buffer. Same storm, two couples, one scar.

  install_couple(...)     the falsification bridge: compile the dyad into two
                          real SOMA characters (manner surfaces, couple
                          reads, guarded appraisals, repair bids -- the same
                          verbs `gottman.marry` uses) so the phase-space
                          claim must reproduce in the Chronicle: a bistable
                          dyad's warm and cold openings must end far apart in
                          the run; a monostable dyad's must reconverge.
                          `confirm_bistability` stages exactly that.

Affect is on Gottman's positive/negative scale, here [-5, +5] with 0 neutral
(clamped at +/-8 so a runaway cascade saturates rather than diverges -- the
pit has a floor). The SOMA bridge maps affect a to the 0..10 `manner` surface
as m = a + 5.

Honesty note: parameters are authorial dials, not fitted SPAFF weights; what
is inherited from the research is the STRUCTURE (which dials exist and how
they couple) and the qualitative predictions the structure licenses --
bistability, basin boundaries, repair thresholds, hysteresis -- each of which
is checked by simulation inside the module rather than asserted.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
import math

CLAMP = 8.0
_BLOCKS = "▁▂▃▄▅▆▇█"


def _sig(x):
    return 1.0 / (1.0 + math.exp(-x))


def _spark(xs, lo=None, hi=None):
    if not xs:
        return ""
    lo = min(xs) if lo is None else lo
    hi = max(xs) if hi is None else hi
    span = max(hi - lo, 1e-9)
    return "".join(_BLOCKS[min(7, int((x - lo) / span * 8))] for x in xs)


# ---------------------------------------------------------------------------
# the dyad: two people's dials, coupled
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Partner:
    """One person's dials, in the book's vocabulary."""
    setpoint: float = 1.0        # uninfluenced steady state (alone, they settle here)
    inertia: float = 0.5         # emotional carryover r in [0, 1)
    pos_slope: float = 0.2       # influence of the partner's positivity on me
    neg_slope: float = 0.9       # influence of the partner's negativity past...
    neg_threshold: float = -0.5  # ...this level (<= 0). CLOSER TO ZERO = thinner
                                 # skin: smaller negativity triggers -- the
                                 # divorcing couples' signature
    repair: float = 0.0          # strength of the repair bid
    repair_at: float = -1.0      # partner affect below which the bid fires
    damping: float = 0.0         # trims runaway positivity...
    damp_at: float = 4.0         # ...past this level
    vulnerability: float = 1.0   # VSA: how much external stress pulls my
                                 # setpoint down (an enduring vulnerability)


@dataclass(frozen=True)
class Dyad:
    a: Partner
    b: Partner
    name_a: str = "A"
    name_b: str = "B"

    def with_repair(self, strength: float) -> "Dyad":
        return Dyad(replace(self.a, repair=strength),
                    replace(self.b, repair=strength),
                    self.name_a, self.name_b)

    def under_stress(self, e: float) -> "Dyad":
        """VSA spillover: external stress e pulls each setpoint down by
        vulnerability * e (negative e is active support past neutral)."""
        return Dyad(replace(self.a, setpoint=self.a.setpoint - self.a.vulnerability * e),
                    replace(self.b, setpoint=self.b.setpoint - self.b.vulnerability * e),
                    self.name_a, self.name_b)


def _influence(x: float, p: Partner) -> float:
    pos = p.pos_slope * max(0.0, x)
    neg = p.neg_slope * min(0.0, x - p.neg_threshold)
    return pos + neg


def step(dyad: Dyad, state):
    """One beat of the coupled difference equations."""
    A, B = state
    pa, pb = dyad.a, dyad.b
    A2 = ((1 - pa.inertia) * pa.setpoint + pa.inertia * A
          + _influence(B, pa)
          + pa.repair * _sig(2.0 * (pa.repair_at - B))
          - pa.damping * _sig(2.0 * (B - pa.damp_at)))
    B2 = ((1 - pb.inertia) * pb.setpoint + pb.inertia * B
          + _influence(A, pb)
          + pb.repair * _sig(2.0 * (pb.repair_at - A))
          - pb.damping * _sig(2.0 * (A - pb.damp_at)))
    cl = lambda v: max(-CLAMP, min(CLAMP, v))
    return (cl(A2), cl(B2))


def trajectory(dyad: Dyad, start, steps: int = 120):
    xs = [tuple(start)]
    for _ in range(steps):
        xs.append(step(dyad, xs[-1]))
    return xs


# ---------------------------------------------------------------------------
# attractors and basins
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Attractor:
    point: tuple            # (A, B) at rest
    kind: str               # "point" | "cycle"
    valence: str            # "positive" | "negative" | "mixed"

    def render(self) -> str:
        return (f"{self.valence} {self.kind} at "
                f"({self.point[0]:+.2f}, {self.point[1]:+.2f})")


def _settle(dyad, start, steps=300, tail=8, tol=1e-3):
    xs = trajectory(dyad, start, steps)
    end = xs[-tail:]
    ma = sum(p[0] for p in end) / tail
    mb = sum(p[1] for p in end) / tail
    wobble = max(max(abs(p[0] - ma), abs(p[1] - mb)) for p in end)
    return (ma, mb), ("point" if wobble < tol else "cycle")


def _valence(pt) -> str:
    s = pt[0] + pt[1]
    if s > 0.4:
        return "positive"
    if s < -0.4:
        return "negative"
    return "mixed"


def attractors(dyad: Dyad, *, grid_n: int = 7, lo: float = -5.0,
               hi: float = 5.0, merge: float = 0.35):
    """Where the marriage can end: settle a grid of openings and cluster the
    resting places. Two attractors of opposite valence = bistability = the
    marriage that could have held exists in this couple's phase space."""
    found = []
    for i in range(grid_n):
        for j in range(grid_n):
            s = (lo + (hi - lo) * i / (grid_n - 1),
                 lo + (hi - lo) * j / (grid_n - 1))
            pt, kind = _settle(dyad, s)
            for att in found:
                if (abs(att.point[0] - pt[0]) < merge
                        and abs(att.point[1] - pt[1]) < merge):
                    break
            else:
                found.append(Attractor(point=(round(pt[0], 2), round(pt[1], 2)),
                                       kind=kind, valence=_valence(pt)))
    return sorted(found, key=lambda a: -(a.point[0] + a.point[1]))


def bistable(dyad: Dyad, **kw) -> bool:
    vals = {a.valence for a in attractors(dyad, **kw)}
    return "positive" in vals and "negative" in vals


def reaches(dyad: Dyad, start, *, steps: int = 300) -> Attractor:
    """Which future a given opening flows to -- the separatrix question,
    answered for one evening."""
    pt, kind = _settle(dyad, start, steps=steps)
    return Attractor(point=(round(pt[0], 2), round(pt[1], 2)),
                     kind=kind, valence=_valence(pt))


@dataclass
class BasinMap:
    dyad: Dyad
    attractors: list
    grid: list               # grid[i][j] -> attractor index (row = B desc)
    lo: float
    hi: float

    @property
    def share_positive(self) -> float:
        """The fraction of openings that end warm -- how much of the space of
        possible evenings this marriage turns good."""
        pos = {k for k, a in enumerate(self.attractors) if a.valence == "positive"}
        cells = [c for row in self.grid for c in row]
        return sum(1 for c in cells if c in pos) / max(1, len(cells))

    def render(self) -> str:
        marks = "#+~-." * 4
        lines = [f"BASINS -- {self.dyad.name_a} x {self.dyad.name_b} "
                 f"(axes {self.lo:+.0f}..{self.hi:+.0f}; "
                 f"{self.share_positive:.0%} of openings end warm)"]
        for row in self.grid:
            lines.append("  " + "".join(marks[c] for c in row))
        for k, a in enumerate(self.attractors):
            lines.append(f"  {marks[k]} = {a.render()}")
        return "\n".join(lines)


def basins(dyad: Dyad, *, res: int = 17, lo: float = -5.0,
           hi: float = 5.0) -> BasinMap:
    """The basin map: every opening on a grid, labelled by the attractor it
    flows to. The boundary between labels is the separatrix -- the line
    between the marriage and the divorce, with coordinates."""
    atts = attractors(dyad, lo=lo, hi=hi)
    grid = []
    for j in range(res - 1, -1, -1):          # B from high to low (map-like)
        row = []
        B0 = lo + (hi - lo) * j / (res - 1)
        for i in range(res):
            A0 = lo + (hi - lo) * i / (res - 1)
            pt, _ = _settle(dyad, (A0, B0), steps=220)
            best, bd = 0, float("inf")
            for k, a in enumerate(atts):
                d = abs(a.point[0] - pt[0]) + abs(a.point[1] - pt[1])
                if d < bd:
                    best, bd = k, d
            row.append(best)
        grid.append(row)
    return BasinMap(dyad=dyad, attractors=atts, grid=grid, lo=lo, hi=hi)


# ---------------------------------------------------------------------------
# the smallest repair -- the marriage that could have held, derived
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MinimalRepair:
    start: tuple
    strength: float          # least repair that carries the start to warmth
    exists: bool             # False if even `hi` repair cannot
    just_below: str          # valence reached at strength - margin (must fail)
    just_above: str          # valence reached at strength + margin (must hold)

    @property
    def verified(self) -> bool:
        return (not self.exists) or (self.just_below != "positive"
                                     and self.just_above == "positive")

    def render(self) -> str:
        if not self.exists:
            return (f"no repair in range rescues the opening "
                    f"({self.start[0]:+.1f}, {self.start[1]:+.1f})")
        return (f"minimal repair from ({self.start[0]:+.1f}, {self.start[1]:+.1f}): "
                f"{self.strength:.3f}  [just below -> {self.just_below}; "
                f"just above -> {self.just_above}; "
                f"{'VERIFIED' if self.verified else 'FALSIFIED'}]")


def minimal_repair(dyad: Dyad, start, *, lo: float = 0.0, hi: float = 6.0,
                   iters: int = 28, margin: float = 0.05) -> MinimalRepair:
    """Bisect the repair strength for the least bid that carries `start` to
    the positive attractor -- then verify BOTH SIDES by simulation, so the
    number is a falsifiable claim, not a search artifact."""
    def warm(strength):
        return reaches(dyad.with_repair(strength), start).valence == "positive"
    if warm(lo):
        return MinimalRepair(start=tuple(start), strength=lo, exists=True,
                             just_below="positive", just_above="positive")
    if not warm(hi):
        return MinimalRepair(start=tuple(start), strength=hi, exists=False,
                             just_below="", just_above="")
    a, b = lo, hi
    for _ in range(iters):
        m = 0.5 * (a + b)
        if warm(m):
            b = m
        else:
            a = m
    s = round(b, 3)
    below = reaches(dyad.with_repair(max(lo, s - margin)), start).valence
    above = reaches(dyad.with_repair(s + margin), start).valence
    return MinimalRepair(start=tuple(start), strength=s, exists=True,
                         just_below=below, just_above=above)


# ---------------------------------------------------------------------------
# hysteresis -- the road back is longer than the road down
# ---------------------------------------------------------------------------

@dataclass
class HysteresisReport:
    fall_at: float           # stress level at which the couple first falls
    recover_at: float        # stress level (down-sweep) at which they return;
                             # may be NEGATIVE: recovery needs support past
                             # neutral, not merely the stress ending
    gap: float               # fall_at - recover_at: the asymmetry itself
    up_states: list          # mutual affect along the up-sweep
    down_states: list        # mutual affect along the down-sweep
    scarred_at_zero: bool    # still in the pit when the stress is back to 0

    def render(self) -> str:
        lines = [f"HYSTERESIS -- fall at stress {self.fall_at:+.2f}; "
                 f"recovery at {self.recover_at:+.2f}; gap {self.gap:.2f}"]
        lines.append(f"  up   {_spark(self.up_states)}")
        lines.append(f"  down {_spark(self.down_states)}")
        if self.scarred_at_zero:
            lines.append("  when the stress returns to zero they are STILL in "
                         "the pit: the hard year ending is not enough.")
        if self.recover_at < 0:
            lines.append(f"  the model's claim: they mend only under active "
                         f"support past neutral ({self.recover_at:+.2f}).")
        return "\n".join(lines)


def hysteresis(dyad: Dyad, *, lo: float = -3.0, hi: float = 4.0,
               steps: int = 57, settle_per: int = 40) -> HysteresisReport:
    """The catastrophe sweep. Raise external stress quasi-statically (the
    state carries over -- this is a life, not a restart), record where the
    couple falls; then lower it and record where they recover. In a bistable
    region the two differ: the fold. `recover_at` below zero is the model
    predicting that the end of the hard year will not, by itself, bring the
    marriage back."""
    es = [lo + (hi - lo) * k / (steps - 1) for k in range(steps)]
    state = _settle(dyad.under_stress(es[0]), (dyad.a.setpoint, dyad.b.setpoint))[0]
    up, fall_at = [], None
    for e in es:
        d = dyad.under_stress(e)
        for _ in range(settle_per):
            state = step(d, state)
        m = 0.5 * (state[0] + state[1])
        up.append(m)
        if fall_at is None and m < -0.4:
            fall_at = e
    down, recover_at = [], None
    for e in reversed(es):
        d = dyad.under_stress(e)
        for _ in range(settle_per):
            state = step(d, state)
        m = 0.5 * (state[0] + state[1])
        down.append(m)
        if recover_at is None and m > 0.4:
            recover_at = e
    fall_at = hi if fall_at is None else fall_at
    recover_at = lo if recover_at is None else recover_at
    at_zero_idx = min(range(len(es)), key=lambda k: abs(es[k]))
    scarred = down[len(es) - 1 - at_zero_idx] < -0.4
    return HysteresisReport(fall_at=round(fall_at, 2),
                            recover_at=round(recover_at, 2),
                            gap=round(fall_at - recover_at, 2),
                            up_states=up, down_states=down,
                            scarred_at_zero=scarred)


# ---------------------------------------------------------------------------
# the hard year -- VSA's stress season through the geometry
# ---------------------------------------------------------------------------

@dataclass
class StressSeasonReport:
    who: str
    mutual: list             # mutual affect per beat
    stress: list
    worst: float
    recovered: bool          # back in the positive attractor after the season
    scarred: bool            # started positive, ended negative -- crossed the
                             # separatrix and stayed
    beats_below: int

    def render(self) -> str:
        lines = [f"THE HARD YEAR -- {self.who}"]
        lines.append(f"  stress {_spark(self.stress)}")
        lines.append(f"  mutual {_spark(self.mutual)}   worst {self.worst:+.2f}, "
                     f"{self.beats_below} beats below the line")
        lines.append("  " + ("RECOVERED: the season passed and they came back."
                             if self.recovered else
                             "SCARRED: the stress ended; the marriage stayed "
                             "where the stress pushed it -- across the "
                             "separatrix."))
        return "\n".join(lines)


def stress_season(dyad: Dyad, schedule, *, start=None, tail: int = 60,
                  label: str = None) -> StressSeasonReport:
    """Run a stress schedule (a list of stress levels, one per beat) through
    the couple: each beat, every partner's setpoint is pulled down by their
    vulnerability times that beat's stress (Karney & Bradbury's spillover).
    After the schedule, `tail` stress-free beats decide the verdict: recovery
    or scar. Adaptation -- the repair dials -- is the buffer; vulnerability is
    the enduring amplifier; the separatrix decides."""
    state = tuple(start) if start else _settle(dyad, (dyad.a.setpoint,
                                                      dyad.b.setpoint))[0]
    started_positive = (state[0] + state[1]) > 0
    mutual, worst = [], 0.0
    for e in schedule:
        state = step(dyad.under_stress(e), state)
        m = 0.5 * (state[0] + state[1])
        mutual.append(m)
        worst = min(worst, m)
    for _ in range(tail):
        state = step(dyad, state)
        mutual.append(0.5 * (state[0] + state[1]))
    final = reaches(dyad, state, steps=120)
    recovered = final.valence == "positive"
    return StressSeasonReport(
        who=label or f"{dyad.name_a} & {dyad.name_b}",
        mutual=mutual, stress=list(schedule) + [0.0] * tail,
        worst=round(worst, 2), recovered=recovered,
        scarred=(started_positive and not recovered),
        beats_below=sum(1 for m in mutual if m < -0.4))


# ---------------------------------------------------------------------------
# the falsification bridge: the dyad as two SOMA characters
# ---------------------------------------------------------------------------

def install_couple(story, dyad: Dyad, *, lag: str = "1s"):
    """Compile the dyad into two real SOMA characters, with the same verbs
    `gottman.marry` uses: a proprioceptive `manner` surface at the mapped
    setpoint, `reads` couplings (surfaces only -- the other-minds rule),
    ease/friction appraisals whose guard IS the negative threshold, and a
    repair bid that fires when the partner's shown manner drops below the
    repair threshold. Affect a maps to manner m = a + 5.

    The point of the bridge is falsification: whatever the phase-space
    analysis claims (bistability, which opening ends where) must reproduce in
    the Chronicle of the compiled couple, or the analysis is only arithmetic."""
    from .temperament import guarded
    ca = story.character(dyad.name_a, temperament=guarded)
    cb = story.character(dyad.name_b, temperament=guarded)
    for ch, me, other in ((ca, dyad.a, dyad.b), (cb, dyad.b, dyad.a)):
        anchor = max(0.0, min(10.0, me.setpoint + 5.0))
        ch._add_sense("manner", "proprio", round(anchor, 1), "Expression")
    gain = max(0.35, min(1.0, 0.45 + 0.35 * (dyad.a.pos_slope + dyad.b.pos_slope)))
    ca.reads(cb, "manner", into="their_manner", gain=gain, lag=lag)
    cb.reads(ca, "manner", into="their_manner", gain=gain, lag=lag)
    for ch, me, other in ((ca, dyad.a, dyad.b), (cb, dyad.b, dyad.a)):
        anchor = max(0.0, min(10.0, me.setpoint + 5.0))
        other_anchor = max(0.0, min(10.0, other.setpoint + 5.0))
        sus = max(0.0, min(1.0, 1.0 - me.inertia))
        warm_resp = round(anchor + sus * (min(10.0, other_anchor + 1.5) - anchor), 1)
        cold_resp = round(anchor + sus * (max(0.0, other_anchor - 3.0) - anchor), 1)
        neg_guard = round(me.neg_threshold + 5.0, 2)
        ch.appraises("their_manner", when="their_manner >= 5.5",
                     feeling="ease", shows_on="manner",
                     shows_value=warm_resp, expects=5.0,
                     conviction=me.inertia)
        ch.appraises("their_manner", when=f"their_manner <= {neg_guard}",
                     as_threat=True, feeling="friction", shows_on="manner",
                     shows_value=cold_resp, drives="heart", to=100,
                     expects=5.0, conviction=me.inertia)
        if me.repair > 0:
            bid = round(min(10.0, anchor + min(3.5, me.repair)), 1)
            ch.appraises("their_manner",
                         when=f"their_manner <= {round(me.repair_at + 5.0, 2)}",
                         feeling="reaching_out", shows_on="manner",
                         shows_value=bid, expects=5.0)
        ch.has_mood("rapport", fed_by=["ease", "friction"])
    story._phasespace = dyad
    return ca, cb


def _final_manner(result, who) -> float:
    ys = result.channel_hist.get(f"{who}.manner") or result.channel_hist.get("manner")
    return sum(ys[-4:]) / 4 if ys else 5.0


def confirm_bistability(dyad: Dyad, *, beats: int = 16, shove: float = 4.0,
                        step_s: str = "1s"):
    """Stage the phase-space claim in the Chronicle: build the SAME couple
    twice, open one evening warm and one cold (a three-beat shove on each
    `their_manner` -- the world interrupting what the face was saying), run
    both, and read where the manners end.

    Returns {"warm_end", "cold_end", "gap", "diverged"}: for a bistable dyad
    the endings must lie far apart (two futures in one couple); for a
    monostable dyad they must reconverge. This is the module's own analysis,
    put at risk in the simulator."""
    from .story import Story
    ends = {}
    for opening, level in (("warm", 5.0 + shove), ("cold", 5.0 - shove)):
        s = Story(f"dyad_{opening}", span=f"{beats}s", step=step_s,
                  about="the weather of a marriage")
        ca, cb = install_couple(s, dyad)
        for t in (1, 2, 3):
            s.at(f"{t}s", ca.hears("their_manner", level),
                 cb.hears("their_manner", level))
        from .insight import run_with
        r = run_with(s)
        ends[opening] = 0.5 * (_final_manner(r, dyad.name_a)
                               + _final_manner(r, dyad.name_b))
    gap = round(ends["warm"] - ends["cold"], 2)
    return {"warm_end": round(ends["warm"], 2),
            "cold_end": round(ends["cold"], 2),
            "gap": gap, "diverged": gap > 1.5}
