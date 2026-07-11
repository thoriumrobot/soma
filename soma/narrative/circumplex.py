"""
soma.narrative.circumplex -- predicting the space BETWEEN two characters.

Single-skull models predict what one person feels. The interpersonal circumplex
(Leary; Carson; Kiesler; Wiggins; contemporary integrative interpersonal theory)
predicts what a person's behavior *pulls from the other* -- which makes it the
right theory for SOMA's multi-character machinery, where minds meet only as
surfaces, with gain and lag.

Two orthogonal axes locate any interpersonal act: DOMINANCE (agency, control:
leading vs. yielding) and WARMTH (communion, affiliation: moving toward vs.
against). The complementarity principle then makes a directional forecast:

  correspondence on warmth   -- warmth invites warmth, hostility invites
                                hostility. Empirically ROBUST (Sadler & Woody;
                                Markey; daily-life and lab studies converge).
  reciprocity on dominance   -- dominance invites yielding, yielding invites
                                taking charge. Empirically REAL BUT WEAKER and
                                context-moderated (stronger in conflict and
                                task settings, weaker between familiars) --
                                so this module stakes it at lower confidence,
                                and says so in the forecast.

CIIT adds the affective consequence, which is the novelist's payoff: high
complementarity predicts interactions that SETTLE (positive affect, rapport
holds); low complementarity predicts STRAIN -- and hostile correspondence
(cold met with cold) predicts escalation, the fight that feeds itself.

Every forecast is checked by compiling the dyad through SOMA's own couple/lag
machinery and running an exchange the forecast has never seen.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Stance:
    """A position on the circumplex: dominance and warmth, each -1..1."""
    dominance: float
    warmth: float

    def octant(self) -> str:
        """The Leary/Wiggins octant name for this position."""
        import math
        d, w = self.dominance, self.warmth
        if abs(d) < 0.15 and abs(w) < 0.15:
            return "neutral (mid-circumplex)"
        ang = math.degrees(math.atan2(d, w)) % 360   # 0 = pure warm, 90 = pure dominant
        names = ["warm-agreeable", "gregarious-extraverted", "assured-dominant",
                 "arrogant-calculating", "coldhearted", "aloof-introverted",
                 "unassured-submissive", "unassuming-ingenuous"]
        return names[int(((ang + 22.5) % 360) // 45)]


@dataclass(frozen=True)
class Pull:
    """The complementary response a stance invites from the other person --
    with the confidence the literature actually supports for each axis."""
    stance: Stance                 # the predicted response position
    warmth_basis: str
    dominance_basis: str

    def gloss(self) -> str:
        return (f"invites {self.stance.octant()} "
                f"(warmth -> {self.stance.warmth:+.2f}: {self.warmth_basis}; "
                f"dominance -> {self.stance.dominance:+.2f}: {self.dominance_basis})")


def predict_pull(stance: Stance) -> Pull:
    """The complementarity forecast: what this behavior invites."""
    return Pull(
        stance=Stance(dominance=-stance.dominance, warmth=stance.warmth),
        warmth_basis="correspondence, robust across studies",
        dominance_basis="reciprocity, weaker and context-moderated "
                        "(strongest in conflict; weaker between familiars)")


def complementarity(a: Stance, b: Stance) -> dict:
    """How complementary two stances are, per axis and overall. Warmth is
    weighted above dominance because its evidential support is stronger."""
    warmth_c = 1.0 - abs(a.warmth - b.warmth) / 2.0          # correspondence
    dom_c = 1.0 - abs(a.dominance + b.dominance) / 2.0       # reciprocity
    overall = 0.65 * warmth_c + 0.35 * dom_c
    return dict(warmth=round(warmth_c, 2), dominance=round(dom_c, 2),
                overall=round(overall, 2))


def _manner(warmth: float) -> float:
    """A stance's warmth as a surface value on the 0..10 'manner' channel."""
    return round(5.0 + 3.5 * warmth, 1)


