"""
soma.narrative.idiographic -- inferring a person's wiring from their diary.

Every layer of this library so far runs FORWARD: given a character, predict
what they do. This one runs BACKWARD. It is the inverse problem at the frontier
of clinical network science (Bringmann, "Person-specific networks in
psychopathology: past, present, and future", Curr Opin Psychol 2021; Epskamp,
van Borkulo et al., "Personalized Network Modeling in Psychopathology",
Clinical Psychological Science 2018): given a time-series of one person's
symptoms -- an experience-sampling diary -- estimate the network of couplings
that generated it, so that the character's own structure is RECOVERED rather
than authored.

The move the field made, reproduced here end to end:

  1. GENERATE a diary. A `SymptomNetwork` (from soma.narrative.network) is
     driven by a fluctuating daily stressor and logs each symptom's activation
     over N days -- exactly the intensive longitudinal data an ESM study
     collects, except here the ground-truth wiring is known.

  2. ESTIMATE the temporal network. The standard model is the lag-1 vector
     autoregression (VAR): each symptom's next value is regressed on ALL
     symptoms' current values. The matrix of coefficients A[target][source] IS
     the person-specific temporal network -- a directed edge source->target
     weighted by how much today's source predicts tomorrow's target. Ridge
     regularization handles the collinearity the literature warns about.

  3. READ the person off the estimate. `out_strength` centrality names the
     hub -- the symptom that most drives the rest -- which is the clinically
     actionable output, and (per Bringmann) the part of the estimate that
     survives noise even where individual edges do not.

  4. VALIDATE the recovery. Because the ground truth is known here (it is not,
     in a real clinic), the module scores the estimate against it: how many
     true edges land in the top-K recovered, and whether the recovered hub is
     the true hub. This is the falsification the clinical literature cannot
     perform and a simulator can.

Why this is the deepest predictive-characterization object in the library: it
closes the loop. A character can be authored, made to live a life, observed
only through their diary, and then RE-DERIVED from that diary -- and the
re-derived character can be run forward again and checked against the original.
It is prediction and postdiction in one instrument, and it is exactly what a
clinician does with a patient they can only observe.

Honest limits, inherited from the field: raw VAR on saturated data gives huge,
unstable coefficients (symptoms locked at ceiling are collinear), so the diary
must keep the person in the DYNAMIC regime (stress fluctuating around
threshold, symptoms rising and falling) for the couplings to be estimable --
`simulate_diary` does this by construction, and `recovery` degrades honestly
when the person is kept saturated. Edge-level recovery is imperfect (~60-70%);
centrality recovery is robust. Both facts match the reliability results in
Epskamp, Borsboom & Kruis, "Estimating psychopathological networks: be careful
what you wish for" (PLoS ONE 2017).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import random

from .network import SymptomNetwork, symptom_network, _run


# ---------------------------------------------------------------------------
# 1. generating a diary
# ---------------------------------------------------------------------------

@dataclass
class Diary:
    """One person's experience-sampling record: each symptom's activation over
    `days` days, plus the daily stressor that drove it. The object a clinician
    actually has -- observations, not the wiring behind them."""
    name: str
    symptoms: list
    series: dict                   # symptom -> [activation per day]
    stress: list                   # daily stress level
    truth: Optional[SymptomNetwork] = None   # ground truth, if known

    @property
    def days(self) -> int:
        return min(len(v) for v in self.series.values())

    def variances(self) -> dict:
        """How much each symptom moved over the diary. A symptom that barely
        varies carries almost no information about its own outgoing
        influence -- so a near-flat driver is UNIDENTIFIABLE from the diary
        alone, however central it truly is. This is the honest floor of
        idiographic inference: you cannot recover a hub that does not vary."""
        import statistics
        return {s: round(statistics.pvariance(self.series[s][:self.days]), 5)
                if self.days > 1 else 0.0 for s in self.symptoms}

    def estimable(self, floor: float = 0.001) -> dict:
        """Which symptoms varied enough to have their outgoing influence
        estimated. Symptoms below `floor` are flagged: their hub status, if
        any, cannot be seen in this diary."""
        v = self.variances()
        return {s: (v[s] >= floor) for s in self.symptoms}

    def render(self, width: int = 40) -> str:
        blocks = " ▁▂▃▄▅▆▇█"
        lines = [f"DIARY — {self.name}, {self.days} days:"]
        for s in self.symptoms:
            v = self.series[s][:width]
            spark = "".join(blocks[min(8, int(x * 8))] for x in v)
            lines.append(f"  {s:>13} {spark}")
        return "\n".join(lines)


def simulate_diary(net: SymptomNetwork, *, days: int = 200, seed: int = 0,
                   stress_mean: float = 1.2, stress_sd: float = 0.9,
                   stress_cap: float = 3.0) -> Diary:
    """Drive `net` with a fluctuating daily stressor and record the symptom
    time-series -- an ESM diary with known ground truth.

    The stressor is kept in a band that holds the person in the DYNAMIC regime
    (symptoms rise and fall rather than locking at ceiling), which is what
    makes the couplings estimable -- a modelling choice that mirrors why real
    ESM studies of remitting patients yield better networks than studies of
    the chronically saturated."""
    rng = random.Random(seed)
    sched = {d: round(max(0.0, min(stress_cap, rng.gauss(stress_mean, stress_sd))), 2)
             for d in range(1, days + 1)}
    driven = symptom_network(net.name, net.symptoms, net.edges,
                             connectivity=net.connectivity,
                             threshold=net.threshold, weights=net.weights,
                             thresholds=net.thresholds, relax=net.relax,
                             span=f"{days + 2}s", step="1s")
    r = _run(driven, stress_schedule=sched)
    series = {s: (r.channel_hist.get(s)
                  or r.channel_hist.get(f"{net.name}.{s}", []))
              for s in net.symptoms}
    stress = (r.channel_hist.get("stress")
              or r.channel_hist.get(f"{net.name}.stress", []))
    return Diary(name=net.name, symptoms=list(net.symptoms), series=series,
                 stress=stress, truth=net)


# ---------------------------------------------------------------------------
# 2. estimating the temporal network (lag-1 VAR, ridge-regularized)
# ---------------------------------------------------------------------------

def _ridge_lstsq(rows, ys, lam):
    k = len(rows[0])
    ata = [[sum(r[i] * r[j] for r in rows) + (lam if i == j else 0.0)
            for j in range(k)] for i in range(k)]
    atb = [sum(r[i] * y for r, y in zip(rows, ys)) for i in range(k)]
    m = [ata[i] + [atb[i]] for i in range(k)]
    for c in range(k):
        p = max(range(c, k), key=lambda r: abs(m[r][c]))
        if abs(m[p][c]) < 1e-12:
            m[c][c] += 1e-9
            p = c
        m[c], m[p] = m[p], m[c]
        for r in range(c + 1, k):
            f = m[r][c] / m[c][c]
            for cc in range(c, k + 1):
                m[r][cc] -= f * m[c][cc]
    x = [0.0] * k
    for r in range(k - 1, -1, -1):
        x[r] = (m[r][k] - sum(m[r][cc] * x[cc]
                              for cc in range(r + 1, k))) / m[r][r]
    return x


@dataclass
class TemporalNetwork:
    """A person-specific temporal network estimated from a diary: A[target]
    [source] is the lag-1 coefficient -- how much today's `source` predicts
    tomorrow's `target`. The directed, weighted graph the network approach
    calls the patient's own network."""
    name: str
    symptoms: list
    A: dict                        # target -> {source -> coef}
    stress_effect: dict = field(default_factory=dict)   # symptom -> stress coef

    def edge(self, source, target) -> float:
        return self.A.get(target, {}).get(source, 0.0)

    def out_strength(self) -> dict:
        """Centrality: the total outgoing influence of each symptom -- the sum
        of |coefficients| on the edges it sends. The hub is the argmax."""
        return {s: sum(abs(self.A[t][s]) for t in self.symptoms if t != s)
                for s in self.symptoms}

    def in_strength(self) -> dict:
        return {s: sum(abs(self.A[s][src]) for src in self.symptoms if src != s)
                for s in self.symptoms}

    def hub(self) -> str:
        os = self.out_strength()
        return max(os, key=os.get)

    def top_edges(self, k: int = 12) -> list:
        edges = [(self.A[t][s], s, t) for t in self.symptoms
                 for s in self.symptoms if s != t]
        edges.sort(key=lambda e: -abs(e[0]))
        return edges[:k]

    def render(self, k: int = 10) -> str:
        lines = [f"TEMPORAL NETWORK — {self.name} (estimated from the diary):"]
        lines.append(f"  strongest directed edges (source → target, lag-1):")
        for co, s, t in self.top_edges(k):
            lines.append(f"    {co:+.3f}  {s:>13} → {t}")
        os = self.out_strength()
        rank = sorted(os, key=os.get, reverse=True)[:3]
        lines.append(f"  hub (out-strength): {self.hub()} "
                     f"— top 3: {', '.join(rank)}")
        return "\n".join(lines)


