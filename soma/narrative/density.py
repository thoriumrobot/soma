"""
soma.narrative.density -- a trait is the whole distribution (Whole Trait Theory).

Fleeson's experience-sampling result (JPSP 2001; Whole Trait Theory, Fleeson &
Jayawickreme 2015) reframed what a trait IS. Sampling people's states across
weeks of everyday life: (1) within-person variability is enormous -- the
typical person routinely manifests nearly every level of every trait; (2) the
MEAN of each person's distribution of states is almost perfectly stable -- that
mean is the classical trait score; and (3) the VARIABILITY (and skew) of the
distribution are THEMSELVES stable individual differences -- and the amount of
within-person variability reflects the person's REACTIVITY to trait-relevant
situational cues. A trait, in short, is a density distribution of states, and a
person is described by the whole distribution -- mean, spread, skew, range --
not by one number.

For a novelist this is a precise upgrade to "consistent characterization": a
character is not someone who always does the same thing (that is flatness); a
character is someone whose DISTRIBUTION of doings is stable. Two characters can
share a mean -- equally anxious "on average" -- and be utterly different
people: one narrow (the same low hum in every scene), one wide (serene at
breakfast, shattered by nightfall), and the width is the character.

This module samples the distribution the model implies. It probes the character
with `samples` randomized, unseen situations (strengths drawn uniformly over
[lo, hi] on a probe channel, via Story.probe -- the same stripped-timeline
machinery as `predict`), reads a STATE off each run, and returns the density:

  density(story, who, probe_channel)  -> DensityReport: mean (the trait score),
                                         sd (the person's width), skew, range,
                                         a histogram, and REACTIVITY -- the
                                         correlation between situation strength
                                         and state, which Fleeson showed the
                                         width reflects.

  compare(a, b)                       -> which distribution parameters separate
                                         two characters; in particular the
                                         Fleeson contrast: same mean, different
                                         width.

State measures (`measure=`):
  "arousal"  peak elevation of a body channel above its resting floor (default:
             heart) -- the physiological state the situation produced;
  "defense"  the fraction of firing settles routed `act` -- how much of the
             situation the character overrode rather than took in.

Falsifiability, as everywhere in the prediction layer: the distribution is a
claim about unseen inputs. Re-sample with a different seed and the parameters
must reproduce (stability of the density -- Fleeson's core finding); stage any
sampled situation in the story proper and the state must land where the
distribution says its kind of situation lands.
"""
from __future__ import annotations
from dataclasses import dataclass
import random
import math


# ---------------------------------------------------------------------------
# reading a state off one probe run
# ---------------------------------------------------------------------------

def _hist_for(result, who: str, channel: str):
    """Find a channel history, tolerant of character scoping."""
    h = result.channel_hist
    for key in (f"{who}.{channel}", channel):
        if key in h:
            return h[key]
    tail = "." + channel
    for k, v in h.items():
        if k.endswith(tail):
            return v
    return None


def _state_arousal(result, who, channel):
    ys = _hist_for(result, who, channel)
    if not ys:
        return 0.0
    floor = min(ys)
    return max(ys) - floor


def _state_defense(result, who, channel):
    name = who
    routes = []
    for e in result.chronicle:
        if e.kind != "settle":
            continue
        owner = e.who.split(".")[0] if "." in e.who else None
        if owner and owner != name:
            continue
        if abs(e.detail.get("error", 0.0)) > 0.5:
            routes.append(e.detail.get("route"))
    if not routes:
        return 0.0
    return routes.count("act") / len(routes)


_MEASURES = {"arousal": _state_arousal, "defense": _state_defense}


# ---------------------------------------------------------------------------
# the density report
# ---------------------------------------------------------------------------

_BLOCKS = " ▁▂▃▄▅▆▇█"

def _histogram(xs, bins=10):
    if not xs:
        return ""
    lo, hi = min(xs), max(xs)
    if hi - lo < 1e-12:
        return "█" * 1
    counts = [0] * bins
    for x in xs:
        i = min(bins - 1, int((x - lo) / (hi - lo) * bins))
        counts[i] += 1
    top = max(counts)
    return "".join(_BLOCKS[max(1, round(c / top * 8))] if c else _BLOCKS[0]
                   for c in counts)