def bind_dyad(a, b, *, a_stance: Stance, b_stance: Stance,
              lag: str = "1s", gain: float = 0.9):
    """Wire two characters into a circumplex dyad using only the library's own
    verbs. Each shows a `manner` surface at their stance's warmth; each reads
    the other's manner (through SOMA's couple -- attenuated and late, per the
    other-minds rule); and each responds by correspondence: warmth received
    warms the manner shown, coldness received cools it, each character anchored
    by their own stance. Rapport is a mood fed by ease and drained by friction,
    so the affective forecast is measurable."""
    for ch, st in ((a, a_stance), (b, b_stance)):
        ch._add_sense("manner", "proprio", _manner(st.warmth), "Expression")
        ch._stance = st
    a.reads(b, "manner", into="their_manner", gain=gain, lag=lag)
    b.reads(a, "manner", into="their_manner", gain=gain, lag=lag)
    for ch, st, other in ((a, a_stance, b_stance), (b, b_stance, a_stance)):
        # Susceptibility to the pull is (1 - conviction): a self held loosely
        # takes on more of the manner it is met with; a self held hard stays
        # anchored at its own stance. This is the SAME dial the base language
        # uses for every prior, so "who gives ground" is a mechanism, not a
        # label -- and it is what makes the accommodation forecast testable.
        anchor = _manner(st.warmth)
        pull = _manner(other.warmth)                 # correspondence target
        sus = max(0.0, min(1.0, 1.0 - ch.temp.conviction))
        warm_resp = round(anchor + sus * (min(10.0, pull + 1.0) - anchor), 1)
        cold_resp = round(anchor + sus * (max(0.0, pull - 1.0) - anchor), 1)
        ch.appraises("their_manner", when="their_manner >= 6",
                     feeling="ease", shows_on="manner",
                     shows_value=warm_resp, expects=5.0)
        ch.appraises("their_manner", when="their_manner <= 4", as_threat=True,
                     feeling="friction", shows_on="manner",
                     shows_value=cold_resp, drives="heart", to=100,
                     expects=5.0)
        # both qualia FEED the mood; their valences (+ease, -friction)
        # carry the direction, so rapport rises with ease and falls
        # with friction without double-negating the weights
        ch.has_mood("rapport", fed_by=["ease", "friction"])
        ch._dyad_anchor = anchor
    return a, b


@dataclass
class DyadReport:
    """The dyadic forecast, checked against a run of the compiled exchange."""
    a: str
    b: str
    comp: dict
    trajectory_forecast: str    # "settles" | "strains" | "mixed"
    verdicts: list              # list[(claim, forecast, observed, ok)]
    notes: list

    @property
    def confirmed(self) -> bool:
        return all(ok for (_, _, _, ok) in self.verdicts)

    def render(self) -> str:
        lines = [f"Dyad forecast — {self.a} & {self.b}: complementarity "
                 f"{self.comp['overall']} (warmth {self.comp['warmth']}, "
                 f"dominance {self.comp['dominance']}) -> the interaction "
                 f"should {self.trajectory_forecast.upper()}."]
        for claim, want, got, ok in self.verdicts:
            mark = "✓" if ok else "✗"
            lines.append(f"  {mark} {'CONFIRMED' if ok else 'FALSIFIED'}: "
                         f"{claim} — forecast {want}, observed {got}")
        for n in self.notes:
            lines.append(f"  ({n})")
        return "\n".join(lines)


