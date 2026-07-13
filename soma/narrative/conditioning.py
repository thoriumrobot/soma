"""
soma.narrative.conditioning -- the reward prediction error, run as learning.

The most quantitatively validated predictive model in behavioral neuroscience
is the reward prediction error (RPE): learning is driven by the gap between
reward received and reward expected (Rescorla & Wagner 1972; the temporal-
difference formulation of Sutton & Barto; Schultz's finding that midbrain
dopamine neurons fire exactly this delta -- large to an unpredicted reward,
zero once the reward is predicted, negative when a predicted reward is
omitted). SOMA's loop is already a prediction-error engine: a value loop's
belief is the value estimate, and the settle event's `error` is the RPE. This
module makes that correspondence explicit and stakes the model's signature
predictions.

The design turns on one honest complication the literature is emphatic about.
Plain Rescorla-Wagner treats extinction as UNLEARNING -- the value decays back
and that is that. But animals show SPONTANEOUS RECOVERY: after extinction and a
rest, the conditioned response returns. This is the evidence that extinction is
not erasure but NEW learning layered over an intact original trace (Bouton;
Pavlov's own observation). A single value cannot represent both "I have
unlearned this" and "the original is still there underneath," so this module
gives each association TWO traces:

  acquired   a slow trace -- the original CS->US value, hard to erase
  context    a fast trace -- the current context's correction, which is what
             extinction actually trains, and which DECAYS toward the slow trace
             during a rest

The expressed expectation is acquired + context. Extinction drives context
negative (the CR wanes); a rest lets context decay back toward zero (the slow
trace re-emerges -- spontaneous recovery). This is the dual-process account:
SOMA's value loop supplies the fast trace and the reward prediction error, and
a thin deterministic driver maintains the slow trace and the rest-time decay on
top of it (the recovery dynamics need per-beat control of which trace sees the
reward, which a single live loop cannot give). It makes recovery a PREDICTION
the single-trace model cannot make -- the module's sharpest, most falsifiable
claim.

    subject = story.conditions("Rat", cs="tone", us="food")
    report = story.predict_conditioning("Rat",
        acquire=10, extinguish=12, rest=8, reacquire=6)
    report.spontaneous_recovery      # True: the CR returned after the rest
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .insight import run_with


# how strongly the fast context trace decays back toward the slow acquired
# trace per beat of rest (no CS, no US). This is the spontaneous-recovery rate;
# 0 would be pure single-trace unlearning (no recovery), 1 instant forgetting
# of the extinction. Bouton's renewal/recovery work motivates a slow value.
CONTEXT_DECAY = 0.18


@dataclass
class Phase:
    name: str
    beats: int
    us_present: bool        # is the reward delivered this phase?
    cs_present: bool = True  # is the cue shown this phase? (rest = neither)


@dataclass
class ConditioningReport:
    subject: str
    cs: str
    us: str
    value: list             # expressed expectation (acquired+context) per beat
    rpe: list               # prediction error per beat -- the dopamine signal
    phases: list            # [(phase_name, start, end)]
    acquired_peak: float
    extinguished_to: float
    recovered_to: float
    verdicts: list
    detail: dict = field(default_factory=dict)

    @property
    def spontaneous_recovery(self) -> bool:
        return self.recovered_to > self.extinguished_to + 0.5

    @property
    def confirmed(self) -> bool:
        return all(ok for (_, _, _, ok) in self.verdicts)

    def render(self) -> str:
        lines = [f"CONDITIONING — {self.subject}: {self.cs} → {self.us} "
                 f"(value = acquired + context trace)"]
        # a small sparkline of the value trajectory across phases
        for pname, lo, hi in self.phases:
            seg = self.value[lo:hi]
            spark = _spark(seg)
            lines.append(f"    {pname:<12s} {spark}  "
                         f"[{_fmt(seg[0])} → {_fmt(seg[-1])}]" if seg else
                         f"    {pname:<12s} (empty)")
        peak_rpe = max(self.rpe) if self.rpe else 0.0
        lines.append(f"    peak RPE (unpredicted reward): {peak_rpe:+.2f}; "
                     f"once predicted it falls toward 0 — dopamine's signature")
        for claim, want, got, ok in self.verdicts:
            mark = "✓" if ok else "✗"
            lines.append(f"    {mark} {'CONFIRMED' if ok else 'FALSIFIED'}: "
                         f"{claim} — {got}")
        return "\n".join(lines)


def _fmt(v):
    return f"{v:.1f}"


def _spark(seg):
    if not seg:
        return ""
    blocks = "▁▂▃▄▅▆▇█"
    lo, hi = 0.0, max(max(seg), 1.0)
    return "".join(blocks[min(7, int((v - lo) / (hi - lo) * 7))] for v in seg)


def install(char, *, cs: str, us: str, salience: float = 0.9,
            rate: float = 0.4):
    """Wire a conditioning subject: a value loop that learns the CS->US
    association. `rate` is the learning rate (how fast the value tracks the
    RPE); `salience` sets the CS's precision. Uses only library verbs.

    The slow 'acquired' trace and fast 'context' trace are represented in the
    Python driver (predict_conditioning) rather than as two live loops, because
    the recovery dynamics need per-beat control of which trace sees the reward;
    the loop here provides the RPE and the fast-trace update, and the driver
    maintains the slow trace and the rest-time decay."""
    char.senses(us, baseline=0.0)
    # the value loop: low conviction so the reward updates the belief (the
    # value estimate); its settle error is the RPE.
    char.appraises(us, when=f"{us} > -1", feeling="anticipation",
                   precision=salience, conviction=0.1, updates=True)
    char._conditioning = dict(cs=cs, us=us, rate=rate, salience=salience,
                              loop=f"appraising_{us}")
    return char


def predict_conditioning(story, who, *, acquire: int = 10, extinguish: int = 12,
                         rest: int = 8, reacquire: int = 0,
                         us_magnitude: float = 8.0):
    """Run the canonical schedule and stake the RPE model's predictions.

    Phases: acquisition (CS+US), extinction (CS, no US), rest (neither), and
    optionally reacquisition (CS+US again). Returns a ConditioningReport whose
    value trajectory is the dual-trace expectation and whose `rpe` is the
    per-beat prediction error.

    The predictions staked, each checked against the trajectory:
      1. acquisition: the value climbs to near the reward magnitude
      2. the RPE shrinks as prediction improves (dopamine's signature: large to
         an unpredicted reward, ~0 once predicted)
      3. extinction: the value falls (the CR wanes)
      4. SPONTANEOUS RECOVERY: after the rest, the value is higher than it was
         at the end of extinction -- the single-trace model's failure
      5. (if reacquire) savings: relearning is faster than original learning
    """
    name = who if isinstance(who, str) else who.name
    ch = next(c for c in story.characters if c.name == name)
    cond = getattr(ch, "_conditioning", None)
    if cond is None:
        raise ValueError(f"{name} is not a conditioning subject; call "
                         f"story.conditions({name!r}, cs=..., us=...) first.")

    phases = [Phase("acquisition", acquire, True),
              Phase("extinction", extinguish, False),
              Phase("rest", rest, False, cs_present=False)]
    if reacquire:
        phases.append(Phase("reacquisition", reacquire, True))

    # build the US stimulus schedule and run once; the loop gives us the fast
    # trace + RPE. The slow trace and rest decay are maintained here.
    multi = len(story.characters) > 1
    us_ch = f"{name}.{cond['us']}" if multi else cond["us"]
    beats = []
    t = 1
    windows = []
    for ph in phases:
        windows.append((ph.name, t - 1, t - 1 + ph.beats))
        for _ in range(ph.beats):
            beats.append(f"at {t}s: {us_magnitude if ph.us_present else 0}")
            t += 1
    total = t
    src = story.source()
    kept = [ln for ln in src.splitlines()
            if not ln.lstrip().startswith("stimulus ")]
    probe = f"stimulus {us_ch} {{ {'  '.join(beats)} }}"
    # widen the sim horizon to cover all phases
    kept = [(_widen(ln, total) if ln.strip().startswith("sim") else ln)
            for ln in kept]
    probe_src = "\n".join(kept + ["", probe]) + "\n"

    from soma import run_source
    r = run_source(probe_src, title=f"{story.title}__conditioning")

    # fast trace + RPE straight from the loop's settle events
    settles = [(e.t, e.detail["belief"], e.detail["error"])
               for e in r.chronicle if e.kind == "settle"
               and (not multi or e.who.split(".")[0] == name)]
    settles.sort()
    fast = [b for _, b, _ in settles]
    rpe = [e for _, _, e in settles]

    # the dual trace: a slow 'acquired' value that rises with the fast trace
    # during acquisition but is *sticky* -- it does not fall during extinction
    # (extinction trains the context, not the original) -- and a context
    # correction that is (fast - slow), which decays toward zero during rest.
    slow = 0.0
    value, contexts = [], []
    for i, ((tt, b, e), ph_of) in enumerate(zip(settles,
                                                _phase_of_each(settles, windows))):
        if ph_of == "acquisition":
            slow = max(slow, b)                    # the original trace forms
            ctx = b - slow
        elif ph_of == "extinction":
            ctx = b - slow                         # context goes negative
        elif ph_of == "rest":
            ctx = contexts[-1] * (1 - CONTEXT_DECAY) if contexts else 0.0
        else:  # reacquisition
            slow = max(slow, b)
            ctx = b - slow
        contexts.append(ctx)
        value.append(max(0.0, slow + ctx))

    def phase_slice(nm):
        for pn, lo, hi in windows:
            if pn == nm:
                return value[lo:hi]
        return []

    acq = phase_slice("acquisition")
    ext = phase_slice("extinction")
    rst = phase_slice("rest")
    acquired_peak = max(acq) if acq else 0.0
    extinguished_to = ext[-1] if ext else acquired_peak
    recovered_to = rst[-1] if rst else extinguished_to

    verdicts = []
    verdicts.append(("acquisition: value climbs to near the reward",
                     "near 8", f"peaked at {acquired_peak:.1f}",
                     acquired_peak >= us_magnitude * 0.6))
    # RPE shrinks: compare the first few acquisition errors to the later ones
    if len(acq) >= 4:
        early_rpe = sum(abs(x) for x in rpe[:2]) / 2
        late_rpe = sum(abs(x) for x in rpe[len(acq) - 2:len(acq)]) / 2
        verdicts.append(("the RPE shrinks as reward becomes predicted "
                         "(dopamine's signature)", "early > late",
                         f"{early_rpe:.2f} → {late_rpe:.2f}",
                         early_rpe > late_rpe + 0.3))
    verdicts.append(("extinction: the conditioned value falls",
                     "falls", f"{acquired_peak:.1f} → {extinguished_to:.1f}",
                     extinguished_to < acquired_peak - 1.0))
    recovered = recovered_to > extinguished_to + 0.5
    verdicts.append(("SPONTANEOUS RECOVERY: after rest the value returns "
                     "(extinction was new learning, not erasure)",
                     "recovers", f"{extinguished_to:.1f} → {recovered_to:.1f} "
                     f"after rest", recovered))
    if reacquire:
        reacq = phase_slice("reacquisition")
        # savings: reacquisition reaches the peak in fewer beats than acquisition
        def beats_to(seg, target):
            for i, v in enumerate(seg):
                if v >= target:
                    return i + 1
            return len(seg) + 1
        # savings has two faces, both real: reacquisition starts HIGHER (the
        # acquired trace was never erased) and reaches criterion no later.
        target = acquired_peak * 0.9
        t_acq = beats_to(acq, target)
        t_re = beats_to(reacq, target)
        head_start = (reacq[0] if reacq else 0.0) > (acq[0] if acq else 0.0) + 0.3
        verdicts.append(("savings: relearning starts from the intact trace and "
                         "is no slower", "reacq >= as fast, higher start",
                         f"{t_acq} vs {t_re} beats; starts "
                         f"{reacq[0]:.1f} vs {acq[0]:.1f}",
                         t_re <= t_acq and head_start))

    return ConditioningReport(
        subject=name, cs=cond["cs"], us=cond["us"], value=value, rpe=rpe,
        phases=windows, acquired_peak=round(acquired_peak, 2),
        extinguished_to=round(extinguished_to, 2),
        recovered_to=round(recovered_to, 2), verdicts=verdicts,
        detail=dict(fast=fast, slow_final=slow, context=contexts))


def _phase_of_each(settles, windows):
    out = []
    for i in range(len(settles)):
        ph = "acquisition"
        for pn, lo, hi in windows:
            if lo <= i < hi:
                ph = pn
                break
        out.append(ph)
    return out


def _widen(sim_line, total):
    import re
    return re.sub(r"duration:\s*\d+\w*",
                  f"duration: {total}s", sim_line)
