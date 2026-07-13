"""
soma.narrative.sensitivity -- which dial actually writes the character.

A simulation with a dozen parameters invites a false kind of understanding: the
author changes one, sees the ending change, and concludes that dial *is* the
character. But a local change at one operating point says nothing about whether
that dial matters across the range the character might have lived, or whether
its apparent effect is really an interaction with another dial held fixed.

Global sensitivity analysis answers the honest version of the question. The
variance-based (Sobol) framework decomposes the variance of an outcome into the
fractions attributable to each input and to their interactions: the first-order
index S_i is the fraction of output variance removed if input i were fixed; the
total index S_Ti is the fraction remaining attributable to i once every
interaction it participates in is counted. A dial with a large total but small
first-order index matters only in concert with others -- which, for a character,
is the difference between a trait and a *contingency*. That distinction is the
insight this module is built to surface.

We estimate the indices by the Saltelli/pick-freeze scheme over Latin-hypercube
samples, using SOMA runs as the model evaluations. Because a SOMA character has
few dials and each run is milliseconds, a few hundred evaluations give stable
rankings -- and the ranking, not the third decimal place, is the point:

    study = story.sensitivity(
        outcome="break_time", character="Ink",
        params={"the_lie_...conviction": (0.3, 0.99),
                "the_lie_...learn":       (0.02, 0.3),
                "the_lie_...overwhelm":   (2.0, 12.0)})
    print(study.render())   # ranks the dials by how much they write the ending
"""
from __future__ import annotations
from dataclasses import dataclass, field
import random

from .insight import run_with, outcome


@dataclass
class SensitivityReport:
    outcome_name: str
    character: str
    first_order: dict          # param -> S_i (fraction of variance, main effect)
    total_order: dict          # param -> S_Ti (with interactions)
    base_variance: float
    n_runs: int
    notes: list = field(default_factory=list)

    def ranked(self):
        return sorted(self.total_order.items(), key=lambda kv: -kv[1])

    def render(self) -> str:
        lines = [f"SENSITIVITY of '{self.outcome_name}'"
                 + (f" ({self.character})" if self.character else "")
                 + f" — variance-based, {self.n_runs} runs"]
        if self.base_variance < 1e-9:
            lines.append("  outcome did not vary across the sampled space — "
                         "no dial in this range writes this ending.")
            return "\n".join(lines)
        lines.append("  dial                                  main   total"
                     "              reading")
        from soma.viz import bar
        for p, st in self.ranked():
            si = self.first_order.get(p, 0.0)
            parts = p.split(".")
            short = ".".join(parts[-2:]) if len(parts) >= 2 else p
            if len(short) > 34:
                short = "…" + short[-33:]
            if st < 0.05:
                reading = "inert here"
            elif si >= 0.75 * st:
                reading = "acts on its own"
            elif si < 0.4 * st:
                reading = "acts through interaction"
            else:
                reading = "mixed"
            lines.append(f"  {short:<36s} {si:5.2f}  {st:5.2f} "
                         f"{bar(st, 10)}  {reading}")
        for n in self.notes:
            lines.append(f"  ({n})")
        return "\n".join(lines)


def _sample(bounds, rng):
    return {p: rng.uniform(lo, hi) for p, (lo, hi) in bounds.items()}


def sensitivity(story, *, outcome_name: str = "break_time", params: dict,
                character=None, channel="heart", mood=None, quale=None,
                n_base: int = 64, seed: int = 0):
    """Estimate first- and total-order Sobol indices of `params` on an outcome.

    params      : {dial_name: (lo, hi)} over the perturb grammar (loop.field, etc.)
    outcome_name: an outcome understood by insight.outcome (default "break_time")

    Uses the Saltelli pick-freeze estimator: draw two independent sample
    matrices A and B of size n_base, then for each parameter i build A_B^{(i)}
    (A with column i taken from B) and run it. Total model runs ~ n_base*(k+2).
    """
    name = outcome_name
    rng = random.Random(seed)
    keys = list(params)
    k = len(keys)

    def ev(sample):
        r = run_with(story, sample)
        return outcome(r, name, character=character, channel=channel,
                       mood=mood, quale=quale)

    A = [_sample(params, rng) for _ in range(n_base)]
    B = [_sample(params, rng) for _ in range(n_base)]
    yA = [ev(a) for a in A]
    yB = [ev(b) for b in B]

    # replace non-finite outcomes (e.g. break_time = inf for "never") with a
    # finite sentinel just past the horizon, so variance is well defined and
    # "never breaks" is an extreme value rather than a NaN.
    horizon = _finite_horizon(yA + yB)
    yA = [horizon if v == float("inf") else v for v in yA]
    yB = [horizon if v == float("inf") else v for v in yB]

    n = len(yA)
    f0 = sum(yA) / n
    varY = sum((v - f0) ** 2 for v in yA) / n
    if varY < 1e-12:
        return SensitivityReport(name, character or "", {p: 0.0 for p in keys},
                                 {p: 0.0 for p in keys}, varY,
                                 n_base * (k + 2),
                                 notes=["outcome constant across the space"])

    first, total = {}, {}
    for i, key in enumerate(keys):
        ABi = []
        for a, b in zip(A, B):
            row = dict(a)
            row[key] = b[key]
            ABi.append(row)
        yABi = [ev(r) for r in ABi]
        yABi = [horizon if v == float("inf") else v for v in yABi]
        # Jansen (1999) estimators, robust variants of Sobol/Saltelli
        s_i = 0.0
        t_i = 0.0
        for j in range(n):
            s_i += yB[j] * (yABi[j] - yA[j])
            t_i += (yA[j] - yABi[j]) ** 2
        first[key] = max(0.0, (s_i / n) / varY)
        # total-order is a fraction of variance and is bounded in [0, 1] by
        # definition; the Jansen estimator can overshoot with small samples or
        # strong interactions, so clamp to 1 (a value > 1 is not meaningful and
        # only confuses the reading).
        total[key] = min(1.0, max(0.0, (t_i / (2 * n)) / varY))

    # clamp first-order to total (estimator noise can invert them slightly)
    for key in keys:
        first[key] = min(first[key], total[key])
    notes = ["main = variance removed if this dial were fixed; "
             "total = variance attributable to it including interactions"]
    return SensitivityReport(name, character or "", first, total, varY,
                             n_base * (k + 2), notes=notes)


def _finite_horizon(values):
    finite = [v for v in values if v != float("inf")]
    if not finite:
        return 1.0
    return max(finite) + (max(finite) - min(finite) + 1.0)
