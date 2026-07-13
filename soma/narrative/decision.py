"""
soma.narrative.decision -- how long a choice takes, and how often it is wrong.

Every SOMA layer so far predicts what a character feels or becomes. This one
predicts something orthogonal and, in the lab, more precisely measured than any
of them: the TIME a decision takes and the RATE at which it errs. The
drift-diffusion model (Ratcliff 1978; Ratcliff & McKoon 2008; Gold & Shadlen)
is the dominant account of speeded two-choice decisions and one of the great
successes of mathematical psychology -- it fits full reaction-time
distributions AND accuracy at once, from four interpretable parameters:

  drift rate v        the quality of the evidence -- how fast, on average, the
                      accumulator is pushed toward the correct boundary. High v:
                      easy decision, fast and accurate.
  boundary a          how much evidence is required before committing. This is
                      the SPEED-ACCURACY DIAL: wide boundaries -> slow but
                      accurate; narrow -> fast but error-prone.
  start point z       prior bias toward one choice (a proportion of a).
  non-decision t0     encoding + motor time, added to every response.

A decision is a noisy walk: evidence accumulates from z with mean step v and
random jitter, until it crosses 0 (the wrong choice) or a (the right one). The
model's signature predictions -- the ones a deterministic or single-number
account cannot make -- are DISTRIBUTIONAL: right-skewed RT distributions, error
responses systematically different from correct ones, and above all the
speed-accuracy tradeoff traced out by moving the boundary alone.

This is also where SOMA gains a faculty it lacked: STOCHASTICITY. The base
interpreter is deterministic by design, and everything built so far relies on
that. So the noise lives here, in a seeded driver, opt-in and reproducible: the
same seed gives the same RT distribution every time, and nothing in the
deterministic core changes. The accumulator is Clark's arithmetic on SOMA's own
terms -- momentary evidence is a precision-weighted prediction error, drift is
its mean, the boundary is an overwhelm-style bound -- but run many times with
jitter to yield the distribution the DDM is famous for.

    thinker = story.decides("Juror", drift=0.15, boundary=1.0)
    report = story.predict_decision("Juror", trials=2000, seed=0)
    report.mean_rt, report.accuracy
    sat = story.speed_accuracy("Juror", boundaries=[0.6, 1.0, 1.6])
"""
from __future__ import annotations
from dataclasses import dataclass, field
import math
import random


@dataclass
class DecisionStyle:
    """The four DDM parameters, as a character's decision temperament."""
    drift: float          # v: mean evidence per step toward the correct bound
    boundary: float       # a: evidence required to commit (the caution dial)
    start_bias: float     # z as a proportion of a: 0.5 is unbiased
    nondecision: float    # t0: fixed encoding+motor time added to every RT
    noise: float = 0.35   # within-trial jitter (the diffusion's sigma)
    dt: float = 0.02      # integration step


# named decision temperaments, staked in advance -- each makes a different,
# checkable claim about the RT/accuracy pair it will produce.
STYLES = {
    "impulsive":   DecisionStyle(drift=0.14, boundary=0.55, start_bias=0.5,
                                 nondecision=0.2),
    "deliberate":  DecisionStyle(drift=0.14, boundary=1.5, start_bias=0.5,
                                 nondecision=0.2),
    "keen":        DecisionStyle(drift=0.28, boundary=1.0, start_bias=0.5,
                                 nondecision=0.2),   # sharp senses: high drift
    "muddled":     DecisionStyle(drift=0.06, boundary=1.0, start_bias=0.5,
                                 nondecision=0.2),   # poor evidence: low drift
    "prejudiced":  DecisionStyle(drift=0.10, boundary=1.0, start_bias=0.72,
                                 nondecision=0.2),   # leans in before looking
}


