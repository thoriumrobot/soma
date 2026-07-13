"""
soma.narrative.earlywarning -- seeing the break coming before it breaks.

A self-revelation in SOMA is a critical transition: a high-conviction loop that
has been suppressing its disconfirming evidence is finally overwhelmed, and the
system flips from one regime (the lie holds) to another (the lie is seen). The
striking empirical result from complex-systems science is that such transitions
announce themselves. As a system approaches a tipping point its dynamics slow --
it recovers from perturbations more sluggishly -- and this *critical slowing
down* shows up as rising variance and rising lag-1 autocorrelation in the
system's fluctuations, before the transition itself. The same indicators that
warn of regime shifts in lakes, climate, and financial variance have been shown
to precede transitions into and out of depression in autorecorded mood.

This module computes those indicators on a SOMA run and asks the predictive
question: reading only the early part of a life -- before any revelation -- can
we tell whether the break is coming? It scores the trend in a rolling-window
variance and autocorrelation of the relevant channel over the pre-transition
stretch, and issues a forecast (break foreseeable / not) that
`predict_break_onset` then checks against whether the full run actually breaks.

The honest caveats are part of the science and are surfaced in the report:
critical slowing down is a property of transitions driven by a fold in the
system's stability, not of every shift -- financial crashes, for instance, show
rising variance without the autocorrelation signature, and are argued *not* to
be critical transitions on that basis. So a rising-variance-only signal is
reported as weaker evidence than variance-and-autocorrelation together.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .insight import run_with, series


def _variance(xs):
    n = len(xs)
    if n < 2:
        return 0.0
    m = sum(xs) / n
    return sum((x - m) ** 2 for x in xs) / (n - 1)


def _lag1_autocorr(xs):
    n = len(xs)
    if n < 3:
        return 0.0
    m = sum(xs) / n
    num = sum((xs[i] - m) * (xs[i - 1] - m) for i in range(1, n))
    den = sum((x - m) ** 2 for x in xs)
    return num / den if den > 1e-12 else 0.0


def _trend(ys):
    """Sign and magnitude of a least-squares slope over equally spaced ys,
    normalized to [-1, 1] by the range so it reads as 'rising/falling'."""
    n = len(ys)
    if n < 2:
        return 0.0
    xbar = (n - 1) / 2
    ybar = sum(ys) / n
    sxy = sum((i - xbar) * (y - ybar) for i, y in enumerate(ys))
    sxx = sum((i - xbar) ** 2 for i in range(n))
    slope = sxy / sxx if sxx else 0.0
    spread = (max(ys) - min(ys)) or 1.0
    return max(-1.0, min(1.0, slope * (n - 1) / spread))


def _detrend(xs):
    """Remove the slow linear trend, leaving the fluctuations. Critical slowing
    down is a property of how the *fluctuations* around the moving level behave
    (their variance and autocorrelation), not of the level itself -- so the
    trend must be taken out first, exactly as the mood/depression early-warning
    work removes slow level changes before computing indicators."""
    n = len(xs)
    if n < 2:
        return list(xs)
    xbar = (n - 1) / 2
    ybar = sum(xs) / n
    sxx = sum((i - xbar) ** 2 for i in range(n))
    sxy = sum((i - xbar) * (xs[i] - ybar) for i in range(n))
    slope = sxy / sxx if sxx else 0.0
    intercept = ybar - slope * xbar
    return [xs[i] - (slope * i + intercept) for i in range(n)]


@dataclass
class EarlyWarningReport:
    who: str
    channel: str
    broke: bool
    break_time: float
    var_trend: float           # slope of rolling variance over the pre-window
    ac_trend: float            # slope of rolling lag-1 autocorrelation
    forecast: str              # "break coming" | "stable" | "ambiguous"
    strength: str              # "strong" | "weak" | "none"
    detail: dict = field(default_factory=dict)

    @property
    def correct(self) -> bool:
        """Did the pre-transition forecast match what the full run did?"""
        if self.forecast == "break coming":
            return self.broke
        if self.forecast == "stable":
            return not self.broke
        return False   # ambiguous forecasts don't count as correct

    def render(self) -> str:
        lines = [f"EARLY WARNING — {self.who}, read only "
                 f"before any revelation:"]
        lines.append(f"  signal: {self.channel}")
        if self.detail.get("bound") is not None:
            from soma.viz import bar
            debt = self.detail.get("debt_last", 0)
            bound = self.detail["bound"]
            frac = 0.0 if bound <= 0 else min(1.0, debt / bound)
            lines.append(f"  accumulator {bar(frac, 16)} {debt:.1f} of "
                         f"bound {bound:.1f}, "
                         f"slope {self.detail.get('slope', 0):+.2f}/s")
        lines.append(f"  fluctuation variance trend:   {self.var_trend:+.2f} "
                     f"({'rising' if self.var_trend > 0.15 else 'flat/falling'})")
        lines.append(f"  fluctuation autocorr. trend:  {self.ac_trend:+.2f} "
                     f"({'rising' if self.ac_trend > 0.15 else 'flat/falling'})")
        fc = f"  -> FORECAST: {self.forecast} ({self.strength} signal)"
        if self.detail.get("predicted_break_time") is not None:
            fc += f" — crossing predicted at ≈{self.detail['predicted_break_time']:.0f}s"
        if self.detail.get("crossing_beyond_horizon") is not None:
            fc += (f" — at this rate the bound is not reached until "
                   f"≈{self.detail['crossing_beyond_horizon']:.0f}s, past the horizon")
        lines.append(fc)
        actual = (f"broke at {self.break_time:.0f}s" if self.broke
                  else "never broke")
        mark = "✓" if self.correct else "✗"
        lines.append(f"  {mark} the full run: {actual}")
        if self.strength == "weak":
            lines.append("  (one fluctuation indicator rose without the other — "
                         "weaker evidence; not every rising-variance run is a "
                         "fold-type critical transition, per the financial-crash "
                         "counterexample)")
        return "\n".join(lines)


def predict_break_onset(story, who, channel: str = "heart", *,
                        window: int = 4, overrides=None, signal: str = "debt",
                        loop_contains: str = ""):
    """Run the story, take the stretch of the chosen signal strictly BEFORE the
    first revelation (or the whole run if none), and compute
    critical-slowing-down indicators over rolling windows of that stretch.
    Forecast whether a break is coming from the trends alone, then reveal
    whether it actually did.

    signal="error" (default) reads the suppressing loop's accumulating
    prediction error from its settle events -- the theory-faithful signal, since
    critical slowing down is a property of the destabilizing variable, which for
    a SOMA lie is the error the loop is holding down, not the body. signal="body"
    reads `channel` (e.g. heart) instead, for characters whose approach to a
    transition is somatic.

    This is a genuine out-of-sample test in time: the indicators see only the
    pre-transition dynamics, and the transition itself is withheld until the
    forecast is fixed."""
    from .insight import error_series, debt_series
    name = who if isinstance(who, str) else who.name
    r = run_with(story, overrides)
    multi = any("." in k for k in r.channel_hist)

    revs = [e.t for e in r.chronicle if e.kind == "revelation"
            and (not multi or e.who.split(".")[0] == name)]
    broke = bool(revs)
    btime = min(revs) if revs else float("inf")

    bounds = []
    if signal == "debt":
        times, xs = debt_series(r, character=name, loop_contains=loop_contains)
        sig_label = "overwhelm-debt (the destabilizing variable)"
        bounds = [e.detail.get("bound") for e in r.chronicle
                  if e.kind == "settle" and e.detail.get("bound") is not None
                  and (not multi or e.who.split(".")[0] == name)
                  and (not loop_contains or loop_contains in e.who)]
    elif signal == "error":
        times, xs = error_series(r, character=name, loop_contains=loop_contains)
        sig_label = "suppressed prediction-error"
    else:
        xs = series(r, channel, character=name)
        times = r.times
        sig_label = f"'{channel}'"
    # keep only samples strictly before the transition
    if broke:
        pre = [x for x, t in zip(xs, times) if t < btime]
    else:
        pre = list(xs)
    detail = {"n_pre": len(pre), "signal": sig_label}

    if len(pre) < window + 2:
        return EarlyWarningReport(name, sig_label, broke, btime, 0.0, 0.0,
                                  "ambiguous", "none",
                                  detail={**detail, "reason": "too short to read"})

    # detrend the pre-transition stretch, then compute rolling indicators on
    # the fluctuations that remain
    fluct = _detrend(pre)
    vars_, acs = [], []
    for i in range(len(fluct) - window + 1):
        w = fluct[i:i + window]
        vars_.append(_variance(w))
        acs.append(_lag1_autocorr(w))
    vt = _trend(vars_)
    at = _trend(acs)
    detail.update(var_series=[round(v, 3) for v in vars_],
                  ac_series=[round(a, 3) for a in acs])

    # the decisive indicator, when the destabilizing accumulator and its bound
    # are both visible: extrapolate the debt's recent slope and ask whether --
    # and WHEN -- it crosses the bound before the story's horizon. This turns
    # the early warning from a binary alarm into a quantitative forecast of
    # the break time, fitted only to pre-transition data.
    t_pred = None
    horizon = r.times[-1] if r.times else 0.0
    bound = None
    if signal == "debt" and bounds:
        bound = bounds[min(len(bounds), len(pre)) - 1]
    if bound and len(pre) >= 3:
        half = pre[len(pre) // 2:]
        tspan = (times[len(pre) - 1] - times[len(pre) - len(half)]) or 1.0
        slope = (half[-1] - half[0]) / tspan
        t_last = times[len(pre) - 1]
        if slope > 1e-6 and pre[-1] < bound:
            t_pred = t_last + (bound - pre[-1]) / slope
        elif pre[-1] >= bound:
            t_pred = t_last
        detail.update(bound=bound, debt_last=round(pre[-1], 2),
                      slope=round(slope, 3))

    var_rising = vt > 0.15
    ac_rising = at > 0.15
    if t_pred is not None and t_pred <= horizon * 1.1:
        forecast = "break coming"
        strength = "strong" if (var_rising or ac_rising) else "moderate"
        detail["predicted_break_time"] = round(t_pred, 1)
    elif bound is not None:
        # the accumulator is visible and does NOT cross before the horizon
        forecast, strength = "stable", "strong"
        if t_pred is not None:
            detail["crossing_beyond_horizon"] = round(t_pred, 1)
    elif var_rising and ac_rising:
        forecast, strength = "break coming", "moderate"
    elif var_rising or ac_rising:
        forecast, strength = "break coming", "weak"
    else:
        forecast, strength = "stable", "strong"

    return EarlyWarningReport(name, sig_label, broke, btime, vt, at,
                              forecast, strength, detail)
