"""
soma.narrative.selfguides -- self-discrepancy: which BAD FEELING a failure makes.

Higgins' Self-Discrepancy Theory (Psychological Review, 1987) answers a question
every novelist needs answered and most tools cannot: why does the same failure
depress one character and make another anxious? The theory: the self has three
domains -- the ACTUAL self, the IDEAL self (aspirations; who they long to be)
and the OUGHT self (duties; who they are obliged to be) -- and the EMOTION
FAMILY a shortfall produces is decided by WHICH GUIDE it violates:

    actual falls short of IDEAL  ->  the absence of a hoped-for positive
                                     -> the DEJECTION family: disappointment,
                                        sadness, worthlessness, despair
    actual falls short of OUGHT  ->  the presence of a threatened negative
                                     -> the AGITATION family: apprehension,
                                        guilt, fear, unease

and the standpoint refines the quale: a guide held from one's OWN standpoint
yields disappointment (ideal) or guilt (ought); a guide held from ANOTHER's
standpoint yields shame (ideal -- falling short before someone) or fear (ought
-- a duty someone enforces). Higgins' surviving practical translation is
Regulatory Focus Theory (1997): ideal-dominant selves run a PROMOTION focus
(eager, gain-seeking, risk-tolerant), ought-dominant selves a PREVENTION focus
(vigilant, loss-avoiding, cautious) -- which this module exposes as a
disposition the decision layer can consume.

Honesty note, inherited from the replication literature: the emotion-SPECIFICITY
claim is the contested part. Ought->agitation is the cleaner unique link;
several studies find ideal and ought discrepancies both predicting depressed
affect (e.g. Tangney et al. 1998; Boldero & Francis 2005). The module therefore
predicts the FAMILY as the primary, falsifiable claim and the specific quale as
a default the author may override -- the same stance schema.py takes: a
typology of useful defaults, not a law.

What makes this a positive prediction: the author declares only the guides --
"she holds an ideal of her craft at 9", "he holds an ought to provide at 8" --
and NEVER names an emotion. The emotion family is derived, the compiled story
must produce the predicted quale in the Chronicle when the shortfall lands, and
the contrast is staged by construction: the SAME failure event, presented to
two characters whose guides differ only in kind, must produce dejection in one
and agitation in the other, or the theory (as encoded) is wrong.

Mechanically, a self-guide is what SOMA already believes a standard is: a loop
whose PRIOR is the guide, sensing the actual-self channel, with conviction set
by how deeply the guide is internalized. The discrepancy is the loop's
prediction error; the emission is gated on the actual self genuinely falling
short of the standard.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

# guide kind x standpoint -> (default quale, the theory's reading)
_QUALE = {
    ("ideal", "own"):   ("despair",       "the hoped-for self did not arrive (dejection)"),
    ("ideal", "other"): ("shame",         "falling short of an ideal before another (dejection)"),
    ("ought", "own"):   ("guilt",         "a duty of one's own, broken (agitation)"),
    ("ought", "other"): ("fear",          "a duty another enforces, threatened (agitation)"),
}
FAMILY = {"ideal": "dejection", "ought": "agitation"}


@dataclass(frozen=True)
class PredictedShortfall:
    """The forecast: which emotion family (the primary claim) and which default
    quale (overridable) a shortfall from this guide will produce, plus the
    regulatory focus the guide implies."""
    who: str
    guide: str            # "ideal" | "ought"
    domain: str           # the actual-self channel the guide watches
    standpoint: str       # "own" | "other"
    family: str           # "dejection" | "agitation"  -- the falsifiable claim
    quale: str            # the default emission (author-overridable)
    focus: str            # "promotion" | "prevention" -- Regulatory Focus Theory
    basis: str

    def gloss(self) -> str:
        return (f"{self.who}: shortfall on '{self.domain}' against an {self.guide} "
                f"({self.standpoint} standpoint) -> {self.family} family, "
                f"default quale '{self.quale}'; regulatory focus: {self.focus}. "
                f"[{self.basis}]")


def predict_shortfall(who, guide: str, domain: str, *,
                      standpoint: str = "own") -> PredictedShortfall:
    """Forecast the emotion a shortfall will produce, from the guide alone. The
    author supplies no emotion term; SDT's mapping supplies it."""
    if guide not in ("ideal", "ought"):
        raise ValueError("guide must be 'ideal' or 'ought'")
    if standpoint not in ("own", "other"):
        raise ValueError("standpoint must be 'own' or 'other'")
    name = who.name if hasattr(who, "name") else str(who)
    quale, basis = _QUALE[(guide, standpoint)]
    return PredictedShortfall(
        who=name, guide=guide, domain=domain, standpoint=standpoint,
        family=FAMILY[guide], quale=quale,
        focus="promotion" if guide == "ideal" else "prevention",
        basis=basis)