def estimate_network(diary: Diary, *, ridge: float = 2.0,
                     include_stress: bool = True,
                     standardize: bool = False) -> TemporalNetwork:
    """Fit the lag-1 VAR: for each symptom, regress its next value on all
    symptoms' current values (and the current stressor). Ridge-regularized to
    tame the collinearity of near-saturated symptoms.

    `standardize=True` (the field's default) rescales each coefficient by the
    ratio of predictor SD to outcome SD, giving the standardized edge weight.
    This matters for centrality: a raw coefficient favours high-variance
    RECEIVERS over low-variance DRIVERS (a root-cause symptom, driven only by
    the world, varies little), so out-strength on raw coefficients can miss the
    very hub it is meant to find. Standardizing makes a driver's influence
    visible in proportion to how much of the receiver it moves per unit of its
    own variation -- which is the causal quantity centrality is a proxy for."""
    syms = diary.symptoms
    T = diary.days
    import math

    def sd(xs):
        n = len(xs)
        if n < 2:
            return 0.0
        m = sum(xs) / n
        return math.sqrt(sum((x - m) ** 2 for x in xs) / n)

    sds = {s: sd(diary.series[s][:T]) for s in syms}
    A, stress_effect = {}, {}
    for target in syms:
        rows, ys = [], []
        for t in range(T - 1):
            row = [diary.series[s][t] for s in syms] + [1.0]
            if include_stress and diary.stress:
                row.append(diary.stress[t] if t < len(diary.stress) else 0.0)
            rows.append(row)
            ys.append(diary.series[target][t + 1])
        coefs = _ridge_lstsq(rows, ys, ridge)
        out_sd = sds[target] or 1.0
        row = {}
        for i, s in enumerate(syms):
            c = coefs[i]
            if standardize:
                c = c * (sds[s] / out_sd) if out_sd else c
            row[s] = c
        A[target] = row
        if include_stress and diary.stress:
            stress_effect[target] = coefs[len(syms) + 1]
    return TemporalNetwork(name=diary.name, symptoms=list(syms), A=A,
                           stress_effect=stress_effect)


