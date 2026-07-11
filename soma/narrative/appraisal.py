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
