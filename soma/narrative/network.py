"""
soma.narrative.network -- a person as a network of symptoms.

Every other predictive layer in this library builds a character from loops the
author wires by hand. This one builds a character whose behaviour is
EMERGENT: a network of symptoms, each activating its neighbours, whose
collective dynamics -- two stable states, a catastrophe between them, a
memory -- no single node contains. It is the object at the centre of the
network theory of mental disorders (Cramer, van Borkulo, Giltay, van der Maas,
Kendler, Scheffer & Borsboom, "Major Depression as a Complex Dynamic System",
PLoS ONE 2016): major depression not as a latent disease expressing itself in
symptoms, but as the symptoms themselves, directly connected -- insomnia ->
fatigue -> poor concentration -> loss of interest -> low mood -> worthlessness
-- so that the disorder is a state the NETWORK falls into and holds.

The model, faithfully:

  * each symptom s_i is an activation in [0,1];
  * it relaxes toward a LOGISTIC function of its neighbours' activations,
    the external stress, and its own threshold:
        s_i  ->  sigmoid( C * sum_j w_ij s_j  +  stress  -  threshold_i );
  * C is the CONNECTIVITY, and it is the whole theory's load-bearing claim:
    it is not a symptom, not stress, but the STRENGTH OF THE COUPLING that
    makes a person vulnerable. In a strongly connected network one bad night's
    sleep is enough to pull the rest down; in a weakly connected one it stays
    local.

Three signatures the paper stakes, and this module reproduces as generated
predictions (see `examples/narrative/the_weight.py`):

  1. VULNERABILITY IS CONNECTIVITY. Sweep stress at several C: the strongly
     connected network tips into the depressed state at far lower stress than
     the weakly connected one. `stress_response(net)` returns the curve;
     `tipping_stress(net)` the threshold.

  2. HYSTERESIS / SPONTANEOUS NON-RECOVERY. Ramp stress up and back down in one
     run: in a strongly connected network the stress reduction needed to
     LEAVE the depressed state is far greater than the stress that produced
     it -- the depression outlives its cause. `hysteresis_loop(net)`, built on
     the phase layer's own hysteresis instrument, measures the gap.

  3. THE FORBIDDEN ZONE. The number of active symptoms at equilibrium is
     bimodal -- a network sits at "few" or "many", rarely between -- and the
     empty middle widens with connectivity (the cusp catastrophe's fold).
     `equilibrium_modes(net)` samples it.

Everything compiles to ordinary SOMA: N `flow`s on the neural clock, one per
symptom, each a logistic of the summed neighbour channels. The network is
therefore inspectable, perturbable (connectivity and thresholds are dials),
and testable in exactly the same way as every hand-wired character -- but its
depression is something it DOES, not something it was told to have.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# the network object
# ---------------------------------------------------------------------------

@dataclass
class SymptomNetwork:
    """A named person and their symptom graph. Build with `symptom_network`,
    then hand to the study functions. `weights[(a, b)]` is the directed
    coupling from symptom a to symptom b (default 1.0); `thresholds[s]` is how
    much summed input a symptom needs to activate (default `threshold`)."""
    name: str
    symptoms: list
    edges: list                    # (a, b) directed; a activates b
    connectivity: float = 1.0
    threshold: float = 3.2
    weights: dict = field(default_factory=dict)
    thresholds: dict = field(default_factory=dict)
    relax: float = 3.0             # relaxation time constant (beats)
    baseline: float = 0.02
    span: str = "45s"
    step: str = "1s"

    def w(self, a, b) -> float:
        return self.weights.get((a, b), 1.0)

    def thr(self, s) -> float:
        return self.thresholds.get(s, self.threshold)

    def _inputs_expr(self, s) -> str:
        terms = []
        for (a, b) in self.edges:
            if b == s:
                wgt = self.w(a, b)
                terms.append(a if wgt == 1.0 else f"{wgt:g} * {a}")
            if a == s:                      # undirected use: symmetric read
                pass
        return " + ".join(terms) if terms else "0"

    def source(self, *, stress_channel: bool = True) -> str:
        """Compile to SOMA source: a body with one channel per symptom (plus a
        stress channel), and one neural `flow` per symptom implementing the
        logistic update."""
        body = [f"body {self.name} @neural {{"]
        for s in self.symptoms:
            body.append(f"  intero {s} : Signal baseline {self.baseline:g}")
        if stress_channel:
            body.append(f"  extero stress : Signal baseline 0")
        body.append("}")
        head = [f"sim {{ duration: {_secs(self.span):g}s  dt: {_secs(self.step):g}s }}",
                f"let conn = {self.connectivity:g}"]
        if not stress_channel:
            head.append("let stress = 0")
        flows = []
        for s in self.symptoms:
            th = self.thr(s)
            # render `- threshold` safely: a negative threshold must become
            # `+ |th|`, never `- -th` (which the lexer reads as two tokens).
            thr_term = f"- {th:g}" if th >= 0 else f"+ {abs(th):g}"
            flows.append(
                f"flow {s} @neural {{ dynamics: "
                f"( sigmoid( conn * ({self._inputs_expr(s)}) + stress "
                f"{thr_term} ) - {s} ) / {self.relax:g} }}")
        return "\n".join(body + head + flows)

    def degree(self) -> dict:
        """In-degree (number of activating inputs) per symptom -- the network's
        own centrality read-out, useful for choosing an intervention target."""
        d = {s: 0 for s in self.symptoms}
        for (a, b) in self.edges:
            d[b] = d.get(b, 0) + 1
        return d

    def out_degree(self) -> dict:
        """Out-degree (number of symptoms this one activates) -- the DYNAMIC
        hub: how much a symptom drives the rest, which is what a temporal-VAR
        out-strength estimate recovers. Distinct from in-degree, which counts
        what drives INTO a symptom."""
        d = {s: 0 for s in self.symptoms}
        for (a, b) in self.edges:
            d[a] = d.get(a, 0) + 1
        return d


def symptom_network(name, symptoms, edges, *, connectivity=1.0,
                    threshold=3.2, weights=None, thresholds=None,
                    relax=3.0, baseline=0.02, span="45s",
                    step="1s") -> SymptomNetwork:
    return SymptomNetwork(name=name, symptoms=list(symptoms),
                          edges=list(edges), connectivity=connectivity,
                          threshold=threshold, weights=dict(weights or {}),
                          thresholds=dict(thresholds or {}), relax=relax,
                          baseline=baseline, span=span, step=step)


# a canonical DSM-ish depression network (the paper's example, simplified to a
# connected graph over the nine core symptoms).
DEPRESSION_SYMPTOMS = ["insomnia", "fatigue", "concentration", "interest",
                       "mood", "appetite", "worthless", "psychomotor",
                       "suicidal"]
DEPRESSION_EDGES = [
    ("insomnia", "fatigue"), ("fatigue", "concentration"),
    ("concentration", "interest"), ("interest", "mood"),
    ("mood", "worthless"), ("worthless", "suicidal"),
    ("fatigue", "mood"), ("mood", "appetite"), ("interest", "psychomotor"),
    ("mood", "concentration"), ("insomnia", "mood"), ("worthless", "mood"),
    ("mood", "interest"), ("fatigue", "insomnia"),
]


def depression_network(name="Person", *, connectivity=1.0, **kw):
    """The paper's running example: the nine core MD symptoms, connected. Vary
    `connectivity` to make a resilient (~0.4) or vulnerable (~1.4) person."""
    return symptom_network(name, DEPRESSION_SYMPTOMS, DEPRESSION_EDGES,
                           connectivity=connectivity, **kw)


# ---------------------------------------------------------------------------
# running
# ---------------------------------------------------------------------------

def _secs(d) -> float:
    from .phase import _dur_seconds
    return _dur_seconds(d)


def _run(net: SymptomNetwork, stress_schedule=None, trigger=None,
         overrides=None):
    """Run the network. `stress_schedule` is a dict {beat: level} or a constant
    float held throughout; `trigger` is an optional (symptom, beat, value) kick
    (a bad night, a loss)."""
    stress_channel = not isinstance(stress_schedule, (int, float))
    src = net.source(stress_channel=stress_channel)
    if isinstance(stress_schedule, (int, float)):
        src = src.replace("let stress = 0", f"let stress = {stress_schedule:g}")
    stims = []
    if stress_channel and stress_schedule:
        body = "  ".join(f"at {b}s: {v:g}" for b, v in
                         sorted(stress_schedule.items()))
        stims.append(f"stimulus stress {{ {body} }}")
    if trigger:
        s, b, v = trigger
        stims.append(f"stimulus {s} {{ at {b}s: {v:g} }}")
    if stims:
        src = src + "\n" + "\n".join(stims)
    from soma.parser import parse
    from soma.interpreter import Interpreter
    prog = parse(src, title=f"{net.name}__network")
    if overrides:
        from soma.perturb import apply_set
        for k, val in overrides.items():
            apply_set(prog, k if "=" in str(k) else f"{k}={val}")
    return Interpreter(prog).run()


def _active_count(result, net, at=-1):
    n = 0
    for s in net.symptoms:
        h = (result.channel_hist.get(s)
             or result.channel_hist.get(f"{net.name}.{s}", []))
        if h and h[at] > 0.5:
            n += 1
    return n


# ---------------------------------------------------------------------------
# study 1: vulnerability is connectivity
# ---------------------------------------------------------------------------

@dataclass
class StressResponse:
    name: str
    connectivity: float
    curve: list                    # (stress, symptoms_active_at_equilibrium)
    tipping: Optional[float]       # least stress reaching the depressed state

    def render(self) -> str:
        from soma.viz import bar
        top = max((n for _, n in self.curve), default=1) or 1
        rows = []
        for s, n in self.curve:
            mark = ("  <- tips" if (self.tipping is not None
                                    and abs(s - self.tipping) < 1e-9) else "")
            rows.append(f"    stress {s:>4g}: {bar(n / top, 12)} "
                        f"{n} symptom{'s' if n != 1 else ''}{mark}")
        tail = (f"tips into depression at stress ≥ {self.tipping:g}"
                if self.tipping is not None
                else "does not reach the depressed state in range")
        return (f"STRESS RESPONSE — {self.name} "
                f"(connectivity {self.connectivity:g}):\n"
                + "\n".join(rows) + f"\n  {tail}")


def stress_response(net: SymptomNetwork, *,
                    levels=(0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4),
                    trigger=None, depressed_at: int = 5) -> StressResponse:
    """Hold stress at each level, run to equilibrium, count active symptoms.
    The curve's steep rise is the transition; `tipping` is the least stress
    that reaches `depressed_at` active symptoms."""
    curve, tipping = [], None
    for st in levels:
        r = _run(net, stress_schedule=float(st), trigger=trigger)
        n = _active_count(r, net)
        curve.append((float(st), n))
        if tipping is None and n >= depressed_at:
            tipping = float(st)
    return StressResponse(name=net.name, connectivity=net.connectivity,
                          curve=curve, tipping=tipping)


def tipping_stress(net: SymptomNetwork, **kw) -> Optional[float]:
    return stress_response(net, **kw).tipping


# ---------------------------------------------------------------------------
# study 2: hysteresis / spontaneous non-recovery
# ---------------------------------------------------------------------------

@dataclass
class NetworkHysteresis:
    name: str
    connectivity: float
    up_path: list                  # (stress, active)
    down_path: list
    triggers_at: Optional[float]
    releases_at: Optional[float]

    @property
    def width(self) -> float:
        if self.triggers_at is None:
            return 0.0
        if self.releases_at is None:
            return float("inf")
        return self.triggers_at - self.releases_at

    @property
    def spontaneous_nonrecovery(self) -> bool:
        """True only when lowering the stress all the way through the sweep --
        including to zero -- never lifts the episode: the network holds itself
        down with no help from the world. Mere hysteresis (releasing at a lower
        stress than triggered, `width > 0`) is the weaker claim that the
        depression OUTLIVES its cause; it is reported separately in render()."""
        return self.releases_at is None

    def render(self) -> str:
        from soma.viz import bar
        up = dict(self.up_path)
        down = dict(self.down_path)
        levels = sorted(set(up) | set(down), reverse=True)
        top = max(list(up.values()) + list(down.values()) + [1])
        rows = ["    stress   up sweep            down sweep"]
        for s in levels:
            u = (f"{bar(up[s] / top, 9)} {up[s]}" if s in up
                 else " " * 11)
            d = (f"{bar(down[s] / top, 9)} {down[s]}" if s in down
                 else "")
            tr = " <-triggers" if abs(s - self.triggers_at) < 1e-9 else ""
            rel = (" <-releases" if (self.releases_at is not None
                                     and abs(s - self.releases_at) < 1e-9)
                   else "")
            rows.append(f"    {s:>5g}    {u}{tr:<11}  {d}{rel}".rstrip())
        w = "∞" if self.width == float("inf") else f"{self.width:g}"
        head = (f"HYSTERESIS — {self.name} (connectivity {self.connectivity:g}):"
                + "\n" + "\n".join(rows) + "\n"
                f"  triggers at {self.triggers_at}, "
                + (f"never releases in range"
                   if self.releases_at is None else
                   f"releases at {self.releases_at:g}")
                + f" — the depression outlives its cause by {w}")
        if self.spontaneous_nonrecovery:
            head += ("\n  spontaneous non-recovery: removing the stressor does "
                     "NOT lift the depression — the network holds itself down.")
        elif self.width > 0:
            head += ("\n  hysteretic: lifting the stress below its trigger is "
                     "not enough — it\n  releases only at "
                     f"{self.releases_at:g}. The depression outlives its "
                     "cause.")
        else:
            head += ("\n  reversible: the symptoms clear when the stressor "
                     "does.")
        return head


def hysteresis_loop(net: SymptomNetwork, *, levels=(0, 1, 2, 3, 4),
                    dwell: int = 7, depressed_at: int = 5,
                    recovered_at: int = 2) -> NetworkHysteresis:
    """Ramp stress up through `levels` and back down in one continuous run,
    holding each level `dwell` beats, and read the active-symptom count at the
    end of each plateau. `triggers_at` is the first ascending stress reaching
    `depressed_at`; `releases_at` the first descending stress falling back to
    `recovered_at`."""
    levels = list(levels)
    seq = levels + list(reversed(levels[:-1]))
    schedule = {1 + i * dwell: v for i, v in enumerate(seq)}
    net2 = symptom_network(net.name, net.symptoms, net.edges,
                           connectivity=net.connectivity,
                           threshold=net.threshold, weights=net.weights,
                           thresholds=net.thresholds, relax=net.relax,
                           span=f"{len(seq) * dwell + 4}s", step=net.step)
    r = _run(net2, stress_schedule=schedule)
    reads = []
    for i, v in enumerate(seq):
        beat = min(len(r.times) - 1, i * dwell + dwell - 1)
        reads.append((float(v), _active_count(r, net2, at=beat)))
    up, down = reads[:len(levels)], reads[len(levels):]
    triggers = next((s for s, n in up if n >= depressed_at), None)
    releases = next((s for s, n in down if n <= recovered_at), None)
    return NetworkHysteresis(name=net.name, connectivity=net.connectivity,
                             up_path=up, down_path=down,
                             triggers_at=triggers, releases_at=releases)


# ---------------------------------------------------------------------------
# study 3: the forbidden zone
# ---------------------------------------------------------------------------

@dataclass
class EquilibriumModes:
    name: str
    connectivity: float
    counts: list                   # active-symptom count from each start
    histogram: dict                # count -> frequency
    n_symptoms: int = 9

    @property
    def forbidden_zone(self) -> tuple:
        """The widest run of active-symptom counts that never occurs at
        equilibrium -- the fold of the cusp, the states the person cannot be
        stably in."""
        present = set(self.histogram)
        if not present:
            return (0, 0)
        lo, hi = min(present), max(present)
        best = (0, -1)
        run_start = None
        for k in range(lo, hi + 1):
            if k not in present:
                if run_start is None:
                    run_start = k
            else:
                if run_start is not None:
                    if k - 1 - run_start > best[1] - best[0]:
                        best = (run_start, k - 1)
                    run_start = None
        return best if best[1] >= best[0] else (0, 0)

    @property
    def forbidden_width(self) -> int:
        lo, hi = self.forbidden_zone
        return max(0, hi - lo + 1) if hi >= lo else 0

    @property
    def bimodality(self) -> float:
        """The share of equilibria sitting at the two POLES (near-empty or
        near-full) rather than in the middle -- the cleanest read of the cusp
        catastrophe at this network size. Cramer's claim is that this rises
        with connectivity: a strongly connected person is depressed or well,
        rarely in between."""
        if not self.counts:
            return 0.0
        lo_pole = self.n_symptoms * 0.25
        hi_pole = self.n_symptoms * 0.75
        poles = sum(1 for c in self.counts if c <= lo_pole or c >= hi_pole)
        return poles / len(self.counts)

    @property
    def depressed_share(self) -> float:
        hi_pole = self.n_symptoms * 0.75
        return (sum(1 for c in self.counts if c >= hi_pole) / len(self.counts)
                if self.counts else 0.0)

    def render(self) -> str:
        top = max(self.histogram) if self.histogram else 0
        bars = "\n".join(
            f"    {k:>2} active: {'█' * self.histogram.get(k, 0)}"
            f"{' ' if self.histogram.get(k, 0) else ''}"
            f"{self.histogram.get(k, 0) or '·'}"
            for k in range(top + 1))
        return (f"EQUILIBRIUM MODES — {self.name} "
                f"(connectivity {self.connectivity:g}), across the transition "
                f"band:\n{bars}\n"
                f"  bimodality (share at the poles): {self.bimodality:.0%}; "
                f"depressed share: {self.depressed_share:.0%}\n"
                f"  a strongly connected person settles at an extreme — well "
                f"or depressed, rarely between.")


def equilibrium_modes(net: SymptomNetwork, *, samples: int = 60,
                      stress_band=(1.5, 3.5), seed: int = 0) -> EquilibriumModes:
    """From many random (initial symptom kick, stress level in `stress_band`)
    combinations, record the equilibrium active-symptom count. High
    connectivity concentrates the mass at the two poles (well / depressed) --
    the cusp catastrophe's bimodality -- and can open an empty middle (the
    forbidden zone). Sampling ACROSS the transition band, rather than at one
    stress, is what exposes the fold."""
    import random
    rng = random.Random(seed)
    counts = []
    for _ in range(samples):
        stress = rng.uniform(*stress_band)
        kick = rng.choice(net.symptoms)
        r = _run(net, stress_schedule=float(stress),
                 trigger=(kick, 1, rng.uniform(0.2, 1.0)))
        counts.append(_active_count(r, net))
    hist = {}
    for c in counts:
        hist[c] = hist.get(c, 0) + 1
    return EquilibriumModes(name=net.name, connectivity=net.connectivity,
                            counts=counts, histogram=hist,
                            n_symptoms=len(net.symptoms))


# ---------------------------------------------------------------------------
# intervention: which symptom to break
# ---------------------------------------------------------------------------

def target_symptom(net: SymptomNetwork, *, stress: float = 3.0,
                   depressed_at: int = 5) -> dict:
    """Which single symptom, if held OFF (its threshold raised out of reach),
    most reduces the equilibrium symptom count -- the network-theory answer to
    'what should treatment target'. Returns {symptom: active_count_without_it}
    plus the best target."""
    base = _active_count(_run(net, stress_schedule=stress), net)
    result = {}
    for s in net.symptoms:
        t2 = dict(net.thresholds)
        t2[s] = 99.0                       # unreachable: the symptom is disabled
        n2 = symptom_network(net.name, net.symptoms, net.edges,
                             connectivity=net.connectivity,
                             threshold=net.threshold, weights=net.weights,
                             thresholds=t2, relax=net.relax,
                             span=net.span, step=net.step)
        result[s] = _active_count(_run(n2, stress_schedule=stress), n2)
    best = min(result, key=result.get)
    return {"baseline": base, "per_symptom": result, "best_target": best,
            "best_result": result[best]}


# ---------------------------------------------------------------------------
# kindling: a life-course over the network (Post's sensitization model)
# ---------------------------------------------------------------------------

@dataclass
class KindlingReport:
    """A life-course of episodes and the stressors that triggered them. Post's
    kindling hypothesis (1992): with each depressive episode the threshold for
    the next falls, so successive episodes are triggered by ever-smaller
    stressors and eventually become AUTONOMOUS -- they arrive with no stressor
    at all. `episodes` records (episode_number, triggering_stress, threshold)."""
    name: str
    episodes: list                 # (n, trigger_stress, threshold_at_the_time)
    became_autonomous_at: Optional[int]
    sensitization: float           # per-episode drop in threshold

    def render(self) -> str:
        thr0 = max((thr for _, _, thr in self.episodes), default=1.0) or 1.0
        from soma.viz import bar
        rows = "\n".join(
            f"    episode {n}: triggered by stress {ts:g} "
            f"(threshold now {bar(thr / thr0, 10)} {thr:.2f})"
            + ("  <- AUTONOMOUS: no stressor needed" if ts <= 0.001 else "")
            for n, ts, thr in self.episodes)
        tail = (f"\n  became autonomous at episode {self.became_autonomous_at}: "
                f"the illness now recurs on its own."
                if self.became_autonomous_at
                else "\n  did not become autonomous in the life-course modelled.")
        return (f"KINDLING — {self.name}: the threshold falls "
                f"{self.sensitization:g} per episode\n{rows}{tail}")


def kindling(net: SymptomNetwork, *, episodes: int = 6,
             sensitization: float = 0.35, recovery_between: bool = True,
             depressed_at: int = 5, max_stress: float = 5.0,
             stress_step: float = 0.5) -> KindlingReport:
    """Model a life-course. For each episode, find the LEAST stressor that tips
    the (current) network into the depressed state; then, having had an
    episode, permanently lower the network's threshold by `sensitization`
    (Post's kindling). Over episodes the required trigger falls; when it
    reaches zero the episode is AUTONOMOUS -- the network tips with no stressor,
    the sensitization model's endpoint.

    Returns the trigger-per-episode curve, which is the kindling signature:
    early episodes need a real blow, late ones need almost nothing."""
    thr = net.threshold
    records, autonomous_at = [], None
    for n in range(1, episodes + 1):
        cur = symptom_network(net.name, net.symptoms, net.edges,
                              connectivity=net.connectivity, threshold=thr,
                              weights=net.weights, thresholds=net.thresholds,
                              relax=net.relax, span=net.span, step=net.step)
        # least stressor that triggers this episode (0 = autonomous)
        trigger = None
        st = 0.0
        while st <= max_stress + 1e-9:
            r = _run(cur, stress_schedule=st,
                     trigger=(net.symptoms[0], 2, 0.6) if st > 0 else None)
            if _active_count(r, cur) >= depressed_at:
                trigger = st
                break
            st += stress_step
        if trigger is None:
            trigger = max_stress + stress_step      # didn't tip even at max
        records.append((n, round(trigger, 3), round(thr, 3)))
        if trigger <= 0.001 and autonomous_at is None:
            autonomous_at = n
        # the episode leaves its mark: the threshold falls (kindling)
        thr -= sensitization
    return KindlingReport(name=net.name, episodes=records,
                          became_autonomous_at=autonomous_at,
                          sensitization=sensitization)
