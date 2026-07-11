"""
soma.narrative.schema -- deriving personality structure from the wound.

Everywhere else in this library the author *specifies* a character's lie and need.
This module *predicts* them. It is the difference between a model that only replays
what you put in and one that makes a positive, falsifiable claim: give the wound
and how the character copes, and the library forecasts the belief they will hold,
what they will want, whom it will hurt, and how hard it will be to break -- a
prediction the author can accept, or override where the person they have in mind
departs from the type.

The mapping is grounded in Jeffrey Young's schema therapy as unified with
predictive processing (see e.g. "Early maladaptive schemas from child maltreatment
... a predictive coding framework", PMC12069367). The chain it encodes:

    unmet core need  ->  early maladaptive schema (a core self-belief)
                     ->  coping style (surrender / avoidance / overcompensation)
                     ->  a characteristic lie, want, and behaviour.

The three coping styles are the load-bearing prediction: the *same* wound yields
three very different people. Surrender accepts the schema and acts it out;
avoidance withdraws from whatever would trigger it; overcompensation does the
opposite, a grandiose denial. All three *perpetuate* the schema (that is why they
are maladaptive, and why the default arc tendency is "kept") -- which is exactly
SOMA's lie loop suppressing its own disconfirming evidence. What each coping style
also predicts is *how* the belief is held: how strong the conviction, how much the
disconfirming evidence is even let in, and therefore how a positive arc, if it
comes, would have to come.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PredictedLie:
    """A positive prediction: the belief a wound is expected to produce under a
    given coping style, plus the dynamics that decide how it will move."""
    schema: str            # the early maladaptive schema (the self-belief)
    claim: str             # the lie in the character's own voice
    feeling: str           # the affect the lie defends against
    want: str              # the conscious want the lie generates
    truth: str             # the need -- the salve, opposite of the lie
    harms: str             # "self" (psychological) or "others" (moral)
    behavior: str          # the characteristic behaviour to expect
    conviction: float      # how hard the coping holds it (higher = harder to break)
    trusts_evidence: float # sensory precision on the disconfirming channel (low =
                           #   the coping keeps disconfirmation out; harder to break)
    arc_tendency: str      # "kept" unless something can overwhelm the coping

    def gloss(self) -> str:
        return (f"{self.schema} coped with by {self._style()}: "
                f"\"{self.claim}\" -- wants {self.want}, harms {self.harms}; "
                f"expect: {self.behavior}.")

    def _style(self) -> str:
        return self.__dict__.get("_coping", "a coping style")


# The three coping styles, described so the prediction can be read.
COPING_STYLES = {
    "surrender": "accepts the schema as true and lives it out",
    "avoidance": "keeps clear of whatever would trigger the schema",
    "overcompensation": "does the opposite -- a grandiose denial of the schema",
}


# unmet need -> schema -> per-coping-style prediction. Compact but real: each entry
# is the shape schema therapy would predict, phrased for a character on a page.
_SCHEMAS = {
    "worth": {
        "schema": "Defectiveness / Shame (an inferior, unlovable self)",
        "feeling": "worthlessness",
        "surrender": dict(
            claim="I am the one who can be done without.",
            want="to be tolerated, to take up little",
            truth="that I am worth keeping for no reason",
            harms="self", conviction=0.95, trusts_evidence=0.3,
            behavior="self-erasing; takes less than offered; apologises for needing"),
        "avoidance": dict(
            claim="If I never test it, no one can find me wanting.",
            want="to not be measured",
            truth="that I am worth keeping for no reason",
            harms="self", conviction=0.9, trusts_evidence=0.2,
            behavior="withdraws from any contest; numbs; will not be seen to try"),
        "overcompensation": dict(
            claim="If I am not ranked above them, I am the surplus again.",
            want="rank, an upstairs, to be visibly above others",
            truth="that I matter as an equal",
            harms="others", conviction=1.1, trusts_evidence=0.3,
            behavior="climbs; dominates; needs there to be someone below"),
    },
    "belonging": {
        "schema": "Social Isolation / Alienation (I belong nowhere)",
        "feeling": "loneliness",
        "surrender": dict(
            claim="I'm always the outsider; I'll keep to the edge of the room.",
            want="to not be noticed as the one who doesn't fit",
            truth="that I am already one of them",
            harms="self", conviction=0.9, trusts_evidence=0.3,
            behavior="hangs back; refuses invitations before they're refused for him"),
        "avoidance": dict(
            claim="Better to leave first than to be shown the door.",
            want="to be gone before the belonging is tested",
            truth="that I am already one of them",
            harms="self", conviction=0.9, trusts_evidence=0.2,
            behavior="exits early; keeps every tie loose enough to drop"),
        "overcompensation": dict(
            claim="I belong here more than any of them.",
            want="to be the most inside of the insiders",
            truth="that I am already one of them",
            harms="others", conviction=1.05, trusts_evidence=0.3,
            behavior="performs the insider loudly; gatekeeps; polices who else fits"),
    },
    "safety": {
        "schema": "Mistrust / Abuse (people will use or betray me)",
        "feeling": "dread",
        "surrender": dict(
            claim="I'll be hurt in the end; better to expect it.",
            want="to see the betrayal coming",
            truth="that some hands can be trusted",
            harms="self", conviction=0.95, trusts_evidence=0.25,
            behavior="hypervigilant; submits to the stronger; braces for the blow"),
        "avoidance": dict(
            claim="Trust no one, need no one, and nothing can be taken.",
            want="to owe and be owed nothing",
            truth="that some hands can be trusted",
            harms="self", conviction=0.95, trusts_evidence=0.2,
            behavior="isolates; keeps exits; lets no one close enough to matter"),
        "overcompensation": dict(
            claim="I'll hurt them before they can hurt me.",
            want="control, the first strike",
            truth="that some hands can be trusted",
            harms="others", conviction=1.1, trusts_evidence=0.25,
            behavior="controlling; pre-emptive; treats care as a move in a game"),
    },
    "connection": {
        "schema": "Emotional Deprivation / Abandonment (no one will stay)",
        "feeling": "longing",
        "surrender": dict(
            claim="My needs won't be met, so I won't name them.",
            want="to need less, to ask for nothing",
            truth="that I can be met, and stayed with",
            harms="self", conviction=0.9, trusts_evidence=0.3,
            behavior="self-sufficient to a fault; won't ask; grateful for scraps"),
        "avoidance": dict(
            claim="Don't get close, and you can't get left.",
            want="distance kept before the leaving can happen",
            truth="that I can be met, and stayed with",
            harms="self", conviction=0.9, trusts_evidence=0.2,
            behavior="keeps love at arm's length; leaves before being left"),
        "overcompensation": dict(
            claim="I need no one.",
            want="to be the one who never needs",
            truth="that I can be met, and stayed with",
            harms="others", conviction=1.05, trusts_evidence=0.3,
            behavior="counter-dependent; scorns others' needs; provides, never asks"),
    },
    "autonomy": {
        "schema": "Subjugation / Enmeshment (my will does not count)",
        "feeling": "resentment",
        "surrender": dict(
            claim="I must go along, or be cast out.",
            want="to keep the peace by disappearing my own will",
            truth="that my will can stand and still be kept",
            harms="self", conviction=0.9, trusts_evidence=0.3,
            behavior="compliant; over-accommodating; resentful underneath"),
        "avoidance": dict(
            claim="Keep clear of anyone who could bind me.",
            want="to stay unbound",
            truth="that my will can stand and still be kept",
            harms="self", conviction=0.9, trusts_evidence=0.2,
            behavior="avoids commitment; bolts at the first pull of obligation"),
        "overcompensation": dict(
            claim="No one tells me anything.",
            want="to answer to no one",
            truth="that my will can stand and still be kept",
            harms="others", conviction=1.05, trusts_evidence=0.3,
            behavior="defiant; contrarian; refuses good counsel to prove he's free"),
    },
}

# friendly aliases for the unmet-need keys
_ALIASES = {
    "to-matter": "worth", "mattering": "worth", "worthiness": "worth",
    "esteem": "worth", "significance": "worth",
    "to-belong": "belonging", "inclusion": "belonging", "fitting-in": "belonging",
    "trust": "safety", "security": "safety",
    "love": "connection", "nurturance": "connection", "attachment": "connection",
    "freedom": "autonomy", "independence": "autonomy", "self-direction": "autonomy",
}


def unmet_needs():
    """The core needs the library can reason from (schema-therapy domains)."""
    return sorted(_SCHEMAS)


def predict_lie(unmet_need: str, coping: str = "overcompensation") -> PredictedLie:
    """Predict the lie a wound will produce under a coping style.

    This is the library making a *positive prediction* rather than being told the
    answer: from the unmet need and the coping style it forecasts the belief, the
    want, whom it harms, the behaviour to expect, and the dynamics (conviction and
    how much disconfirming evidence the coping lets in) that decide whether the lie
    can ever break. Falsifiable in the ordinary way -- if the character you have in
    mind would not say this, the wound or the coping is mis-named, or the person is
    an exception the type does not cover.

        >>> p = predict_lie("worth", "overcompensation")
        >>> p.claim
        'If I am not ranked above them, I am the surplus again.'
    """
    key = _ALIASES.get(unmet_need, unmet_need)
    if key not in _SCHEMAS:
        raise KeyError(f"unknown unmet need {unmet_need!r}; "
                       f"choose from {unmet_needs()} (or an alias)")
    if coping not in COPING_STYLES:
        raise KeyError(f"unknown coping style {coping!r}; "
                       f"choose from {sorted(COPING_STYLES)}")
    entry = _SCHEMAS[key]
    c = entry[coping]
    p = PredictedLie(
        schema=entry["schema"], claim=c["claim"], feeling=entry["feeling"],
        want=c["want"], truth=c["truth"], harms=c["harms"],
        behavior=c["behavior"], conviction=c["conviction"],
        trusts_evidence=c["trusts_evidence"], arc_tendency="kept")
    object.__setattr__(p, "_coping", coping)
    return p