def install(char, *, guide: str, domain: str, standard: float = 9.0,
            standpoint: str = "own", internalized: float = 0.75,
            quale: Optional[str] = None) -> PredictedShortfall:
    """Give a character a self-guide and wire the machinery that makes the
    prediction testable.

    `domain` is an actual-self channel (created if absent) whose value is how
    the character is actually doing in that domain; `standard` is the guide's
    level. A loop is installed whose prior IS the standard, whose sense is the
    actual self, and whose conviction is `internalized` (how deep the guide
    goes). When the actual self falls materially short of the standard, the
    predicted quale fires -- and which quale that is was never typed by the
    author: it is derived from (guide, standpoint) by SDT's mapping.

    Returns the PredictedShortfall so a study (or a Preregistration) can stake
    the claim before running."""
    p = predict_shortfall(char, guide, domain, standpoint=standpoint)
    if quale is not None:                     # the author's override
        p = PredictedShortfall(**{**p.__dict__, "quale": quale})
    # the actual self in this domain: a channel resting at the standard (no
    # discrepancy until the story creates one).
    char.senses(domain, baseline=standard)
    # the guide loop: prior = the standard, held at `internalized` conviction;
    # precision high enough that a real shortfall is seen, and the emission
    # gated on the shortfall being material (more than a point below standard).
    char.appraises(domain,
                   expects=standard,
                   when=f"{domain} < {standard - 1.0}",
                   feeling=p.quale,
                   precision=0.9,
                   conviction=internalized,
                   updates=False)
    guides = getattr(char, "_selfguides", [])
    guides.append(p)
    char._selfguides = guides
    return p


def ideal(char, domain: str, *, standard: float = 9.0, standpoint: str = "own",
          internalized: float = 0.75, quale: Optional[str] = None):
    """Sugar: `ideal(nora, "her_craft")` -- an aspiration whose shortfall the
    theory predicts will DEJECT her."""
    return install(char, guide="ideal", domain=domain, standard=standard,
                   standpoint=standpoint, internalized=internalized, quale=quale)


def ought(char, domain: str, *, standard: float = 9.0, standpoint: str = "own",
          internalized: float = 0.75, quale: Optional[str] = None):
    """Sugar: `ought(theo, "providing")` -- an obligation whose shortfall the
    theory predicts will AGITATE him."""
    return install(char, guide="ought", domain=domain, standard=standard,
                   standpoint=standpoint, internalized=internalized, quale=quale)


def regulatory_focus(char) -> dict:
    """Read the character's regulatory focus off their installed guides
    (Higgins 1997: ideal-dominant -> promotion; ought-dominant -> prevention).
    Returns {"focus", "eagerness", "vigilance", "boundary_bias"} where
    `boundary_bias` is a multiplier the decision layer can apply to its
    decision boundary: a prevention focus decides more cautiously (higher
    boundary -- slower, fewer misses), a promotion focus more eagerly (lower
    boundary -- faster, more false alarms). Balanced or absent guides return a
    neutral 1.0."""
    guides = getattr(char, "_selfguides", [])
    ideals = sum(1 for g in guides if g.guide == "ideal")
    oughts = sum(1 for g in guides if g.guide == "ought")
    if ideals > oughts:
        return {"focus": "promotion", "eagerness": 0.7, "vigilance": 0.3,
                "boundary_bias": 0.8}
    if oughts > ideals:
        return {"focus": "prevention", "eagerness": 0.3, "vigilance": 0.7,
                "boundary_bias": 1.3}
    return {"focus": "balanced", "eagerness": 0.5, "vigilance": 0.5,
            "boundary_bias": 1.0}


def contrast(story, a, b, *, severity: float = 4.0, beats: int = 6) -> dict:
    """Stage SDT's signature experiment: present the SAME shortfall to two
    characters and check that each feels the family their guide predicts.

    For each character, the probe drops their guide's domain channel to
    `severity` (well below any standard) and reads which qualia fired. Returns
    {name: {"predicted_family", "predicted_quale", "felt", "confirmed"}} --
    `confirmed` is the falsification check: did the predicted quale actually
    fire in the probe's Chronicle?"""
    out = {}
    for who in (a, b):
        guides = getattr(who, "_selfguides", [])
        if not guides:
            raise ValueError(f"{who.name} has no installed self-guides")
        g = guides[0]
        p = story.predict(who, {g.domain: severity}, beats=beats)
        out[g.who] = {
            "predicted_family": g.family,
            "predicted_quale": g.quale,
            "felt": list(p.feelings),
            "confirmed": g.quale in p.feelings,
        }
    return out
