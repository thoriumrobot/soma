"""
legitimacy.py -- system justification: the belief that holds the holder.

The layer models the psychology of legitimizing ideology -- why the people a
system injures so often defend it -- and what loosens the grip. It is grounded
in system justification theory:

  * Jost & Banaji (1994); Jost & Hunyady (2002), "The psychology of system
    justification and the palliative function of ideology": system-justifying
    beliefs REDUCE anxiety, guilt, dissonance, and uncertainty -- for the
    advantaged and the disadvantaged alike. The belief is load-bearing.
  * Jost & Thompson (2000); Bahamondes-Correa (2016): for the DISADVANTAGED the
    same belief costs self-regard and long-run wellbeing even while it quiets
    the day's anxiety -- a genuine double-edged trade, not a simple delusion.
  * Friesen, Laurin, Shepherd, Gaucher & Kay (2019): three contextual
    antecedents raise the motive -- system THREAT, system DEPENDENCE, and
    system INESCAPABILITY.
  * Laurin, Shepherd & Kay (2010), "Restricted emigration, system
    inescapability, and defense of the status quo": make a system harder to
    leave and people defend it MORE, even in unrelated domains. The inverse is
    the lever of every exodus: open an exit, and the grip breaks.
  * Wakslak, Jost, Tyler & Chen (2007): system justification DAMPENS moral
    outrage, and through outrage, the will to change anything. The belief does
    not only soothe; it dissolves the anger that would act.

In SOMA the legitimizing belief is an ordinary high-conviction prior wired
with `believes(...)`: it predicts the system's harm channel reads low, and so
suppresses the injuries as they arrive. What this layer adds is that the
conviction is not authored -- it is DERIVED from the person's context by the
three antecedents, and the palliative trade is wired into the body: while the
belief holds, anxiety is driven down (the palliative function) and, for the
disadvantaged, self-worth is driven down with it (the internalization cost),
and outrage is suppressed. When the belief breaks -- `overwhelm`, the standard
self-revelation machinery -- the palliation stops, the grief comes back whole,
and the outrage becomes available.

Because conviction is derived, every downstream prediction is too:

    justifies(neva, "the_perch", dependence=0.9, inescapability=0.9)
    story.tipping_point("Neva", "harm")     # -> never, in [0, 9]
    justifies(mara, "the_perch", dependence=0.9, inescapability=0.3)
    story.tipping_point("Mara", "harm")     # -> breaks at a modest harm

The exodus in one line: `inescapability` is the dial, and a legend of a
homeland beyond the Sea of Stars is not a destination -- it is a solvent.

Instruments:

  * justifies(char, system, ...)      -- wire the belief + the palliative trade
  * palliative_tradeoff(builder, who) -- WITH vs WITHOUT the belief: anxiety
                                         down, worth down. The trade, priced.
  * antecedent_dose(builder, dial, levels)
                                      -- tipping point as a function of one
                                         antecedent: the exodus curve.
  * conscientize(builder, who, sessions)
                                      -- Freire's critical consciousness as a
                                         dose: each session of dialogic
                                         challenge lowers felt inescapability
                                         and raises trust in one's own reading;
                                         returns the tipping point per dose.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Optional

from .story import Story, Character


# ---------------------------------------------------------------------------
# conviction from context: the three antecedents
# ---------------------------------------------------------------------------

def derived_conviction(*, dependence: float, inescapability: float,
                       threat: float = 0.0, base: float = 0.28) -> float:
    """How hard the legitimizing belief is held, from the person's context.

    Friesen et al. (2019) name three antecedents that raise the system
    justification motive: dependence, inescapability, and threat. Each is a
    [0, 1] dial. The weights make inescapability the strongest single lever
    (Laurin et al., 2010, found restricted exit raising defense of the system
    even in unrelated domains), dependence next, threat the mildest.
    """
    for name, v in (("dependence", dependence),
                    ("inescapability", inescapability), ("threat", threat)):
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"{name} must be in [0, 1], got {v}")
    conv = base + 0.34 * inescapability + 0.26 * dependence + 0.10 * threat
    return round(min(conv, 0.98), 3)


def derived_evidence_trust(*, dependence: float, inescapability: float,
                           threat: float = 0.0) -> float:
    """The precision granted to the evidence of the system's harm -- MOTIVATED
    IGNORANCE (Friesen et al., 2019: "motivated ignorance of critical social
    issues"). The same antecedents that raise conviction lower how much the
    injuries are allowed to count: the less you can leave, the less you can
    afford to see."""
    trust = 0.40 - 0.26 * inescapability - 0.10 * dependence - 0.04 * threat
    return round(max(trust, 0.05), 3)


# ---------------------------------------------------------------------------
# the wiring
# ---------------------------------------------------------------------------

@dataclass
class Justification:
    """What `justifies` wired, so studies can read the derivation back."""
    who: str
    system: str
    dependence: float
    inescapability: float
    threat: float
    conviction: float
    disadvantaged: bool
    lie: str

    def gloss(self) -> str:
        tag = "disadvantaged" if self.disadvantaged else "advantaged"
        return (f"{self.who} justifies '{self.system}' ({tag}): conviction "
                f"{self.conviction} derived from dependence "
                f"{self.dependence:g} + inescapability {self.inescapability:g}"
                f" + threat {self.threat:g}. While the belief holds, anxiety "
                f"is quieted"
                + (" and self-worth pays for the quiet."
                   if self.disadvantaged else "."))


def justifies(char: Character, system: str, *, dependence: float,
              inescapability: float, threat: float = 0.0,
              disadvantaged: bool = True, palliative: float = 0.75,
              claim: Optional[str] = None,
              feeling: str = "grief") -> Justification:
    """Give `char` a legitimizing belief about `system`, with the conviction
    DERIVED from context and the palliative trade wired into the body.

    Channels created (shared names, so studies can read them):
      * harm      -- extero: evidence of the system's injury to them
      * anxiety   -- intero: the negative arousal the belief exists to quiet
      * worth     -- intero: self-regard, which pays for the quiet (if
                     disadvantaged; Jost & Thompson, 2000)
      * outrage   -- intero: the will to act, dampened while the belief holds
                     (Wakslak et al., 2007)

    The belief itself is `the_<system>_is_just`, a `believes(...)` lie with
    `disconfirmed_by='harm'` and `breakable=True`, so the standard overwhelm /
    tipping-point machinery applies: WHETHER and WHEN it breaks falls out of
    the derived conviction, i.e. out of the person's dependence and exits.
    """
    conv = derived_conviction(dependence=dependence,
                              inescapability=inescapability, threat=threat)
    trust = derived_evidence_trust(dependence=dependence,
                                   inescapability=inescapability,
                                   threat=threat)
    lie = f"the_{system}_is_just"
    if claim is None:
        claim = (f"The {system} is what there is. If it is just, my losses "
                 f"were bad luck; let me have the luck.")

    char.has_body_signal("anxiety", baseline=55.0)
    char.has_body_signal("worth", baseline=60.0)
    char.has_body_signal("outrage", baseline=20.0)

    # The legitimizing belief: predicts the harm channel reads low, suppresses
    # it when it reads high, hardens with each suppression, and can break.
    char.believes(lie, claim=claim, disconfirmed_by="harm",
                  conviction=conv, feeling=feeling, harms="self",
                  breakable=True, learn=0.02, evidence_trust=trust)

    # Every palliation loop below is GATED ON THE BELIEF ITSELF via the lie's
    # `_seen` channel (0 while the belief holds; driven to 9 at the
    # self-revelation). The guard `harm - 2 * <seen> > K` fires on injury only
    # while the belief is unbroken, and shuts off the moment it is seen -- so
    # perturbing or breaking the belief removes the quiet, mechanically.
    seen = f"{lie}_seen"

    # The palliative function: while the belief holds, injury is met with the
    # legitimizing quiet -- anxiety is driven DOWN (Jost & Hunyady, 2002; van
    # der Toorn et al., 2015: given the chance to legitimize, arousal drops).
    char.appraises("harm", when=f"harm - 2 * {seen} > 2", drives="anxiety",
                   to=max(10.0, 55.0 - 45.0 * palliative), fades_to=55.0,
                   precision=0.9, conviction=0.2)

    # The cost (disadvantaged only): the same quiet is paid for in self-regard
    # -- internalization of the system's low regard (Jost & Thompson, 2000).
    if disadvantaged:
        char.appraises("harm", when=f"harm - 2 * {seen} > 2", drives="worth",
                       to=max(10.0, 60.0 - 40.0 * conv), fades_to=60.0,
                       precision=0.9, conviction=0.2)

    # After the revelation: the grief comes back whole, and the outrage
    # becomes available (Wakslak et al., 2007, in reverse: with the
    # justification gone, nothing dampens the anger that acts).
    char.appraises(seen, when=f"{seen} > 5", drives="anxiety", to=88.0,
                   fades_to=55.0, precision=0.9, conviction=0.2,
                   feeling="the_grief_whole")
    char.appraises(seen, when=f"{seen} > 5", drives="outrage", to=85.0,
                   fades_to=20.0, precision=0.9, conviction=0.2)

    return Justification(who=char.name, system=system, dependence=dependence,
                         inescapability=inescapability, threat=threat,
                         conviction=conv, disadvantaged=disadvantaged, lie=lie)


# ---------------------------------------------------------------------------
# study 1: the trade, priced
# ---------------------------------------------------------------------------

@dataclass
class TradeReport:
    who: str
    with_belief: dict           # {"anxiety": mean, "worth": mean}
    without_belief: dict
    palliation: float           # anxiety spared by the belief (+ = calmer)
    cost: float                 # worth paid for it (+ = worth lost)

    def render(self) -> str:
        from soma.viz import bar
        w, wo = self.with_belief, self.without_belief
        rows = []
        for ch in ("anxiety", "worth"):
            rows.append(f"  {ch:<8} with belief  "
                        f"{bar(w[ch] / 100.0, 20)} {w[ch]:5.1f}")
            rows.append(f"  {'':<8} without      "
                        f"{bar(wo[ch] / 100.0, 20)} {wo[ch]:5.1f}")
        return (f"THE TRADE — {self.who}, the same injury, with and without "
                f"the belief:\n" + "\n".join(rows) + "\n"
                f"  the belief buys {self.palliation:.1f} points of quiet and "
                f"charges {self.cost:.1f} points of worth.\n"
                f"  'Let me have the luck' is not a delusion; it is a priced "
                f"purchase.")


def _mean_channel(result, who: str, channel: str, multi: bool) -> float:
    key = f"{who}.{channel}" if multi else channel
    hist = result.channel_hist.get(key) or result.channel_hist.get(channel)
    if not hist:
        return float("nan")
    return sum(hist) / len(hist)


def palliative_tradeoff(builder: Callable[[], Story], who: str, *,
                        harm: float = 7.0, beats: int = 10) -> TradeReport:
    """Price the belief. `builder` returns a fresh Story whose `who` has been
    wired with `justifies(...)`. The study stages the same sustained injury
    twice -- once as built, once with the legitimizing belief's conviction
    perturbed to nothing -- and reads mean anxiety and worth off the body.

    Prediction (Jost & Hunyady 2002; Jost & Thompson 2000): WITH the belief,
    anxiety is lower AND worth is lower. The belief is simultaneously a
    comfort and a tax, which is what the theory means by palliative.
    """
    def staged(perturb_off: bool) -> dict:
        s = builder()
        multi = len(s.characters) > 1
        ch = f"{who}.harm" if multi else "harm"
        target = next(c for c in s.characters if c.name == who)
        for t in range(2, 2 + beats):
            s.at(f"{t}s", target.hears("harm", harm))
        overrides = {}
        if perturb_off:
            # find the justifying loop and unhold it -- BOTH dials. A
            # legitimizing belief is a high conviction AND a motivated
            # distrust of the evidence; "without the belief" means without
            # the whole believing structure, so the injuries are both allowed
            # to count (precision up) and allowed to win (conviction down).
            from soma import parse
            for lp in parse(s.source()).loops:
                if lp.name.startswith("the_lie_") and "_is_just" in lp.name:
                    overrides[f"{lp.name}.conviction"] = 0.05
                    overrides[f"{lp.name}.precision"] = 0.9
        from .insight import run_with
        r = run_with(s, overrides) if overrides else s.result()
        return {"anxiety": round(_mean_channel(r, who, "anxiety", multi), 1),
                "worth": round(_mean_channel(r, who, "worth", multi), 1)}

    w = staged(False)
    wo = staged(True)
    return TradeReport(who=who, with_belief=w, without_belief=wo,
                       palliation=round(wo["anxiety"] - w["anxiety"], 1),
                       cost=round(wo["worth"] - w["worth"], 1))


# ---------------------------------------------------------------------------
# study 2: the exodus curve
# ---------------------------------------------------------------------------

@dataclass
class DoseReport:
    who: str
    dial: str
    rows: list                  # (level, conviction, tipping)

    def render(self) -> str:
        from soma.viz import bar, track
        out = [f"THE EXODUS CURVE — {self.who}: tipping point of the belief "
               f"as {self.dial} falls",
               f"  {'':>{len(self.dial) + 6}}  conviction"
               f"{'':<16}breaking harm  0{'':<8}9"]
        for level, conv, tip in self.rows:
            t = ("never, in [0, 9]" if tip is None
                 else f"breaks at harm >= {tip:g}")
            out.append(f"  {self.dial} {level:>4.2f}  {conv:.3f} "
                       f"{bar(conv, 14)}  {track(tip, 0, 9, 10)} {t}")
        out.append("  An exit is not a destination. It is a solvent.")
        return "\n".join(out)


def antecedent_dose(make_story: Callable[[float], Story], who: str, *,
                    dial: str = "inescapability",
                    levels=(0.9, 0.6, 0.3, 0.1),
                    channel: str = "harm") -> DoseReport:
    """The novel's central mechanism, quantified. `make_story(level)` builds a
    fresh Story with the antecedent under study set to `level` (the caller
    passes it into `justifies`). For each level the study asks the standard
    tipping-point question: the least sustained harm at which the legitimizing
    belief BREAKS -- or `never`.

    Prediction (Laurin et al., 2010, run in reverse): at high inescapability
    the belief holds against everything the system ordinarily deals (and at
    the extreme of all three antecedents it does not break in range at all);
    open the exit and the very same injuries that were suppressed become
    sufficient. The person did not change. The door did.
    """
    rows = []
    for level in levels:
        s = make_story(level)
        # read the derived conviction back off the wired character
        conv = None
        for c in s.characters:
            if c.name == who:
                for l in c._lies:
                    if "_is_just" in l.name:
                        conv = round(float(l.conviction), 3)
        tp = s.tipping_point(who, channel)
        tip = tp.get("breaks_at") if isinstance(tp, dict) else None
        rows.append((level, conv, tip))
    return DoseReport(who=who, dial=dial, rows=rows)


# ---------------------------------------------------------------------------
# study 3: conscientization -- the Mender's pedagogy, dosed
# ---------------------------------------------------------------------------

@dataclass
class ConscientizationReport:
    who: str
    rows: list                  # (sessions, inescapability_felt, tipping)

    def render(self) -> str:
        from soma.viz import bar, track
        out = [f"CONSCIENTIZATION — {self.who}: the dialogic dose "
               f"(Freire, 1970; Watts & Diemer)",
               f"                 felt inescapability      "
               f"breaking harm  0        9"]
        for n, e, tip in self.rows:
            t = ("never, in [0, 9]" if tip is None
                 else f"breaks at harm >= {tip:g}")
            out.append(f"  {n:>2} sessions:  {e:.2f} {bar(e, 14)}  "
                       f"{track(tip, 0, 9, 10)} {t}")
        out.append("  The walls did not move. The book made the sea beyond "
                   "them thinkable,\n  and a thinkable exit un-holds the "
                   "belief the walls were holding.")
        return "\n".join(out)


def conscientize(make_story: Callable[[float], Story], who: str, *,
                 start_inescapability: float = 0.95,
                 per_session: float = 0.11,
                 sessions=(0, 2, 4, 6, 8)) -> ConscientizationReport:
    """Freire's critical consciousness as a dose-response. Problem-posing
    dialogue does two things this layer can express with one dial: it makes
    the world readable as CHANGEABLE -- each session lowers the FELT
    inescapability of the system (the walls stay; the sense that they are all
    there is does not). `make_story(felt_inescapability)` wires the student at
    that level; the study reports the tipping point per dose.

    Prediction: at zero sessions the breaking point sits above what the
    machine ordinarily deals (the student is on Neva's path); each session
    lowers it until the same injuries suffice. Teaching someone to read the
    machine is, mechanically, teaching them the door exists.
    """
    rows = []
    for n in sessions:
        e = max(0.05, start_inescapability - per_session * n)
        s = make_story(e)
        tp = s.tipping_point(who, "harm")
        tip = tp.get("breaks_at") if isinstance(tp, dict) else None
        rows.append((n, e, tip))
    return ConscientizationReport(who=who, rows=rows)
