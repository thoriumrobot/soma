"""
soma.narrative.appraisal -- predicting the feeling from the appraisal.

Everywhere else in this library the author *names* the feeling an event produces
(`feels("dread")`, `appraises(..., feeling="grief")`). This module predicts it.
The author supplies only the *appraisal* of the event -- was it good or bad for
my goals, who caused it, how certain is it, can I do anything about it, did it
break a standard I hold -- and the library forecasts which discrete emotion the
character will feel and what they will be moved to do about it.

The mapping is the convergent core of appraisal theory: Scherer's Component
Process Model and its sequential checks (relevance, implication, coping
potential, normative significance), Smith & Ellsworth's dimensional analysis,
Roseman's motive-consistency/agency structure, and the OCC model's
event/agent/standard branches. These theories differ in detail but converge on
the claim this module encodes: A SPECIFIC PATTERN OF APPRAISAL PREDICTS A
SPECIFIC EMOTION -- other-blame with power predicts anger where the same loss
without power predicts fear or grief; self-blame against a standard predicts
guilt (about the act) or shame (about the self); goal-conducive uncertainty
predicts hope where certainty predicts joy. Frijda supplies the second half of
each forecast: every emotion carries an action tendency (anger moves against,
fear moves away, shame hides, guilt repairs, grief withdraws and searches).

Why this counts as a positive prediction rather than accommodation: the emotion
term never appears in the author's input. It is derived from independently
grounded theory, and the compiled story must then *produce* it -- the forecast
quale has to actually fire in the Chronicle when the appraised event lands, or
the model is wrong. `Preregistration.expect_feeling` is the natural check.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class PredictedFeeling:
    """A forecast: the discrete emotion a given appraisal pattern will produce,
    with Frijda's action tendency and the theoretical basis spelled out."""
    quale: str             # the predicted feeling (a SOMA quale name)
    tendency: str          # Frijda action tendency: what it moves them to do
    intensity: float       # 0..1, from relevance x |congruence|
    appraisal: dict        # the input pattern, kept for the record
    basis: str             # which appraisal-theoretic branch predicted this

    def gloss(self) -> str:
        return (f"predicted feeling: {self.quale} (tendency: {self.tendency}, "
                f"intensity {self.intensity:.2f}) -- {self.basis}")


# Frijda-style action tendencies, one per predicted emotion.
TENDENCIES = {
    "anger":        "move against -- confront, oppose, remove the obstacle",
    "resentment":   "withhold -- oppose without power, at a distance, in time",
    "fear":         "move away -- avoid, escape, make oneself small",
    "dread":        "scan -- hypervigilance toward a threat not yet located",
    "grief":        "withdraw and search -- deactivate, and reach for what is gone",
    "frustration":  "persist -- push harder against a blockable obstacle",
    "guilt":        "repair -- undo the act, confess, make amends",
    "shame":        "hide -- conceal the self, withdraw from being seen",
    "regret":       "disengage -- turn from the path that led here",
    "hope":         "sustain -- keep the goal lit and keep moving toward it",
    "joy":          "engage -- open toward, continue, share",
    "relief":       "recover -- release the braced body, stand down",
    "pride":        "display -- show the achieving self to others",
    "gratitude":    "approach -- move toward and credit the other",
}


