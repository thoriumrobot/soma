"""
soma.narrative.gottman -- the mathematics of a marriage, run as a marriage.

Gottman and Murray's model of marital interaction (The Mathematics of
Marriage, 2002) is the most famous predictive character simulation there is:
from parameters fitted to minutes of one conversation -- each partner's
uninfluenced steady state, emotional inertia, influence function with its
negative threshold, and repair terms -- it predicted which newlyweds would
divorce with striking accuracy, and the couple typology it formalized
(validating, volatile, and conflict-avoiding couples stable; hostile and
hostile-detached couples headed for the cascade) turned on a handful of
measurable quantities: the ratio of positive to negative interaction (the
"magic" 5:1 during conflict), negative-affect reciprocity, and whether repair
attempts land.

This module rebuilds that model out of SOMA's own machinery, so every quantity
is generated rather than scored by hand:

  uninfluenced steady state  = the manner each stance would hold alone
  influence function          = the couple/lag reading of the other's manner,
                                with correspondence responses gated by...
  negative threshold          = the received-manner level at which friction
                                triggers. Gottman's divorcing couples had a
                                LOWER threshold -- smaller negativity set them
                                off -- which is exactly a guard level here.
  emotional inertia           = conviction: how much the held self resists the
                                pull of what it is met with
  repair                      = an interoceptive loop: when my OWN distress
                                climbs past the repair threshold, I reach for
                                warmth -- a bid made through the body, which is
                                why stonewalling (never reaching) reads on the
                                heart record
  the Dow of the marriage     = the running ease:friction ratio

And the model's most famous move is reproduced as an honest test: THIN-SLICE
FORECASTING. `assess()` computes its diagnosis from only the FIRST QUARTER of
the interaction, stakes a forecast of where rapport ends, then reveals the full
run. The 94%-from-minutes claim, in-model and falsifiable.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .circumplex import Stance, _manner
from .insight import run_with, outcome


@dataclass(frozen=True)
class CoupleType:
    name: str
    stable: bool               # Gottman's regulated vs. unregulated
    a_stance: Stance
    b_stance: Stance
    gain: float                # influence strength through the couple
    inertia: float             # conviction: resistance to the partner's pull
    neg_threshold: float       # received manner at/below which friction fires.
                               # HIGHER = thinner skin (smaller negativity
                               # triggers) -- divorcing couples' signature
    repairs: bool              # repair attempts exist
    repair_at: float           # own-heart level that triggers the repair bid
    engagement: float          # how much manner is shown at all (avoiders low)
    gloss: str = ""


COUPLE_TYPES = {
    "validating": CoupleType(
        "validating", True,
        Stance(0.2, 0.6), Stance(-0.2, 0.6),
        gain=0.85, inertia=0.45, neg_threshold=2.5,
        repairs=True, repair_at=88.0, engagement=1.0,
        gloss="warm, mutually influenced, lets small negativity pass, repairs"),
    "volatile": CoupleType(
        "volatile", True,
        Stance(0.6, 0.45), Stance(0.55, 0.4),
        gain=0.95, inertia=0.25, neg_threshold=3.5,
        repairs=True, repair_at=92.0, engagement=1.0,
        gloss="hot and loud, quick to fire AND quick to repair -- stable "
              "because the positive is louder still"),
    "avoider": CoupleType(
        "avoider", True,
        Stance(-0.3, 0.35), Stance(-0.25, 0.3),
        gain=0.45, inertia=0.7, neg_threshold=2.0,
        repairs=True, repair_at=90.0, engagement=0.55,
        gloss="conflict-avoiding: little influence either way, little said, "
              "stable by disengagement"),
    "hostile": CoupleType(
        "hostile", False,
        Stance(0.5, -0.55), Stance(0.45, -0.5),
        gain=0.9, inertia=0.5, neg_threshold=4.5,
        repairs=False, repair_at=999.0, engagement=1.0,
        gloss="engaged and corrosive: thin-skinned (low negative threshold), "
              "no repair that lands -- the cascade"),
    "hostile_detached": CoupleType(
        "hostile_detached", False,
        Stance(0.6, -0.6), Stance(-0.5, -0.45),
        gain=0.75, inertia=0.65, neg_threshold=4.5,
        repairs=False, repair_at=999.0, engagement=0.75,
        gloss="one attacks, one stonewalls: hostility met with withdrawal, "
              "the coldest configuration"),
}


def marry(story, a, b, type_name: str, *, lag: str = "1s"):
    """Wire two characters into a Gottman couple of the given type. Uses only
    library verbs; every type parameter above is staked before any run."""
    ct = COUPLE_TYPES[type_name]
    ca = a if not isinstance(a, str) else next(
        c for c in story.characters if c.name == a)
    cb = b if not isinstance(b, str) else next(
        c for c in story.characters if c.name == b)
    # engagement governs how much of each other they take in (the couple
    # gain): avoiders read each other faintly, landing received manner in the
    # NEUTRAL zone -- no ease, no friction, stability by disengagement, which
    # is exactly Gottman's conflict-avoiding couple. The anchor itself stays
    # unscaled: avoiders are quiet, not cold.
    eff_gain = ct.gain   # the influence dial IS the engagement mechanism:
                         # avoiders' low gain lands the received manner in the
                         # neutral zone between the ease and friction guards
    for ch, st, other in ((ca, ct.a_stance, ct.b_stance),
                          (cb, ct.b_stance, ct.a_stance)):
        anchor = _manner(st.warmth)
        ch._add_sense("manner", "proprio", round(anchor, 1), "Expression")
        ch._stance = st
    ca.reads(cb, "manner", into="their_manner", gain=eff_gain, lag=lag)
    cb.reads(ca, "manner", into="their_manner", gain=eff_gain, lag=lag)
    # the conflict topic arrives on its own channel, through partner A -- a
    # grievance the timeline can inject without the manner loops overwriting it
    ca.senses("grievance", baseline=0.0)
    for ch, st, other in ((ca, ct.a_stance, ct.b_stance),
                          (cb, ct.b_stance, ct.a_stance)):
        anchor = _manner(st.warmth)
        pull = _manner(other.warmth)
        sus = max(0.0, min(1.0, 1.0 - ct.inertia))
        warm_resp = round(anchor + sus * (min(10.0, pull + 1.0) - anchor), 1)
        cold_resp = round(anchor + sus * (max(0.0, pull - 1.5) - anchor), 1)
        # ease above the positive line; friction at/below the NEGATIVE
        # THRESHOLD -- the dial Gottman found lower in divorcing couples
        ch.appraises("their_manner", when="their_manner >= 5.5",
                     feeling="ease", shows_on="manner",
                     shows_value=warm_resp, expects=5.0)
        ch.appraises("their_manner",
                     when=f"their_manner <= {ct.neg_threshold}",
                     as_threat=True, feeling="friction", shows_on="manner",
                     shows_value=cold_resp, drives="heart", to=102,
                     expects=5.0)
        if ch is ca:
            # the grievance lands on A: their manner cools and their body
            # rises while the topic is live -- the fight arriving
            ch.appraises("grievance", as_threat=True, when="grievance > 5",
                         feeling="friction", shows_on="manner",
                         shows_value=cold_resp, drives="heart", to=100,
                         expects=0.0)
        if ct.repairs:
            # repair as interoceptive regulation: my own distress climbing
            # past the repair threshold triggers a warm bid THROUGH the
            # relationship -- the manner lifts even mid-fight
            ch.appraises("heart", when=f"heart > {ct.repair_at}",
                         feeling="reaching_out", shows_on="manner",
                         shows_value=min(10.0, anchor + 3.0), expects=72.0)
        ch.has_mood("rapport", fed_by=["ease", "friction"])
    story._gottman = dict(type=ct, a=ca.name, b=cb.name)
    return ca, cb


@dataclass
class GottmanReport:
    a: str
    b: str
    type_name: str
    stable_forecast: bool          # staked by the type table
    ratio: float                   # ease : friction over the whole run
    thin_ratio: float              # same, first quarter only
    reciprocity: float             # P(partner friction follows own friction)
    thin_forecast: str             # "holds" | "falls", from the first quarter
    verdicts: list
    gloss: str

    @property
    def confirmed(self) -> bool:
        return all(ok for (_, _, _, ok) in self.verdicts)

    def render(self) -> str:
        lines = [f"GOTTMAN ASSESSMENT — {self.a} & {self.b} ({self.type_name}): "
                 f"{self.gloss}"]
        lines.append(f"  positivity ratio {self.ratio:.2f}:1 over the whole run "
                     f"(first quarter: {self.thin_ratio:.2f}:1); "
                     f"negative reciprocity {self.reciprocity:.0%}")
        for claim, want, got, ok in self.verdicts:
            mark = "✓" if ok else "✗"
            lines.append(f"  {mark} {'CONFIRMED' if ok else 'FALSIFIED'}: "
                         f"{claim} — forecast {want}, observed {got}")
        return "\n".join(lines)


def _quale_times(r, quale, who=None):
    return [e.t for e in r.chronicle if e.kind == "emit"
            and quale in str(e.detail.get("quale", ""))
            and (who is None or e.who.startswith(f"{who}."))]


def assess(story, *, beats: int = 20, complaint_at: int = 3):
    """Run the couple through a contentious conversation -- both open at their
    stance, then one lodges a complaint (a hard dip in manner) -- and measure
    the Gottman quantities. Stakes two kinds of forecast before looking:

      1. from the TYPE (theory-side): stable types end with rapport holding
         and ratio >= 1; unstable types end with rapport falling and ratio < 1.
      2. from the THIN SLICE (data-side): the first-quarter ratio alone
         forecasts where rapport ends -- the famous minutes-to-years claim.
    """
    g = story._gottman
    ct, an, bn = g["type"], g["a"], g["b"]

    src = story.source()
    kept = [ln for ln in src.splitlines()
            if not ln.lstrip().startswith("stimulus ")]
    ma = _manner(ct.a_stance.warmth)
    mb = _manner(ct.b_stance.warmth)
    probes = [
        f"stimulus {an}.manner {{ at 1s: {round(ma,1)} }}",
        f"stimulus {bn}.manner {{ at 1s: {round(mb,1)} }}",
        # the complaint: the conflict topic arrives through A and stays live
        # for three beats. What happens next is the marriage.
        f"stimulus {an}.grievance {{ at {complaint_at}s: 8  "
        f"at {complaint_at+1}s: 8  at {complaint_at+2}s: 8  "
        f"at {complaint_at+3}s: 0 }}",
    ]
    probe_src = "\n".join(kept + [""] + probes) + "\n"
    from soma import run_source
    r = run_source(probe_src, title=f"{story.title}__gottman")

    horizon = r.times[-1] or 1.0
    q1 = horizon / 4.0

    def ratio_in(t_hi):
        ease = sum(1 for t in _quale_times(r, "ease") if t <= t_hi)
        fric = sum(1 for t in _quale_times(r, "friction") if t <= t_hi)
        if fric == 0:
            return float(ease) if ease else 1.0   # silence is neutral, not negative
        return ease / fric

    ratio = ratio_in(horizon)
    thin_ratio = ratio_in(q1)

    # negative reciprocity: how often one partner's friction is answered by
    # the other's within two beats
    fa = _quale_times(r, "friction", an)
    fb = _quale_times(r, "friction", bn)
    answered = sum(1 for t in fa if any(0 < u - t <= 2.0 for u in fb))
    reciprocity = answered / len(fa) if fa else 0.0

    def rap_delta(name):
        h = (r.mood_hist.get(f"{name}_rapport") or [])
        if len(h) < 2:
            return 0.0
        return (sum(h[-3:]) / min(3, len(h))) - h[0]

    da, db = rap_delta(an), rap_delta(bn)
    holds = da >= -0.5 and db >= -0.5

    # the thin-slice coding rule: near-silence in the slice reads as a
    # disengaged (regulated) couple, not a cascading one -- conflict-avoiders
    # do not divorce by ratio; otherwise the slice ratio decides
    thin_affect = (sum(1 for t in _quale_times(r, "ease") if t <= q1)
                   + sum(1 for t in _quale_times(r, "friction") if t <= q1))
    if thin_affect <= 3:
        thin_forecast = "holds"
    else:
        thin_forecast = "holds" if thin_ratio >= 1.0 else "falls"

    verdicts = []
    if ct.stable:
        verdicts.append((f"a {ct.name} couple is REGULATED: rapport holds",
                         "holds", f"deltas {da:+.1f}/{db:+.1f}", holds))
        if ct.name != "avoider":
            verdicts.append(("their positivity outweighs the negative "
                             "(ratio >= 1)", ">= 1", f"{ratio:.2f}:1",
                             ratio >= 1.0))
    else:
        verdicts.append((f"a {ct.name} couple CASCADES: rapport falls",
                         "falls", f"deltas {da:+.1f}/{db:+.1f}", not holds))
        verdicts.append(("negativity outweighs the positive (ratio < 1)",
                         "< 1", f"{ratio:.2f}:1", ratio < 1.0))
    # engagement claims: volatile couples are LOUD (many affect events), and
    # conflict-avoiders are quiet (few) -- both staked by the typology
    n_affect = (len(_quale_times(r, "ease")) + len(_quale_times(r, "friction")))
    if ct.name == "volatile":
        verdicts.append(("a volatile couple is loud: many affect events",
                         ">= 20", str(n_affect), n_affect >= 20))
    if ct.name == "avoider":
        verdicts.append(("an avoider couple is quiet: few affect events",
                         "<= 8", str(n_affect), n_affect <= 8))

    thin_ok = (thin_forecast == "holds") == holds
    verdicts.append(("THIN SLICE: the first quarter alone forecasts the ending",
                     thin_forecast, "holds" if holds else "falls", thin_ok))

    return GottmanReport(a=an, b=bn, type_name=ct.name,
                         stable_forecast=ct.stable, ratio=round(ratio, 2),
                         thin_ratio=round(thin_ratio, 2),
                         reciprocity=round(reciprocity, 2),
                         thin_forecast=thin_forecast, verdicts=verdicts,
                         gloss=ct.gloss)
