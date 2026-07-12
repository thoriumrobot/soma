"""
soma.narrative.futures -- ensemble forecasting: the distribution over endings.

A counterfactual study (soma.narrative.counterfactual) asks: what one change
turns THIS ending? An ensemble study asks the deeper question weather and
climate prediction settled on decades ago: across the cloud of NEARBY WORLDS --
the same people, the dials each nudged within their plausible range -- what is
the DISTRIBUTION over endings? A fate that holds in 95% of nearby worlds is a
character's nature; a fate that holds in 55% is a coin the story flips, and
the difference between those two marriages is invisible to any single run.
Scheffer's resilience language gives the same idea a landscape reading: the
probability of an ending is the measure of its basin under parameter
uncertainty.

  futures(story, dials, classify)  run `samples` replicates, each with every
                                   dial drawn uniformly from its range (via the
                                   perturb grammar -- anything perturb can
                                   move), classify each Result into a named
                                   ending, and return the probability
                                   distribution: P(each ending), the modal
                                   fate, ENTROPY (how settled the fate is, 0 =
                                   destiny, 1 = a coin), and per-run records.

  pivotal(report)                  which dial DECIDES the fate: for each dial,
                                   the standardized separation between its
                                   values in the modal-ending worlds and the
                                   rest (Cohen's d). The dial with the largest
                                   |d| is the hinge of the story -- computed,
                                   not asserted.

  dose_response(factory, doses,    the probabilistic deepening of "the smallest
                classify)          change that saves it": for each dose of an
                                   intervention (the factory builds the story
                                   at that dose), an ensemble estimates
                                   P(target ending); the curve is the
                                   intervention's dose-response, and
                                   `minimal_dose` is the least dose whose
                                   P(target) clears a threshold. One
                                   counterfactual run says "this day would have
                                   saved them"; the dose-response says "a day
                                   this good saves 8 marriages in 10, and a
                                   lesser day saves almost none" -- which is a
                                   different, and truer, sentence.

Classifiers are plain callables Result -> str, so any outcome the insight
vocabulary can read (a break, a route fraction, a mood drift) can name an
ending; `by_outcome` builds the common threshold classifiers.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
import random

from .insight import run_with, outcome


# ---------------------------------------------------------------------------
# classifiers
# ---------------------------------------------------------------------------

def by_outcome(name: str, *, above: float = None, below: float = None,
               labels=("yes", "no"), **kw):
    """A threshold classifier over the insight outcome vocabulary:
    by_outcome("perceive_frac", above=0.5, labels=("open", "armored"),
    character="Soren")."""
    if (above is None) == (below is None):
        raise ValueError("give exactly one of above=/below=")
    def classify(result):
        v = outcome(result, name, **kw)
        hit = (v >= above) if above is not None else (v <= below)
        return labels[0] if hit else labels[1]
    return classify


def by_break(labels=("seen", "kept")):
    """Ending named by whether any lie broke (a revelation was logged)."""
    def classify(result):
        return labels[0] if outcome(result, "break") > 0 else labels[1]
    return classify


# ---------------------------------------------------------------------------
# the ensemble
# ---------------------------------------------------------------------------

@dataclass
class FuturesReport:
    title: str
    dials: dict                 # dial -> (lo, hi)
    runs: list                  # per replicate: {"dials": {...}, "ending": str}
    endings: dict               # ending -> probability

    @property
    def modal(self) -> str:
        return max(self.endings, key=self.endings.get)

    @property
    def entropy(self) -> float:
        """How settled the fate is, normalized to [0, 1]: 0 = every nearby
        world ends the same way (destiny); 1 = the endings are equiprobable
        (a coin)."""
        ps = [p for p in self.endings.values() if p > 0]
        if len(ps) <= 1:
            return 0.0
        h = -sum(p * math.log(p) for p in ps)
        return h / math.log(len(ps))

    def p(self, ending: str) -> float:
        return self.endings.get(ending, 0.0)

    def render(self) -> str:
        n = len(self.runs)
        lines = [f"FUTURES — {self.title}: {n} nearby worlds"]
        width = 26
        for e, p in sorted(self.endings.items(), key=lambda kv: -kv[1]):
            bar = "█" * max(1, round(p * width))
            lines.append(f"  {e:<14} {bar:<{width}} {p:.0%}")
        lines.append(f"  modal fate: '{self.modal}'   settledness: "
                     f"{'destiny' if self.entropy < 0.35 else 'a coin' if self.entropy > 0.85 else 'contested'}"
                     f" (entropy {self.entropy:.2f})")
        return "\n".join(lines)


def futures(story, dials: dict, classify, *, samples: int = 40,
            seed: int = 0, base_overrides: dict = None) -> FuturesReport:
    """Run the ensemble: each replicate draws every dial uniformly from its
    (lo, hi) range, applies it through the perturb grammar, runs once, and is
    classified into an ending."""
    rng = random.Random(seed)
    runs = []
    for _ in range(samples):
        draw = {d: round(rng.uniform(lo, hi), 4)
                for d, (lo, hi) in dials.items()}
        ov = dict(base_overrides or {})
        ov.update(draw)
        r = run_with(story, ov)
        runs.append({"dials": draw, "ending": classify(r)})
    counts = {}
    for rec in runs:
        counts[rec["ending"]] = counts.get(rec["ending"], 0) + 1
    endings = {e: c / samples for e, c in counts.items()}
    return FuturesReport(title=story.title, dials=dict(dials), runs=runs,
                         endings=endings)


def pivotal(report: FuturesReport) -> list:
    """Which dial decides the fate: for each dial, Cohen's d between its
    values in the modal-ending worlds and all other worlds. Returns
    [(dial, d)] sorted by |d| descending -- the top entry is the hinge."""
    modal = report.modal
    out = []
    for dial in report.dials:
        xs = [r["dials"][dial] for r in report.runs if r["ending"] == modal]
        ys = [r["dials"][dial] for r in report.runs if r["ending"] != modal]
        if not xs or not ys:
            out.append((dial, 0.0))
            continue
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        vx = sum((x - mx) ** 2 for x in xs) / max(1, len(xs) - 1)
        vy = sum((y - my) ** 2 for y in ys) / max(1, len(ys) - 1)
        sp = math.sqrt(((len(xs) - 1) * vx + (len(ys) - 1) * vy)
                       / max(1, len(xs) + len(ys) - 2))
        out.append((dial, round((mx - my) / sp, 3) if sp > 1e-12 else 0.0))
    return sorted(out, key=lambda kv: -abs(kv[1]))


# ---------------------------------------------------------------------------
# dose-response of an intervention
# ---------------------------------------------------------------------------

@dataclass
class DoseResponse:
    intervention: str
    target: str
    curve: list                 # (dose, P(target))
    p_min: float
    minimal_dose: object        # least dose with P >= p_min, or None

    def render(self) -> str:
        rows = "\n".join(
            f"    dose {d}: P({self.target}) = {p:.0%} "
            + "█" * max(0, round(p * 20)) for d, p in self.curve)
        tail = (f"\n    minimal effective dose: {self.minimal_dose} "
                f"(first P ≥ {self.p_min:.0%})" if self.minimal_dose is not None
                else f"\n    NO dose in range reaches P ≥ {self.p_min:.0%}.")
        return (f"DOSE-RESPONSE — {self.intervention} vs "
                f"'{self.target}':\n{rows}{tail}")


def dose_response(factory, doses, classify=None, *, target: str,
                  dials: dict = None, samples: int = 12, seed: int = 0,
                  p_min: float = 0.75, intervention: str = "intervention",
                  classify_at=None) -> DoseResponse:
    """For each dose, `factory(dose)` builds the story with the intervention at
    that strength; an ensemble (over `dials` jitter, or a single run each if
    dials is None) estimates P(target ending). Returns the curve and the
    minimal effective dose -- the probabilistic form of `the smallest change
    that would have saved it`. Pass doses in the order that makes "minimal"
    meaningful for the intervention (ascending strength; or DESCENDING year,
    when the dose is a timing and the question is the latest safe moment).

    `classify_at(dose) -> classifier` builds a dose-dependent classifier (an
    ending defined relative to the intervention itself, e.g. "reaches him in
    the year the day lands"); otherwise `classify` is used for every dose."""
    curve = []
    minimal = None
    for i, dose in enumerate(doses):
        story = factory(dose)
        if classify_at is not None:
            classify = classify_at(dose)
        if dials:
            rep = futures(story, dials, classify, samples=samples,
                          seed=seed + i)
            p = rep.p(target)
        else:
            p = 1.0 if classify(run_with(story)) == target else 0.0
        curve.append((dose, round(p, 3)))
        if minimal is None and p >= p_min:
            minimal = dose
    return DoseResponse(intervention=intervention, target=target,
                        curve=curve, p_min=p_min, minimal_dose=minimal)