@dataclass
class DecisionReport:
    who: str
    style: str
    n: int
    accuracy: float
    mean_rt: float          # mean RT of CORRECT responses
    mean_rt_error: float    # mean RT of ERROR responses
    rt_sd: float
    skew: float             # RT distribution skew (DDM predicts right-skew)
    quantiles: dict         # .1/.3/.5/.7/.9 RT quantiles of correct responses
    detail: dict = field(default_factory=dict)

    def render(self) -> str:
        lines = [f"DECISION — {self.who} ({self.style}), {self.n} trials:"]
        lines.append(f"    accuracy {self.accuracy:.0%}  |  mean RT "
                     f"{self.mean_rt:.2f}s (correct), "
                     f"{self.mean_rt_error:.2f}s (errors)")
        q = self.quantiles
        lines.append(f"    RT quantiles: .1={q[0.1]:.2f}  .3={q[0.3]:.2f}  "
                     f".5={q[0.5]:.2f}  .7={q[0.7]:.2f}  .9={q[0.9]:.2f}")
        lines.append(f"    right-skew {self.skew:+.2f} "
                     f"({'present' if self.skew > 0.1 else 'absent'}) — the "
                     f"DDM's signature RT shape")
        # if a meaningful fraction of walks never reached a bound within the
        # time limit, the accuracy above is computed on the decided minority and
        # would mislead -- say so.
        censored = self.detail.get("n_censored", 0)
        if censored and self.n and censored / self.n >= 0.05:
            frac = censored / self.n
            lines.append(f"    ⚠ {frac:.0%} of trials did not reach a decision "
                         f"within the time limit (drift too weak or boundary "
                         f"too wide); accuracy is over the {self.n - censored} "
                         f"that decided")
        return "\n".join(lines)


def install(char, *, drift: float = 0.15, boundary: float = 1.0,
            start_bias: float = 0.5, nondecision: float = 0.2,
            noise: float = 0.35, style: str = None):
    """Give a character a decision temperament. Either name a `style` from
    STYLES or pass DDM parameters directly. Stored on the character; the actual
    accumulation happens per-trial in the seeded driver (SOMA's deterministic
    core is left untouched)."""
    if style is not None:
        st = STYLES[style]
        char._decision = DecisionStyle(**st.__dict__)
        char._decision_style = style
    else:
        char._decision = DecisionStyle(drift=drift, boundary=boundary,
                                       start_bias=start_bias,
                                       nondecision=nondecision, noise=noise)
        char._decision_style = "custom"
    return char


def _one_trial(st: DecisionStyle, rng: random.Random, max_t: float = 8.0):
    """One noisy accumulation to bound. Returns (correct, rt) or (None, rt) on
    a non-terminating walk (censored at max_t). The upper bound a is the correct
    choice; 0 is the error. Evidence starts at z = start_bias * a."""
    a = st.boundary
    x = st.start_bias * a
    t = 0.0
    sqrt_dt = math.sqrt(st.dt)
    while 0.0 < x < a and t < max_t:
        x += st.drift * st.dt + st.noise * sqrt_dt * rng.gauss(0.0, 1.0)
        t += st.dt
    rt = t + st.nondecision
    if x >= a:
        return True, rt
    if x <= 0.0:
        return False, rt
    return None, rt


def _skew(xs):
    n = len(xs)
    if n < 3:
        return 0.0
    m = sum(xs) / n
    s = (sum((x - m) ** 2 for x in xs) / n) ** 0.5
    if s < 1e-9:
        return 0.0
    return (sum((x - m) ** 3 for x in xs) / n) / (s ** 3)


def _quantiles(xs, qs=(0.1, 0.3, 0.5, 0.7, 0.9)):
    if not xs:
        return {q: 0.0 for q in qs}
    s = sorted(xs)
    out = {}
    for q in qs:
        i = min(len(s) - 1, int(q * len(s)))
        out[q] = s[i]
    return out