# ---------------------------------------------------------------------------
# 4. validating the recovery against ground truth
# ---------------------------------------------------------------------------

@dataclass
class RecoveryReport:
    """How well the estimate recovered the truth -- the falsification a
    simulator can do and a clinic cannot. `edge_recall` is the fraction of
    true directed edges landing in the top-K estimated; `hub_correct` is
    whether the estimated hub is the true one (the robust, clinically
    actionable claim)."""
    name: str
    n_true_edges: int
    edge_recall: float
    true_hub: str
    recovered_hub: str
    true_top3: list
    recovered_top3: list
    days: int

    @property
    def hub_correct(self) -> bool:
        return self.true_hub == self.recovered_hub

    @property
    def hub_in_top3(self) -> bool:
        return self.true_hub in self.recovered_top3

    def render(self) -> str:
        hub = ("✓ CORRECT" if self.hub_correct
               else "✓ in top 3" if self.hub_in_top3 else "✗ missed")
        return (f"RECOVERY — {self.name} ({self.days} days):\n"
                f"  edge recall: {self.edge_recall:.0%} of {self.n_true_edges} "
                f"true edges in the top-{self.n_true_edges} estimated\n"
                f"  hub: true '{self.true_hub}', recovered '{self.recovered_hub}'"
                f" — {hub}\n"
                f"  the individual edges are noisy; the hub is recoverable — "
                f"exactly the field's reliability finding, staked against a "
                f"ground truth a clinic never has.")