def predict_feeling(*, congruence: float, agency: str = "circumstance",
                    certainty: float = 0.7, coping: float = 0.5,
                    norm_compatible: bool = True, norm_focus: str = "act",
                    was_feared: bool = False,
                    relevance: float = 1.0) -> Optional[PredictedFeeling]:
    """Forecast the emotion from the appraisal pattern.

    congruence      -1..1  goal-conduciveness: was the event bad (-) or good (+)
                           for what the character wants?
    agency          who caused it: "self" | "other" | "circumstance"
    certainty       0..1   how settled the event is (uncertain futures vs done facts)
    coping          0..1   control/power: can anything be done about it?
    norm_compatible did the event (if self-caused) respect the character's
                    standards? False engages the OCC standards branch.
    norm_focus      "act" (guilt: I *did* a bad thing) or "self" (shame: I *am*
                    the bad thing) -- the classic guilt/shame distinction.
    was_feared      a good outcome that had been braced against reads as relief,
                    not joy (goal-conducive after expected obstruction).
    relevance       0..1   goal relevance; scales intensity. Below ~0.15 nothing
                    is predicted -- an irrelevant event moves no one.

    Returns None when the pattern predicts no emotion (irrelevant or flat).
    """
    if relevance < 0.15 or abs(congruence) < 0.1:
        return None
    intensity = max(0.0, min(1.0, relevance * abs(congruence)))
    appr = dict(congruence=congruence, agency=agency, certainty=certainty,
                coping=coping, norm_compatible=norm_compatible,
                norm_focus=norm_focus, was_feared=was_feared,
                relevance=relevance)

    def out(quale, basis):
        return PredictedFeeling(quale=quale, tendency=TENDENCIES[quale],
                                intensity=intensity, appraisal=appr, basis=basis)

    # ---- goal-obstructive branch (congruence < 0) ---------------------------
    if congruence < 0:
        if agency == "other":
            if certainty < 0.5:
                return out("fear", "other-caused harm still uncertain: "
                           "threat without a settled fact (Scherer: low certainty "
                           "+ obstruction -> fear family)")
            if coping >= 0.5:
                return out("anger", "other-blame with power: obstruction + "
                           "other-agency + coping potential (Smith & Ellsworth; "
                           "Roseman; OCC blameworthiness)")
            return out("resentment", "other-blame without power: the anger "
                       "pattern minus control (Scherer: low power turns "
                       "antagonism inward or into time)")
        if agency == "self":
            if not norm_compatible:
                if norm_focus == "self":
                    return out("shame", "self-caused standard violation, "
                               "focused on the self (Lewis; Tracy & Robins: "
                               "shame is about who I am)")
                return out("guilt", "self-caused standard violation, focused "
                           "on the act (OCC standards branch; guilt repairs)")
            return out("regret", "self-caused obstruction without a standard "
                       "broken: a path wrongly taken (decision-theoretic "
                       "regret; Roseman self-agency)")
        # circumstance
        if certainty < 0.5:
            return out("dread", "obstruction, uncertain, no one to blame: "
                       "anxious scanning (Scherer: low certainty + low "
                       "predictability -> anxiety/dread)")
        if coping < 0.5:
            return out("grief", "a certain, uncontrollable loss: nothing to "
                       "fight and no one to fight (Ellsworth & Scherer: "
                       "certainty + low coping -> sadness/grief)")
        return out("frustration", "a certain obstruction that could still "
                   "yield: coping potential keeps it a fight (Scherer: "
                   "obstruction + power -> instrumental persistence)")

    # ---- goal-conducive branch (congruence > 0) ------------------------------
    if certainty < 0.5:
        return out("hope", "a good outcome not yet settled (OCC prospect-based "
                   "branch: desirable + unconfirmed -> hope)")
    if was_feared:
        return out("relief", "a good outcome where a bad one was braced for "
                   "(OCC: disconfirmed fear -> relief)")
    if agency == "self":
        return out("pride", "self-caused good against a standard met (OCC "
                   "attribution branch: praiseworthy self-agency)")
    if agency == "other":
        return out("gratitude", "other-caused good (OCC: praiseworthy "
                   "other-agency -> gratitude)")
    return out("joy", "a certain, conducive event (Scherer: conduciveness + "
               "certainty -> enjoyment/joy)")


# Distress qualia this module can predict -- the compiler's consent gate should
# know about the ones the base checker does not already list.
PREDICTABLE_DISTRESS = {"fear", "anger", "resentment", "grief", "dread",
                        "shame", "guilt", "regret", "frustration"}


# ---------------------------------------------------------------------------
# inverse inference: from an observed emotion, recover the appraisal
# ---------------------------------------------------------------------------
#
# Appraisal theory's central claim is bidirectional (Smith & Ellsworth 1985:
# emotions and appraisals map onto each other). The forward direction --
# appraisal -> emotion -- is predict_feeling above. The inverse -- emotion ->
# the appraisal that must have produced it -- is the stronger, more falsifiable
# claim, because it is what lets an observer reason from behaviour back to the
# construal, and because it is only well-posed if the forward mapping is
# IDENTIFIABLE (distinct emotions come from distinct appraisal regions). This
# section provides the inverse and a construct-validity check that the two
# directions are mutually consistent across the whole emotion vocabulary.

