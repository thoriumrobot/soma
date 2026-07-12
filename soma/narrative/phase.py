"""
soma.narrative.phase -- the shape of a relationship: attractors, basins,
and therapy as a change to the landscape.

Gottman & Murray's *The Mathematics of Marriage* (2002) predicted divorce not
from a score but from a PHASE PORTRAIT. Fit each partner's uninfluenced steady
state, emotional inertia, and influence function from minutes of conversation;
draw the null clines; and the plane of (his affect, her affect) partitions into
BASINS OF ATTRACTION around stable steady states (attractors), separated by
unstable ones. Where a conversation ends is decided by which basin it starts
in. The couples headed for divorce were the couples whose landscape had lost
its positive attractor -- every start decays to the negative one -- and the
formal content of therapy is a change to the landscape itself: create a
positive stable steady state, or widen its basin. Holling's and Scheffer's
resilience work supplies the last piece: RESILIENCE IS THE SIZE OF THE BASIN,
and a shrinking basin announces itself as slower recovery from perturbation
(critical slowing down) before the attractor disappears.

For a novelist this is the deepest form of "the marriage that could have
held": not one counterfactual run with a different ending, but the claim that
the couple's landscape does or does not CONTAIN a good ending -- and, if it
does not, the smallest change to the people that creates one.

The module is two-layered and honest about which layer is which:

  EMPIRICAL (the machine itself):
    phase_portrait(story)        sweep a grid of starting manners, run the
                                 actual coupled SOMA characters from each,
                                 cluster where they end -> the attractors; map
                                 start -> end -> the basins. Nothing is fitted;
                                 this is what the marriage does.
    resilience(story)            Holling/Scheffer, literally: the positive
                                 basin's share of the plane, plus a kick probe
                                 from the positive attractor -- the largest
                                 perturbation recovered from (basin radius) and
                                 how recovery time grows with kick size
                                 (slowing down as the rim approaches).

  FITTED (Gottman's own move, performed on the simulation):
    fit_influence(story)         regress, from the portrait's own trajectories,
                                 each partner's next manner on their own last
                                 (inertia, uninfluenced state) and their
                                 partner's last (a two-slope influence function
                                 hinged at neutral) -- the exact parameters
                                 Gottman fitted from observed conversations,
                                 recovered here from the Chronicle. The fitted
                                 map's own attractors are then computed and
                                 VALIDATED against the empirical portrait: a
                                 model of the model, checked against the
                                 machine that generated it.

  THE THERAPY QUESTION (bifurcation, not counterfactual):
    second_stable_state(story,   sweep one dial (a couple's gain, a loop's
        dial, values)            conviction...) and find the least change that
                                 CREATES a positive attractor, or grows its
                                 basin past a target share. Gottman's claim
                                 that intervention should move the influenced
                                 dynamics, staged as a search over landscapes.

Everything is falsifiable in the repository's usual sense: the portrait must
reproduce run-to-run (the dynamics are deterministic given a start); the fitted
model's attractors must land on the empirical ones; and any start staged in the
story proper must flow to the basin's attractor.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

POSITIVE_LINE = 5.5      # the ease guard in gottman.marry: warm is >= this

_UNIT = {"s": 1.0, "m": 60.0, "h": 3600.0, "d": 86400.0,
         "y": 31557600.0}


def _dur_seconds(d) -> float:
    """'1s' / '5m' / '1y' -> seconds; numbers pass through."""
    if isinstance(d, (int, float)):
        return float(d)
    s = str(d).strip()
    for u in sorted(_UNIT, key=len, reverse=True):
        if s.endswith(u):
            try:
                return float(s[:-len(u)]) * _UNIT[u]
            except ValueError:
                return 1.0
    try:
        return float(s)
    except ValueError:
        return 1.0


# ---------------------------------------------------------------------------
# running the coupled system from a chosen start
# ---------------------------------------------------------------------------

def _pair(story, a=None, b=None):
    if a is not None and b is not None:
        return (a.name if hasattr(a, "name") else a,
                b.name if hasattr(b, "name") else b)
    g = getattr(story, "_gottman", None)
    if g:
        return g["a"], g["b"]
    cs = story.characters
    if len(cs) < 2:
        raise ValueError("phase analysis needs two characters")
    return cs[0].name, cs[1].name


def _run_from(story, an, bn, a0, b0, *, beats, overrides=None,
              channel="manner"):
    """Run the couple with all scripted stimuli stripped and only the initial
    manners injected; return (Result, series_a, series_b)."""
    src = story.source()
    kept = [ln for ln in src.splitlines()
            if not ln.lstrip().startswith("stimulus ")]
    probes = [f"stimulus {an}.{channel} {{ at 1s: {round(a0, 2)} }}",
              f"stimulus {bn}.{channel} {{ at 1s: {round(b0, 2)} }}"]
    probe_src = "\n".join(kept + [""] + probes) + "\n"
    from soma.parser import parse
    from soma.interpreter import Interpreter
    prog = parse(probe_src, title=f"{story.title}__phase")
    if overrides:
        from soma.perturb import apply_set
        for key, val in overrides.items():
            spec = key if "=" in str(key) else f"{key}={val}"
            apply_set(prog, spec)
    r = Interpreter(prog).run()
    sa = r.channel_hist.get(f"{an}.{channel}", [])
    sb = r.channel_hist.get(f"{bn}.{channel}", [])
    return r, sa, sb


def _endpoint(series, tail=3):
    if not series:
        return 0.0
    t = series[-tail:] if len(series) >= tail else series
    return sum(t) / len(t)


def _tail_motion(series, tail=10):
    """Read the trajectory's tail: (center, amplitude, period). A settled
    trajectory has near-zero amplitude; a limit cycle keeps a sustained swing,
    whose period is estimated from the spacing of its interior peaks."""
    if not series:
        return 0.0, 0.0, 0.0
    t = series[-tail:] if len(series) > tail else series[:]
    center = sum(t) / len(t)
    amplitude = max(t) - min(t)
    peaks = [i for i in range(1, len(t) - 1)
             if t[i] >= t[i - 1] and t[i] > t[i + 1]]
    period = 0.0
    if len(peaks) >= 2:
        gaps = [q - p for p, q in zip(peaks, peaks[1:])]
        period = sum(gaps) / len(gaps)
    return center, amplitude, period


# ---------------------------------------------------------------------------
# the empirical portrait
# ---------------------------------------------------------------------------

@dataclass
class Attractor:
    """A stable state of the coupled system. `kind` distinguishes the two
    dynamical objects a relationship (or a psyche) can rest in: a FIXED point
    -- the system settles and stays -- and a CYCLE (a limit cycle): the stable
    state IS an oscillation, with an amplitude and a period. Rinaldi's model
    of Laura and Petrarch (SIAM J. Appl. Math, 1998) is the canonical
    character example: the poet's twenty-year emotional cycle between ecstasy
    and despair is not a failure to settle -- the cycle is the attractor."""
    a: float                 # axis-1 center (mean over the tail)
    b: float                 # axis-2 center
    share: float = 0.0       # fraction of the sampled plane in its basin
    kind: str = "fixed"      # "fixed" | "cycle"
    amplitude: float = 0.0   # peak-to-trough of the wider axis, if a cycle
    period: float = 0.0      # estimated beats per cycle (0 if inestimable)

    @property
    def positive(self) -> bool:
        return self.a >= POSITIVE_LINE and self.b >= POSITIVE_LINE

    @property
    def negative(self) -> bool:
        return self.a < POSITIVE_LINE and self.b < POSITIVE_LINE

    @property
    def cyclic(self) -> bool:
        return self.kind == "cycle"

    def label(self) -> str:
        base = ("warm" if self.positive else
                "cold" if self.negative else "split")
        return base if self.kind == "fixed" else f"{base} cycle"

    def render(self) -> str:
        head = (f"({self.a:.1f}, {self.b:.1f}) [{self.label()}] "
                f"holding {self.share:.0%} of the plane")
        if self.cyclic:
            per = (f", period ≈ {self.period:.0f} beats" if self.period
                   else "")
            head += f" (swing ±{self.amplitude / 2:.1f}{per})"
        return head


@dataclass
class PortraitReport:
    a_name: str
    b_name: str
    attractors: list                 # list[Attractor]
    basins: dict                     # (a0, b0) -> attractor index
    grid: list                       # the start values used on each axis
    trajectories: list               # list of (series_a, series_b), for fitting
    subject: str = "couple"          # "couple" (interpersonal) or "psyche"
    high_label: str = "warm"         # what an all-high attractor is called
    low_label: str = "cold"          # what an all-low attractor is called

    @property
    def healthy_share(self):
        """The fraction of the sampled plane whose trajectories settle in a
        healthy attractor (None when no `healthy_is` label was given). Public
        twin of the internal `_healthy_share`, which studies previously had to
        reach for directly."""
        return getattr(self, "_healthy_share", None)

    @property
    def positive_attractor(self) -> Optional[Attractor]:
        cands = [at for at in self.attractors if at.positive]
        return max(cands, key=lambda at: at.share) if cands else None

    @property
    def positive_share(self) -> float:
        return sum(at.share for at in self.attractors if at.positive)

    def attractor_of(self, a0, b0) -> Attractor:
        return self.attractors[self.basins[(a0, b0)]]

    def render(self) -> str:
        lines = [f"PHASE PORTRAIT — {self.a_name} x {self.b_name} "
                 f"({len(self.attractors)} attractor"
                 f"{'s' if len(self.attractors) != 1 else ''}):"]
        marks = "ABCDEFGH"
        for i, at in enumerate(self.attractors):
            if self.subject == "psyche":
                line = getattr(self, "_positive_line", None)
                l2 = line
                if line is None:
                    g2 = getattr(self, "_grid2", self.grid)
                    line = (min(self.grid) + max(self.grid)) / 2.0
                    l2 = (min(g2) + max(g2)) / 2.0
                hi = at.a >= line and at.b >= l2
                lo = at.a < line and at.b < l2
                tag = (self.high_label if hi else self.low_label if lo
                       else "mixed")
                if at.cyclic:
                    tag += " cycle"
                cyc = (f" (swing ±{at.amplitude / 2:.1f}"
                       + (f", period ≈ {at.period:.0f} beats" if at.period
                          else "") + ")") if at.cyclic else ""
                lines.append(f"  {marks[i]}: ({at.a:.1f}, {at.b:.1f}) [{tag}] "
                             f"holding {at.share:.0%} of the plane{cyc}")
            else:
                lines.append(f"  {marks[i]}: {at.render()}")
        # the plane, drawn: rows are the second axis (high at top),
        # columns are the first; each cell is the basin it belongs to.
        grid2 = getattr(self, "_grid2", self.grid)
        lines.append(f"  basins ({self.a_name} →, {self.b_name} ↑):")
        for b0 in sorted(grid2, reverse=True):
            row = "".join(marks[self.basins[(a0, b0)]].lower()
                          for a0 in sorted(self.grid))
            lines.append(f"    {b0:>5.1f} |{row}|")
        lines.append("          " + "".join("-" for _ in self.grid))
        if self.subject == "psyche":
            if getattr(self, "_healthy_share", None) is None:
                return "\n".join(lines)     # no healthy pole declared
            hshare = self._healthy_share
            hatt = getattr(self, "_healthy_attractors", [])
            if not hatt:
                lines.append(f"  NO {self.high_label.upper()} (healthy) "
                             f"attractor in range: every starting state flows "
                             f"to the {self.low_label} region.")
            else:
                lines.append(f"  the healthy basin holds {hshare:.0%} of the "
                             f"plane — a psyche is a set of attractors, and a "
                             f"disorder is one of them.")
            return "\n".join(lines)
        if self.positive_attractor is None:
            lines.append("  NO WARM ATTRACTOR: every opening decays to the "
                         "cold state. The landscape does not contain a "
                         "good ending.")
        else:
            lines.append(f"  the warm basin holds {self.positive_share:.0%} "
                         f"of the plane — the couple's resilience, as a "
                         f"region.")
        return "\n".join(lines)


def phase_portrait(story, a=None, b=None, *, grid: int = 5, lo: float = 1.0,
                   hi: float = 9.0, beats: int = 16, tol: float = 0.8,
                   osc_tol: float = 1.5, overrides: dict = None,
                   channel: str = "manner") -> PortraitReport:
    """Sweep a grid x grid square of opening manners, run the real coupled
    characters from each, and return the attractors and basins the machine
    itself displays."""
    an, bn = _pair(story, a, b)
    starts = [round(lo + i * (hi - lo) / (grid - 1), 2) for i in range(grid)]
    attractors: list[Attractor] = []
    basins, trajectories = {}, []

    def _assign(ea, eb, kind, amp, per) -> int:
        for i, at in enumerate(attractors):
            if (abs(at.a - ea) <= tol and abs(at.b - eb) <= tol
                    and at.kind == kind):
                return i
        attractors.append(Attractor(a=round(ea, 2), b=round(eb, 2),
                                    kind=kind, amplitude=round(amp, 2),
                                    period=round(per, 1)))
        return len(attractors) - 1

    for a0 in starts:
        for b0 in starts:
            _, sa, sb = _run_from(story, an, bn, a0, b0, beats=beats,
                                  overrides=overrides, channel=channel)
            trajectories.append((sa, sb))
            tail = max(10, beats // 2)
            ca, aa, pa = _tail_motion(sa, tail=tail)
            cb, ab, pb = _tail_motion(sb, tail=tail)
            amp = max(aa, ab)
            kind = "cycle" if amp > osc_tol else "fixed"
            per = pa if aa >= ab else pb
            basins[(a0, b0)] = _assign(ca, cb, kind, amp, per)

    n = len(starts) ** 2
    for i, at in enumerate(attractors):
        at.share = sum(1 for v in basins.values() if v == i) / n
    return PortraitReport(a_name=an, b_name=bn, attractors=attractors,
                          basins=basins, grid=starts,
                          trajectories=trajectories)


# ---------------------------------------------------------------------------
# fitting Gottman's parameters from the simulation's own trajectories
# ---------------------------------------------------------------------------

def _lstsq(rows, ys):
    """Tiny normal-equations least squares (pure python), returns coefs."""
    k = len(rows[0])
    ata = [[sum(r[i] * r[j] for r in rows) for j in range(k)] for i in range(k)]
    atb = [sum(r[i] * y for r, y in zip(rows, ys)) for i in range(k)]
    # gaussian elimination with partial pivoting
    m = [ata[i] + [atb[i]] for i in range(k)]
    for col in range(k):
        piv = max(range(col, k), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-12:
            m[col][col] += 1e-9      # ridge nudge for degenerate designs
            piv = col
        m[col], m[piv] = m[piv], m[col]
        for r in range(col + 1, k):
            f = m[r][col] / m[col][col]
            for c in range(col, k + 1):
                m[r][c] -= f * m[col][c]
    x = [0.0] * k
    for r in range(k - 1, -1, -1):
        x[r] = (m[r][k] - sum(m[r][c] * x[c] for c in range(r + 1, k))) / m[r][r]
    return x


@dataclass
class FittedPartner:
    """One partner's Gottman–Murray parameters, recovered by regression from
    the simulated conversation: m[t+1] = c + r*m[t] + I(partner[t]).

    Two functional forms for I, both from the book: BILINEAR (two slopes
    hinged at neutral) and OJIVE (two plateaus past thresholds, a deadband
    between). Each partner carries whichever form fit their trajectories
    better (by R²) -- Gottman's own model-selection question, answered from
    the data."""
    name: str
    form: str                # "bilinear" | "ojive"
    uninfluenced: float      # the manner they would hold alone (c / (1-r))
    inertia: float           # r: how much of themselves carries to the next beat
    r2: float                # fit quality on the pooled trajectories
    # bilinear params
    warm_slope: float = 0.0
    cold_slope: float = 0.0
    # ojive params
    warm_plateau: float = 0.0    # influence when partner reads warm
    cold_plateau: float = 0.0    # influence when partner reads cold
    warm_at: float = 5.5
    cold_at: float = 4.0

    def influence(self, partner_m: float, neutral: float = 5.0) -> float:
        if self.form == "bilinear":
            d = partner_m - neutral
            return (self.warm_slope if d >= 0 else self.cold_slope) * d
        if partner_m >= self.warm_at:
            return self.warm_plateau
        if partner_m <= self.cold_at:
            return self.cold_plateau
        return 0.0

    def step(self, own_m: float, partner_m: float) -> float:
        nxt = (self.uninfluenced * (1.0 - self.inertia)
               + self.inertia * own_m + self.influence(partner_m))
        return max(0.0, min(10.0, nxt))

    def render(self) -> str:
        if self.form == "bilinear":
            inf = (f"influence slopes warm {self.warm_slope:+.2f} / "
                   f"cold {self.cold_slope:+.2f}")
        else:
            inf = (f"influence plateaus warm {self.warm_plateau:+.2f} / "
                   f"cold {self.cold_plateau:+.2f} (ojive)")
        return (f"{self.name}: uninfluenced state {self.uninfluenced:.1f}, "
                f"inertia {self.inertia:.2f}, {inf}  [R²={self.r2:.2f}]")


@dataclass
class FittedModel:
    a: FittedPartner
    b: FittedPartner
    neutral: float = 5.0

    def attractors(self, *, grid: int = 5, lo: float = 1.0, hi: float = 9.0,
                   iters: int = 200, tol: float = 0.6) -> list:
        """The fitted map's own stable states, found by iterating it
        (simultaneous update) from a grid of starts -- robust to the piecewise
        regions of either influence form."""
        found = []
        starts = [lo + i * (hi - lo) / (grid - 1) for i in range(grid)]
        for a0 in starts:
            for b0 in starts:
                ma, mb = a0, b0
                for _ in range(iters):
                    # damped (Krasnoselskii) iteration: finds the same fixed
                    # points while suppressing the spurious 2-cycles a
                    # zero-inertia mirror map admits
                    na, nb = self.a.step(ma, mb), self.b.step(mb, ma)
                    ma, mb = 0.5 * ma + 0.5 * na, 0.5 * mb + 0.5 * nb
                # keep only genuine fixed points of the undamped map
                na, nb = self.a.step(ma, mb), self.b.step(mb, ma)
                if abs(na - ma) > 0.2 or abs(nb - mb) > 0.2:
                    continue
                if not any(abs(fa - ma) <= tol and abs(fb - mb) <= tol
                           for fa, fb in found):
                    found.append((round(ma, 2), round(mb, 2)))
        return found

    def validate(self, portrait: PortraitReport, *, tol: float = 1.2) -> dict:
        """Gottman's move, closed into a loop: do the parameters fitted from
        the conversation reproduce the landscape the machine displays? The
        check is BIDIRECTIONAL -- every empirical attractor must be matched by
        a fitted one within `tol`, and every fitted attractor by an empirical
        one -- so a degenerate fit whose map is everywhere quasi-fixed cannot
        pass by accident."""
        fitted = self.attractors()
        emp = [(at.a, at.b) for at in portrait.attractors]
        def near(p, qs):
            return any(abs(p[0]-q[0]) <= tol and abs(p[1]-q[1]) <= tol
                       for q in qs)
        fwd = [{"empirical": e, "matched": near(e, fitted)} for e in emp]
        back = [{"fitted": f, "matched": near(f, emp)} for f in fitted]
        ok = (all(m["matched"] for m in fwd)
              and all(m["matched"] for m in back))
        return {"ok": ok, "empirical_matched": fwd, "fitted_matched": back,
                "fitted_attractors": fitted,
                "r2": (self.a.r2, self.b.r2)}

    def render(self) -> str:
        return ("FITTED INFLUENCE MODEL (regressed from the run itself):\n  "
                + self.a.render() + "\n  " + self.b.render())


def _r2(rows, ys, coefs):
    preds = [sum(c * x for c, x in zip(coefs, r)) for r in rows]
    my = sum(ys) / len(ys)
    ss_tot = sum((y - my) ** 2 for y in ys) or 1e-12
    ss_res = sum((y - p) ** 2 for y, p in zip(ys, preds))
    return 1.0 - ss_res / ss_tot


def fit_influence(portrait: PortraitReport, *, neutral: float = 5.0,
                  warm_grid=(5.0, 5.5, 6.0, 6.5, 7.0),
                  cold_grid=(3.0, 3.5, 4.0, 4.5, 5.0),
                  skip: int = 2) -> FittedModel:
    """Recover each partner's uninfluenced state, inertia, and influence
    function by least squares over ALL the portrait's trajectories, trying
    BOTH of Gottman's functional forms -- bilinear (two slopes through
    neutral) and ojive (two plateaus past thresholds) -- and keeping, per
    partner, whichever fits their data better. The ojive THRESHOLDS are
    themselves fitted (searched over warm_grid x cold_grid for best R²):
    this is Gottman's negativity-threshold estimation, and it matters because
    a couple's gain shifts where the partner's shown manner actually crosses
    the guard. `skip` drops the first beats, before the injected opening has
    landed."""
    def fit_one(own_ix, other_ix, name):
        base_rows, bi_cols, others, ys = [], [], [], []
        for traj in portrait.trajectories:
            own, other = traj[own_ix], traj[other_ix]
            for t in range(skip, min(len(own), len(other)) - 1):
                d = other[t] - neutral
                base_rows.append([1.0, own[t]])
                bi_cols.append([max(0.0, d), min(0.0, d)])
                others.append(other[t])
                ys.append(own[t + 1])
        bi_rows = [b + c for b, c in zip(base_rows, bi_cols)]
        bi = _lstsq(bi_rows, ys)
        r2_bi = _r2(bi_rows, ys, bi)
        # ojive: search the thresholds (Gottman's negativity threshold)
        best = None
        for wa in warm_grid:
            for ca in cold_grid:
                if ca >= wa:
                    continue
                oj_rows = [b + [1.0 if o >= wa else 0.0,
                                1.0 if o <= ca else 0.0]
                           for b, o in zip(base_rows, others)]
                oj = _lstsq(oj_rows, ys)
                r2 = _r2(oj_rows, ys, oj)
                if best is None or r2 > best[0]:
                    best = (r2, oj, wa, ca)
        r2_oj, oj, wa, ca = best
        if r2_oj > r2_bi:
            c, r, ph, pl = oj
            r = max(0.0, min(0.999, r))
            u = c / (1.0 - r) if (1.0 - r) > 1e-9 else c
            return FittedPartner(name=name, form="ojive",
                                 uninfluenced=round(u, 2), inertia=round(r, 3),
                                 r2=round(r2_oj, 3),
                                 warm_plateau=round(ph, 3),
                                 cold_plateau=round(pl, 3),
                                 warm_at=wa, cold_at=ca)
        c, r, wp, wn = bi
        r = max(0.0, min(0.999, r))
        u = c / (1.0 - r) if (1.0 - r) > 1e-9 else c
        return FittedPartner(name=name, form="bilinear",
                             uninfluenced=round(u, 2), inertia=round(r, 3),
                             r2=round(r2_bi, 3),
                             warm_slope=round(wp, 3), cold_slope=round(wn, 3))
    return FittedModel(a=fit_one(0, 1, portrait.a_name),
                       b=fit_one(1, 0, portrait.b_name), neutral=neutral)


# ---------------------------------------------------------------------------
# resilience: the basin as a region, and the kick probe
# ---------------------------------------------------------------------------

@dataclass
class ResilienceReport:
    who: str
    basin_share: float        # Holling: resilience as the basin's size
    attractor: Optional[tuple]
    kicks: list               # (kick, recovered, recovery_beats)

    @property
    def basin_radius(self) -> float:
        """The largest probed kick the warm state recovers from."""
        rec = [k for k, ok, _ in self.kicks if ok]
        return max(rec) if rec else 0.0

    @property
    def slowing(self) -> bool:
        """Does recovery take longer as the kick approaches the rim --
        critical slowing down, read directly off the recovery times?"""
        times = [t for _, ok, t in self.kicks if ok and t is not None]
        return len(times) >= 2 and times[-1] > times[0]

    def render(self) -> str:
        if self.attractor is None:
            return (f"RESILIENCE — {self.who}: none. There is no warm "
                    f"attractor to be resilient AT.")
        rows = "\n".join(
            f"    kick -{k:.1f}: " + (f"recovers in {t} beats" if ok
                                      else "does NOT recover — over the rim")
            for k, ok, t in self.kicks)
        return (f"RESILIENCE — {self.who}: warm basin holds "
                f"{self.basin_share:.0%} of the plane; kick probe from "
                f"{self.attractor}:\n{rows}\n    basin radius ≈ "
                f"{self.basin_radius:.1f}"
                + ("; recovery slows toward the rim (critical slowing down)"
                   if self.slowing else ""))


def resilience(story, a=None, b=None, *, portrait: PortraitReport = None,
               kicks=(1.0, 2.0, 3.0, 4.0), beats: int = 16,
               recover_tol: float = 0.8, overrides: dict = None
               ) -> ResilienceReport:
    """Two readings of one quantity. The warm basin's SHARE of the plane is
    Holling's resilience-as-region; the KICK PROBE is Scheffer's engineering
    reading -- perturb both partners coldward from the warm attractor by
    increasing amounts, and measure whether and how fast the marriage returns.
    Recovery slowing as the kick grows is the empirical signature of a rim."""
    an, bn = _pair(story, a, b)
    p = portrait or phase_portrait(story, a, b, overrides=overrides)
    warm = p.positive_attractor
    if warm is None:
        return ResilienceReport(who=f"{an} & {bn}", basin_share=0.0,
                                attractor=None, kicks=[])
    out = []
    for k in kicks:
        _, sa, sb = _run_from(story, an, bn, warm.a - k, warm.b - k,
                              beats=beats, overrides=overrides)
        ea, eb = _endpoint(sa), _endpoint(sb)
        ok = abs(ea - warm.a) <= recover_tol and abs(eb - warm.b) <= recover_tol
        t_rec = None
        if ok:
            for t in range(len(sa)):
                if (abs(sa[t] - warm.a) <= recover_tol
                        and abs(sb[t] - warm.b) <= recover_tol):
                    t_rec = t
                    break
        out.append((k, ok, t_rec))
    return ResilienceReport(who=f"{an} & {bn}", basin_share=p.positive_share,
                            attractor=(warm.a, warm.b), kicks=out)


# ---------------------------------------------------------------------------
# therapy as bifurcation: the least change that changes the landscape
# ---------------------------------------------------------------------------

@dataclass
class LandscapeChange:
    dial: str
    baseline_share: float
    curve: list                # (value, positive_share, n_attractors)
    threshold: Optional[float] # least value meeting the target, in sweep order
    target: float

    def render(self) -> str:
        rows = "\n".join(f"    {self.dial} = {v}: warm basin {s:.0%} "
                         f"({n} attractor{'s' if n != 1 else ''})"
                         for v, s, n in self.curve)
        head = (f"THE SECOND STABLE STATE — sweeping {self.dial} "
                f"(baseline warm share {self.baseline_share:.0%}, "
                f"target ≥ {self.target:.0%}):\n{rows}")
        if self.threshold is None:
            return head + "\n    NO value in range changes the landscape enough."
        return (head + f"\n    the landscape acquires its good ending at "
                f"{self.dial} = {self.threshold} — the marriage that could "
                f"have held, as a bifurcation.")


def second_stable_state(story, dial, values, *, a=None, b=None,
                        target_share: float = 0.25, grid: int = 4,
                        beats: int = 16) -> LandscapeChange:
    """Gottman's therapy claim, staged as a search over landscapes: sweep one
    dial and find the least value (in the order given -- pass values sorted by
    intervention size) at which the couple's phase portrait contains a warm
    basin of at least `target_share`. This is a stronger object than a
    counterfactual ending: it asserts the existence, or absence, of a region
    of openings from which the marriage holds. `dial` may be a list of dials
    swept in lockstep (e.g. both directions of a couple's gain)."""
    dials = [dial] if isinstance(dial, str) else list(dial)
    base = phase_portrait(story, a, b, grid=grid, beats=beats)
    curve, threshold = [], None
    for v in values:
        p = phase_portrait(story, a, b, grid=grid, beats=beats,
                           overrides={d: v for d in dials})
        curve.append((v, round(p.positive_share, 3), len(p.attractors)))
        if threshold is None and p.positive_share >= target_share:
            threshold = v
    return LandscapeChange(dial=" & ".join(dials),
                           baseline_share=round(base.positive_share, 3),
                           curve=curve, threshold=threshold,
                           target=target_share)


# ---------------------------------------------------------------------------
# the intrapersonal plane: two channels of one psyche
# ---------------------------------------------------------------------------

def state_portrait(story, who, channels, *, grid: int = 5, lo: float = 0.0,
                   hi: float = 100.0, lo2: float = None, hi2: float = None,
                   beats: int = 20, tol: float = None, osc_tol: float = None,
                   positive_line: float = None, high_label: str = "high",
                   low_label: str = "low", healthy_is: str = "high",
                   overrides: dict = None
                   ) -> PortraitReport:
    """The phase portrait of a SINGLE psyche: the plane of two of one
    character's channels (arousal x perceived threat, hope x dread), swept
    from a grid of initial states and clustered into attractors and basins.

    This is the object at the center of the computational-psychopathology
    literature (Robinaugh et al.'s panic model; Scheffer's alternative stable
    states of mood): a disorder is not a level of a variable but an ATTRACTOR
    of the person -- a region of starting states from which the psyche flows
    into a self-sustaining configuration and stays. Axis ranges default to
    body-channel scale (0..100); pass lo2/hi2 if the axes differ. The
    `positive` labelling of attractors uses `positive_line` per axis if given
    (else the plane's midpoint), so a "warm" attractor here means "both
    channels below/above whatever the caller deems the healthy side" only
    through the labels; interpret with the axes in mind."""
    name = who.name if hasattr(who, "name") else who
    ch_a, ch_b = channels
    lo2 = lo if lo2 is None else lo2
    hi2 = hi if hi2 is None else hi2
    span = max(hi - lo, hi2 - lo2)
    tol = 0.08 * span if tol is None else tol
    osc_tol = 0.15 * span if osc_tol is None else osc_tol
    starts_a = [round(lo + i * (hi - lo) / (grid - 1), 2) for i in range(grid)]
    starts_b = [round(lo2 + i * (hi2 - lo2) / (grid - 1), 2)
                for i in range(grid)]
    attractors, basins, trajectories = [], {}, []

    def _assign(ea, eb, kind, amp, per) -> int:
        for i, at in enumerate(attractors):
            if (abs(at.a - ea) <= tol and abs(at.b - eb) <= tol
                    and at.kind == kind):
                return i
        attractors.append(Attractor(a=round(ea, 2), b=round(eb, 2),
                                    kind=kind, amplitude=round(amp, 2),
                                    period=round(per, 1)))
        return len(attractors) - 1

    src = story.source()
    kept = [ln for ln in src.splitlines()
            if not ln.lstrip().startswith("stimulus ")]
    multi = len(story.characters) > 1
    from soma.parser import parse
    from soma.interpreter import Interpreter
    from soma.perturb import apply_set
    for a0 in starts_a:
        for b0 in starts_b:
            scope = f"{name}." if multi else ""
            probes = [f"stimulus {scope}{ch_a} {{ at 1s: {a0} }}",
                      f"stimulus {scope}{ch_b} {{ at 1s: {b0} }}"]
            probe_src = "\n".join(kept + [""] + probes) + "\n"
            prog = parse(probe_src, title=f"{story.title}__state")
            if overrides:
                for key, val in overrides.items():
                    spec = key if "=" in str(key) else f"{key}={val}"
                    apply_set(prog, spec)
            r = Interpreter(prog).run()
            sa = (r.channel_hist.get(f"{name}.{ch_a}")
                  or r.channel_hist.get(ch_a, []))
            sb = (r.channel_hist.get(f"{name}.{ch_b}")
                  or r.channel_hist.get(ch_b, []))
            trajectories.append((sa, sb))
            tail = max(10, beats // 2)
            ca, aa, pa = _tail_motion(sa, tail=tail)
            cb, ab, pb = _tail_motion(sb, tail=tail)
            amp = max(aa, ab)
            kind = "cycle" if amp > osc_tol else "fixed"
            per = pa if aa >= ab else pb
            basins[(a0, b0)] = _assign(ca, cb, kind, amp, per)

    n = grid * grid
    for i, at in enumerate(attractors):
        at.share = sum(1 for v in basins.values() if v == i) / n
    # classify which attractor is the "healthy" one by the declared pole and
    # a midpoint line, independent of the interpersonal POSITIVE_LINE.
    line = positive_line if positive_line is not None else (lo + hi) / 2.0
    line2 = positive_line if positive_line is not None else (lo2 + hi2) / 2.0

    def _healthy(at):
        hi_side = at.a >= line and at.b >= line2
        lo_side = at.a < line and at.b < line2
        return hi_side if healthy_is == "high" else lo_side

    rep = PortraitReport(a_name=f"{name}.{ch_a}", b_name=f"{name}.{ch_b}",
                         attractors=attractors, basins=basins,
                         grid=starts_a, trajectories=trajectories,
                         subject="psyche", high_label=high_label,
                         low_label=low_label)
    if healthy_is is None:
        rep._healthy_share = None
        rep._healthy_attractors = []
    else:
        rep._healthy_share = sum(at.share for at in attractors if _healthy(at))
        rep._healthy_attractors = [at for at in attractors if _healthy(at)]
    rep._grid2 = starts_b
    rep._positive_line = positive_line
    return rep


# ---------------------------------------------------------------------------
# hysteresis: the up-path and the down-path disagree
# ---------------------------------------------------------------------------

@dataclass
class HysteresisReport:
    """The signature of alternative stable states (Scheffer; and the panic
    model's central clinical claim): the stressor level that TRIGGERS the high
    state is not the level that RELEASES it. Between the two thresholds the
    system is bistable -- where it sits depends on where it has been, i.e. the
    psyche has a memory that is dynamical, not stored. `width` is the size of
    the trap: how far below its own trigger the state persists. A width of ~0
    is a reversible system; `releases=None` is the extreme case -- once
    triggered, no reduction of the stressor in range ends it."""
    who: str
    stimulus: str
    response: str
    up_path: list             # (stimulus level, response) ascending
    down_path: list           # (stimulus level, response) descending
    triggers_at: object       # first up-level where response crosses high
    releases_at: object       # first down-level where response falls low again
    high: float
    low: float
    resolution: float = 1.0   # the sweep's own step: a loop no wider than
                              # this is quantization, not bistability

    @property
    def width(self) -> float:
        if self.triggers_at is None:
            return 0.0
        if self.releases_at is None:
            return float("inf")
        return self.triggers_at - self.releases_at

    @property
    def bistable(self) -> bool:
        return self.triggers_at is not None and (
            self.releases_at is None or self.width > self.resolution)

    def render(self) -> str:
        def path(p):
            return "  ".join(f"{s:g}->{r:.0f}" for s, r in p)
        w = ("∞ (self-sustaining: no release in range)"
             if self.width == float("inf") else f"{self.width:g}")
        return (f"HYSTERESIS — {self.who}, {self.stimulus} vs {self.response}:\n"
                f"  up:   {path(self.up_path)}\n"
                f"  down: {path(self.down_path)}\n"
                f"  triggers at {self.triggers_at}, releases at "
                f"{self.releases_at} — loop width {w}"
                + ("\n  the up-path and the down-path disagree: two stable "
                   "states, and history decides between them."
                   if self.bistable else
                   "\n  no loop: the response retraces its path — one stable "
                   "state, fully reversible."))


def hysteresis(story, who, stimulus: str, response: str, *, levels=None,
               dwell: int = 6, high: float = None, low: float = None,
               overrides: dict = None) -> HysteresisReport:
    """Sweep `stimulus` up through `levels` and back down, holding each level
    for `dwell` beats, in ONE continuous run (so the state carries over --
    that is the point), and read `response` at the end of each plateau.
    `triggers_at` is the first ascending level at which the response crosses
    `high`; `releases_at` the first descending level at which it falls back
    below `low`. Defaults: levels 0..9, and high/low from the observed
    response range (upper/lower third)."""
    name = who.name if hasattr(who, "name") else who
    levels = list(levels) if levels is not None else [i * 1.0 for i in range(10)]
    seq = levels + list(reversed(levels[:-1]))
    src = story.source()
    kept = [ln for ln in src.splitlines()
            if not ln.lstrip().startswith("stimulus ")]
    # the sweep must fit inside the run: extend the sim duration to cover
    # every plateau (plus settling room), in the story's own step units
    import re as _re
    step_s = _dur_seconds(getattr(story, "step", "1s"))
    need = (len(seq) * dwell + 3) * step_s
    for i, ln in enumerate(kept):
        m = _re.search(r"duration:\s*([0-9.]+)\s*([a-z]+)", ln)
        if m:
            cur = float(m.group(1)) * _UNIT.get(m.group(2), 1.0)
            if cur < need:
                kept[i] = _re.sub(r"duration:\s*[0-9.]+\s*[a-z]+",
                                  f"duration: {need:g}s", ln)
            break
    multi = len(story.characters) > 1
    scope = f"{name}." if multi else ""
    body = "  ".join(f"at {1 + i * dwell}s: {v:g}" for i, v in enumerate(seq))
    probe_src = "\n".join(
        kept + ["", f"stimulus {scope}{stimulus} {{ {body} }}"]) + "\n"
    from soma.parser import parse
    from soma.interpreter import Interpreter
    from soma.perturb import apply_set
    prog = parse(probe_src, title=f"{story.title}__hysteresis")
    if overrides:
        for key, val in overrides.items():
            spec = key if "=" in str(key) else f"{key}={val}"
            apply_set(prog, spec)
    r = Interpreter(prog).run()
    ys = (r.channel_hist.get(f"{name}.{response}")
          or r.channel_hist.get(response, []))
    # sample the response at the end of each plateau
    reads = []
    for i, v in enumerate(seq):
        t = min(len(ys) - 1, i * dwell + dwell - 1)
        reads.append((v, ys[t] if ys else 0.0))
    n_up = len(levels)
    up_path, down_path = reads[:n_up], reads[n_up:]
    vals = [y for _, y in reads]
    if high is None or low is None:
        lo_v, hi_v = min(vals), max(vals)
        high = lo_v + 2 * (hi_v - lo_v) / 3 if high is None else high
        low = lo_v + (hi_v - lo_v) / 3 if low is None else low
    triggers = next((s for s, y in up_path if y >= high), None)
    releases = next((s for s, y in down_path if y <= low), None)
    res = max((b - a for a, b in zip(levels, levels[1:])), default=1.0)
    return HysteresisReport(who=name, stimulus=stimulus, response=response,
                            up_path=up_path, down_path=down_path,
                            triggers_at=triggers, releases_at=releases,
                            high=high, low=low, resolution=res)