def _skew(xs):
    n = len(xs)
    if n < 3:
        return 0.0
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / n)
    if sd < 1e-12:
        return 0.0
    return sum(((x - m) / sd) ** 3 for x in xs) / n


def _corr(xs, ys):
    n = len(xs)
    if n < 2:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if sx < 1e-12 or sy < 1e-12:
        return 0.0
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)


@dataclass
class DensityReport:
    """A character's trait, as Whole Trait Theory defines one: the whole
    density distribution of their states across situations, plus the
    reactivity that the width reflects."""
    who: str
    measure: str
    probe_channel: str
    states: list            # one state per sampled situation
    strengths: list         # the situation strength that produced each state

    @property
    def mean(self) -> float:
        return sum(self.states) / len(self.states) if self.states else 0.0

    @property
    def sd(self) -> float:
        n = len(self.states)
        if n < 2:
            return 0.0
        m = self.mean
        return math.sqrt(sum((x - m) ** 2 for x in self.states) / n)

    @property
    def skew(self) -> float:
        return _skew(self.states)

    @property
    def spread(self) -> tuple:
        return (min(self.states), max(self.states)) if self.states else (0.0, 0.0)

    @property
    def reactivity(self) -> float:
        """Correlation between situation strength and state -- Fleeson's
        account of what within-person variability IS: differential reactivity
        to trait-relevant situational cues."""
        return _corr(self.strengths, self.states)

    def render(self) -> str:
        lo, hi = self.spread
        return (f"Density -- {self.who}, {self.measure} across {len(self.states)} "
                f"unseen situations on '{self.probe_channel}':\n"
                f"  {_histogram(self.states)}\n"
                f"  mean {self.mean:.2f} (the trait score)   sd {self.sd:.2f} "
                f"(the width -- itself a trait)   skew {self.skew:+.2f}\n"
                f"  range [{lo:.2f}, {hi:.2f}]   reactivity to the cue "
                f"{self.reactivity:+.2f}")


def density(story, who, probe_channel: str, *, measure: str = "arousal",
            state_channel: str = "heart", samples: int = 24, beats: int = 6,
            lo: float = 0.0, hi: float = 9.0, seed: int = 0) -> DensityReport:
    """Sample the character's density distribution of states over `samples`
    randomized, unseen situations on `probe_channel`."""
    if measure not in _MEASURES:
        raise ValueError(f"measure must be one of {sorted(_MEASURES)}")
    name = who.name if hasattr(who, "name") else who
    rng = random.Random(seed)
    read = _MEASURES[measure]
    states, strengths = [], []
    for _ in range(samples):
        v = rng.uniform(lo, hi)
        r = story.probe(name, {probe_channel: v}, beats=beats)
        states.append(read(r, name, state_channel))
        strengths.append(v)
    return DensityReport(who=name, measure=measure, probe_channel=probe_channel,
                         states=states, strengths=strengths)


def compare(a: DensityReport, b: DensityReport, *, tol_mean: float = None,
            tol_sd: float = None) -> dict:
    """Which distribution parameters separate two characters. Tolerances
    default to 15% of the larger spread, so 'same' means 'same at the scale of
    the phenomenon'. The Fleeson contrast to look for: same_mean=True with
    same_width=False -- two people identical as trait scores and different as
    people."""
    scale = max(a.spread[1] - a.spread[0], b.spread[1] - b.spread[0], 1e-9)
    tol_mean = 0.15 * scale if tol_mean is None else tol_mean
    tol_sd = 0.15 * scale if tol_sd is None else tol_sd
    return {
        "same_mean": abs(a.mean - b.mean) <= tol_mean,
        "same_width": abs(a.sd - b.sd) <= tol_sd,
        "mean": (round(a.mean, 3), round(b.mean, 3)),
        "sd": (round(a.sd, 3), round(b.sd, 3)),
        "skew": (round(a.skew, 3), round(b.skew, 3)),
        "reactivity": (round(a.reactivity, 3), round(b.reactivity, 3)),
        "wider": a.who if a.sd > b.sd else b.who,
    }