def predict_decision(char, *, trials: int = 2000, seed: int = 0):
    """Run many noisy decisions and summarize the RT distribution and accuracy.
    Deterministic in the seed: the same seed reproduces the same distribution."""
    name = char if isinstance(char, str) else char.name
    st = getattr(char, "_decision", None) if not isinstance(char, str) else None
    if st is None:
        raise ValueError("call story.decides(name, ...) to give a character a "
                         "decision temperament first.")
    style = getattr(char, "_decision_style", "custom")
    rng = random.Random(seed)
    correct_rts, error_rts = [], []
    n_correct = n_error = 0
    for _ in range(trials):
        ok, rt = _one_trial(st, rng)
        if ok is True:
            n_correct += 1
            correct_rts.append(rt)
        elif ok is False:
            n_error += 1
            error_rts.append(rt)
    decided = n_correct + n_error
    accuracy = n_correct / decided if decided else 0.0
    mean_rt = sum(correct_rts) / len(correct_rts) if correct_rts else 0.0
    mean_err = sum(error_rts) / len(error_rts) if error_rts else 0.0
    sd = (sum((x - mean_rt) ** 2 for x in correct_rts) / len(correct_rts)) ** 0.5 \
        if correct_rts else 0.0
    return DecisionReport(
        who=name, style=style, n=trials, accuracy=accuracy,
        mean_rt=mean_rt, mean_rt_error=mean_err, rt_sd=sd,
        skew=_skew(correct_rts), quantiles=_quantiles(correct_rts),
        detail=dict(n_correct=n_correct, n_error=n_error,
                    n_censored=trials - decided))


@dataclass
class SATReport:
    who: str
    rows: list              # [(boundary, accuracy, mean_rt)]
    verdicts: list

    @property
    def confirmed(self) -> bool:
        return all(ok for (_, _, _, ok) in self.verdicts)

    def render(self) -> str:
        lines = [f"SPEED-ACCURACY TRADEOFF — {self.who}, boundary swept "
                 f"(drift held fixed):"]
        from soma.viz import bar
        rt_top = max((rt for *_, rt in self.rows), default=1.0) or 1.0
        lines.append("    boundary   accuracy               mean RT")
        for b, acc, rt in self.rows:
            lines.append(f"      {b:.2f}    {acc:5.0%} {bar(acc, 10)}"
                         f"   {rt:.2f}s {bar(rt / rt_top, 8)}")
        for claim, want, got, ok in self.verdicts:
            mark = "✓" if ok else "✗"
            lines.append(f"    {mark} {'CONFIRMED' if ok else 'FALSIFIED'}: "
                         f"{claim} — {got}")
        return "\n".join(lines)


def speed_accuracy(char, *, boundaries=(0.6, 1.0, 1.6), trials: int = 2000,
                   seed: int = 0):
    """Trace the speed-accuracy tradeoff by sweeping the boundary alone -- the
    DDM's most famous prediction. Widening the boundary must RAISE accuracy and
    LENGTHEN RT together; that monotone pair, from one dial, is the signature.

    Crucially this dissociates caution from ability: the drift (evidence
    quality) is held fixed, so any accuracy change is pure response caution --
    the same person being careful, not a smarter person."""
    name = char if isinstance(char, str) else char.name
    base = getattr(char, "_decision")
    rows = []
    try:
        for a in boundaries:
            # temporarily swap in each boundary and run; base is restored in
            # the finally, so an error mid-sweep can't leave the character with
            # a stray temporary decision style.
            char._decision = DecisionStyle(**{**base.__dict__, "boundary": a})
            rep = predict_decision(char, trials=trials, seed=seed)
            rows.append((a, rep.accuracy, rep.mean_rt))
    finally:
        char._decision = base

    accs = [acc for _, acc, _ in rows]
    rts = [rt for _, _, rt in rows]
    verdicts = [
        ("wider boundary raises accuracy (more evidence, fewer errors)",
         "monotone up", f"{[f'{a:.0%}' for a in accs]}",
         all(accs[i] <= accs[i + 1] + 1e-9 for i in range(len(accs) - 1))),
        ("wider boundary lengthens RT (more evidence takes longer)",
         "monotone up", f"{[f'{r:.2f}' for r in rts]}",
         all(rts[i] <= rts[i + 1] + 1e-9 for i in range(len(rts) - 1))),
    ]
    return SATReport(who=name, rows=rows, verdicts=verdicts)