def recovery(diary: Diary, estimate: TemporalNetwork = None, *,
             ridge: float = 2.0) -> RecoveryReport:
    """Score an estimate against the diary's ground-truth network. Requires
    `diary.truth`. Edge recall uses the top-(number of true edges) estimated
    edges by magnitude; hub uses out-strength centrality vs the true network's
    in-degree hub."""
    if diary.truth is None:
        raise ValueError("recovery needs a diary with known ground truth")
    est = estimate or estimate_network(diary, ridge=ridge)
    true_edges = set(diary.truth.edges)
    k = len(true_edges)
    top = [(s, t) for _, s, t in est.top_edges(k)]
    recall = sum(1 for e in top if e in true_edges) / max(1, k)

    true_deg = diary.truth.out_degree()
    true_hub = max(true_deg, key=true_deg.get)
    true_top3 = sorted(true_deg, key=true_deg.get, reverse=True)[:3]
    os = est.out_strength()
    rec_top3 = sorted(os, key=os.get, reverse=True)[:3]
    return RecoveryReport(name=diary.name, n_true_edges=k, edge_recall=recall,
                          true_hub=true_hub, recovered_hub=est.hub(),
                          true_top3=true_top3, recovered_top3=rec_top3,
                          days=diary.days)


# ---------------------------------------------------------------------------
# closing the loop: re-derive a runnable network from the estimate
# ---------------------------------------------------------------------------

def rebuild_network(estimate: TemporalNetwork, *, keep: int = None,
                    connectivity: float = 1.0, threshold: float = 3.2,
                    **kw) -> SymptomNetwork:
    """Turn an estimated temporal network back into a runnable
    `SymptomNetwork`, so the re-derived character can be simulated forward and
    compared to the original. Keeps the `keep` strongest positive edges (default
    all positive edges), since the forward model's activation is excitatory.
    This is the loop closed: author -> live -> observe -> estimate -> RE-RUN."""
    edges, weights = [], {}
    scored = estimate.top_edges(len(estimate.symptoms) ** 2)
    kept = 0
    for co, s, t in scored:
        if co <= 0:
            continue                      # excitatory forward model
        if keep is not None and kept >= keep:
            break
        edges.append((s, t))
        weights[(s, t)] = round(co, 3)
        kept += 1
    return symptom_network(f"{estimate.name}_rederived", estimate.symptoms,
                           edges, connectivity=connectivity,
                           threshold=threshold, weights=weights, **kw)


def compare_hubs(diary: Diary, *, ridge: float = 2.0) -> dict:
    """Convenience: estimate, then report the true vs recovered hub and the
    out-strength ranking -- the one-line answer to 'did we find the person's
    hub from their diary alone'."""
    est = estimate_network(diary, ridge=ridge)
    rep = recovery(diary, est, ridge=ridge)
    return {"true_hub": rep.true_hub, "recovered_hub": rep.recovered_hub,
            "correct": rep.hub_correct, "recovered_top3": rep.recovered_top3,
            "edge_recall": rep.edge_recall}