def predict_dyad(story, a, b, *, beats: int = 10):
    """Forecast, then test, what happens between two bound characters.

    The forecast is computed from the two stances ALONE (theory-side, before
    any run): the complementarity index sets the trajectory -- settles (>= .60),
    strains (< .45), or mixed -- and hostile correspondence (both cold) adds an
    escalation claim. The accommodation claim names WHO gives ground: the
    character whose temperament holds its priors more loosely (lower
    conviction) is forecast to drift further from their opening manner.

    Then the compiled dyad is run on a neutral probe (each simply shows their
    opening manner once; everything after emerges through the couple), and each
    claim is checked against the moods, emits, and the manner record."""
    an = a if isinstance(a, str) else a.name
    bn = b if isinstance(b, str) else b.name
    ca = next(c for c in story.characters if c.name == an)
    cb = next(c for c in story.characters if c.name == bn)
    sa, sb = ca._stance, cb._stance
    comp = complementarity(sa, sb)

    # Structural complementarity is not the same thing as comfort: two cold
    # people CORRESPOND perfectly on warmth (Kiesler: hostility invites
    # hostility) and the exchange is still corrosive -- the CIIT affective
    # forecast branches on which side of the warmth axis the correspondence
    # sits. So: hostile correspondence -> strains (and sustains itself);
    # otherwise high complementarity -> settles, low -> strains.
    hostile = sa.warmth < -0.3 and sb.warmth < -0.3
    if hostile:
        traj = "strains"
    elif comp["overall"] >= 0.60:
        traj = "settles"
    elif comp["overall"] < 0.45:
        traj = "strains"
    else:
        traj = "mixed"
    softer = an if ca.temp.conviction <= cb.temp.conviction else bn

    # ---- run the exchange the forecast has not seen -------------------------
    src = story.source()
    kept = [ln for ln in src.splitlines()
            if not ln.lstrip().startswith("stimulus ")]
    probes = [f"stimulus {n}.manner {{ at 1s: {_manner(s.warmth)} }}"
              for n, s in ((an, sa), (bn, sb))]
    probe_src = "\n".join(kept + [""] + probes) + "\n"
    from soma import run_source
    r = run_source(probe_src, title=f"{story.title}__dyad")

    def mood_delta(name):
        # the compiler qualifies moods with an underscore: "Rook_rapport"
        h = (r.mood_hist.get(f"{name}_rapport")
             or r.mood_hist.get("rapport") or [])
        if len(h) < 2:
            return 0.0
        return (sum(h[-3:]) / min(3, len(h))) - h[0]

    da, db = mood_delta(an), mood_delta(bn)
    if traj == "settles":
        observed_ok = da >= -0.5 and db >= -0.5
        got = f"rapport deltas {da:+.1f}/{db:+.1f}"
    elif traj == "strains":
        observed_ok = da < -0.5 or db < -0.5
        got = f"rapport deltas {da:+.1f}/{db:+.1f}"
    else:
        observed_ok = True
        got = f"rapport deltas {da:+.1f}/{db:+.1f} (mixed: no directional claim)"
    verdicts = [(f"the interaction {traj}", traj, got, observed_ok)]

    if hostile:
        # hostile correspondence sustains itself: the friction does not die
        # out (it still fires in the final quarter) and rapport ends negative
        fr = [e.t for e in r.chronicle if e.kind == "emit"
              and "friction" in str(e.detail.get("quale", ""))]
        last_q = (r.times[-1] or 1) * 0.75
        persists = any(t >= last_q for t in fr)
        ends_neg = min(da, db) < 0 or (
            (r.mood_hist.get(f"{an}_rapport") or [0])[-1] < 0)
        verdicts.append(("hostile correspondence sustains itself (friction "
                         "persists; rapport ends negative)",
                         "persists & negative",
                         f"{len(fr)} frictions, last at "
                         f"{max(fr) if fr else 0:.0f}s; deltas {da:+.1f}/{db:+.1f}",
                         persists and ends_neg))

    def drift(name, char):
        # drift is measured from the DECLARED opening stance, not from frame 0
        # (the response loops may already have moved the surface by frame 0)
        h = r.channel_hist.get(f"{name}.manner", [])
        if not h:
            return 0.0
        anchor = getattr(char, "_dyad_anchor", h[0])
        return abs((sum(h[-3:]) / min(3, len(h))) - anchor)

    if abs(ca.temp.conviction - cb.temp.conviction) > 0.05:
        wa, wb = drift(an, ca), drift(bn, cb)
        who_moved = an if wa >= wb else bn
        verdicts.append((f"who gives ground: the looser-held self ({softer}) "
                         f"drifts further from their opening manner",
                         softer, f"{who_moved} (drift {an} {wa:.1f} vs {bn} {wb:.1f})",
                         who_moved == softer))

    notes = ["warmth correspondence is the robust axis; dominance reciprocity "
             "is staked at lower confidence (context-moderated in the literature)"]
    return DyadReport(a=an, b=bn, comp=comp, trajectory_forecast=traj,
                      verdicts=verdicts, notes=notes)
