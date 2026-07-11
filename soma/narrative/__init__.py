"""
soma.narrative -- a high-level library for writing novelistic simulations.

The core language asks an author to think in loops, precisions, clocks, and
arbitration. This library lets them think in *characters, feelings, and beats*
instead, and compiles that down to ordinary SOMA source -- so every safety and
correctness guarantee of the base language still holds, and the output can be
run, sifted, prosed, and perturbed exactly like a hand-written program.

    from soma.narrative import Story, anxious, stoic

    story = Story("the_phone_call", span="6s", step="0.5s",
                  about="acute distress")

    nadia = story.character("Nadia", temperament=anxious)
    nadia.senses("ear")                       # a channel onto the world
    nadia.appraises("ear", as_threat=True)    # a loop that reacts to it
    nadia.feels("dread", when_body="alarmed") # viscera -> feeling
    nadia.narrates(downplaying={"dread": "I'm fine. I just need to write this down."})

    story.at("1.5s", nadia.hears("ear", 9))   # the sentence lands

    print(story.run())                        # the dashboard, as text
    print(story.source())                     # the SOMA source it generated

The library is deliberately small and composable: `Story`, `Character`,
`Temperament`, and a set of verb-methods on Character (`senses`, `appraises`,
`feels`, `narrates`, `reads`, `remembers`, `dissociates_when`, `learns`,
`has_mood`, `has_attention`). Appraisals can drive the body (`drives`), show a
feeling on a surface (`shows_on`/`fades_to`), cost attention (`effortful`), and
harden with use (`updates`/`stops_seeing`). `Story.over(arc, ...)` spreads an
Arc across the timeline. Each verb records intent; `.source()` renders the whole
thing to SOMA.
"""

from .temperament import (Temperament, anxious, stoic, trusting, guarded,
                          volatile, numb, tender, hollowed, TEMPERAMENTS)
from .story import Story, Character
from .arc import Arc, arc
from .schema import predict_lie, unmet_needs, COPING_STYLES, PredictedLie
from .appraisal import predict_feeling, PredictedFeeling, TENDENCIES
from .attachment import STYLES as ATTACHMENT_STYLES, AttachmentStyle, SeparationReport
from .circumplex import (Stance, predict_pull, complementarity, Pull,
                         DyadReport)
from .preregister import Preregistration, Report as PreregReport
from .insight import run_with, outcome, series
from .sensitivity import sensitivity, SensitivityReport
from .discriminate import discriminate, DiscriminationReport
from .earlywarning import predict_break_onset, EarlyWarningReport
from .counterfactual import (minimal_intervention, CounterfactualReport,
                             Intervention)

__all__ = [
    "Story", "Character", "Temperament", "Arc", "arc",
    "anxious", "stoic", "trusting", "guarded", "volatile", "numb", "tender",
    "hollowed", "TEMPERAMENTS",
    "predict_lie", "unmet_needs", "COPING_STYLES", "PredictedLie",
]