# the canonical appraisal signature behind each emotion: the region of appraisal
# space that predict_feeling maps to it. Written as human-readable constraints;
# `explain_emotion` returns them, and `recover_appraisal` returns a concrete
# representative that predict_feeling round-trips back to the same emotion.
_SIGNATURES = {
    "anger":       dict(congruence=-0.8, agency="other", certainty=0.9, coping=0.8),
    "resentment":  dict(congruence=-0.8, agency="other", certainty=0.9, coping=0.2),
    "fear":        dict(congruence=-0.8, agency="other", certainty=0.3, coping=0.5),
    "dread":       dict(congruence=-0.7, agency="circumstance", certainty=0.2, coping=0.3),
    "grief":       dict(congruence=-0.9, agency="circumstance", certainty=0.95, coping=0.1),
    "frustration": dict(congruence=-0.7, agency="circumstance", certainty=0.9, coping=0.8),
    "guilt":       dict(congruence=-0.7, agency="self", certainty=0.9, coping=0.5,
                        norm_compatible=False, norm_focus="act"),
    "shame":       dict(congruence=-0.7, agency="self", certainty=0.9, coping=0.5,
                        norm_compatible=False, norm_focus="self"),
    "regret":      dict(congruence=-0.7, agency="self", certainty=0.9, coping=0.5,
                        norm_compatible=True),
    "hope":        dict(congruence=0.6, agency="circumstance", certainty=0.3),
    "relief":      dict(congruence=0.7, agency="circumstance", certainty=0.9,
                        was_feared=True),
    "pride":       dict(congruence=0.7, agency="self", certainty=0.9),
    "gratitude":   dict(congruence=0.7, agency="other", certainty=0.9),
    "joy":         dict(congruence=0.7, agency="circumstance", certainty=0.9),
}

# the plain-language reading of each appraisal dimension, for explanations.
_DIMENSION_GLOSS = {
    "congruence": lambda v: ("good for what they wanted" if v > 0
                             else "bad for what they wanted"),
    "agency":     lambda v: {"self": "they caused it",
                             "other": "someone else caused it",
                             "circumstance": "no one caused it"}[v],
    "certainty":  lambda v: "it is settled" if v >= 0.5 else "it is still uncertain",
    "coping":     lambda v: "something can be done" if v >= 0.5 else "nothing can be done",
    "norm_compatible": lambda v: "no standard was broken" if v else "a standard was broken",
    "norm_focus": lambda v: {"act": "the act was wrong", "self": "the self is wrong"}[v],
    "was_feared": lambda v: "the bad outcome had been braced for" if v else "",
}


def recover_appraisal(emotion: str) -> dict:
    """Inverse inference: given an observed emotion, return an appraisal pattern
    that produces it. Raises if the emotion is outside the vocabulary. The
    returned pattern is guaranteed to round-trip (predict_feeling of it yields
    the same emotion) -- see check_identifiability."""
    if emotion not in _SIGNATURES:
        raise ValueError(f"{emotion!r} is not in the appraisal vocabulary: "
                         f"{sorted(_SIGNATURES)}")
    return dict(_SIGNATURES[emotion])


def explain_emotion(emotion: str) -> str:
    """A plain-language account of the appraisal behind an emotion -- what a
    character must have construed for this feeling to be the one that fired.
    This is the observer's inference: feeling -> the reading of the world that
    produced it, with its Frijda action tendency."""
    sig = recover_appraisal(emotion)
    parts = []
    for dim, val in sig.items():
        g = _DIMENSION_GLOSS.get(dim)
        if g:
            phrase = g(val)
            if phrase:
                parts.append(phrase)
    tendency = TENDENCIES.get(emotion, "")
    return (f"{emotion}: they construed that " + ", ".join(parts)
            + f" — and so are moved to {tendency}")


def check_identifiability() -> dict:
    """Construct validity, the same standard the Strange Situation meets: the
    forward and inverse mappings must be mutually consistent. For every emotion
    the module can predict, recover its appraisal and run it forward again; the
    result must be the same emotion. A failure means the emotion is not
    identifiable from appraisal -- two feelings share a region -- which would
    make the prediction ill-posed. Returns the per-emotion round-trip result and
    whether all recovered.
    """
    rows = {}
    for emotion in _SIGNATURES:
        recovered = recover_appraisal(emotion)
        pf = predict_feeling(**recovered)
        rows[emotion] = (pf.quale if pf else None)
    ok = all(v == k for k, v in rows.items())
    return dict(rows=rows,
                recovered=ok,
                n=len(rows),
                n_correct=sum(1 for k, v in rows.items() if v == k))
