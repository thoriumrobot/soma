"""
the_house -- a three-generation saga, in ~40 lines of narrative intent.

A fear enters a family with the grandmother, who has a reason for it. It passes
to her daughter, who inherits the vigilance without the memory, and hardens it
into a way of living. It reaches the granddaughter only as a weather she cannot
name -- and the question the simulation asks is whether it reaches her at all.

This exercises most of soma.narrative at once: three characters on the biography
clock, couplings that carry a surface (never an interior) down the generations,
somatic memory with no story attached, dissociation as a supervisor that crashes
and repairs, learning that hardens a prior into a life, and moods -- the slow
variable that lets a feeling become a decade.

    python examples/narrative/the_house.py             # the dashboard
    python examples/narrative/the_house.py --source    # the generated SOMA
    python examples/narrative/the_house.py --prose     # as free indirect prose
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from soma.narrative import Story, numb, anxious, guarded, tender, arc


def build():
    story = Story("the_house", span="90y", step="1y", cadence=True,
                  about="inherited trauma across three generations")

    story.scene("The war she survived",     frm="0y",  to="28y")
    story.scene("The daughter's vigilance",  frm="29y", to="58y")
    story.scene("The granddaughter's weather", frm="59y", to="90y")

    # --- Vera: the original wound -----------------------------------------
    # Numb by disposition -- the signal lands softly -- but the memory is intact
    # and fires without a story. When the threat overwhelms her, she dissociates.
    vera = story.character("Vera", temperament=numb, clock="life")
    vera.senses("gunfire")
    vera.appraises("gunfire", as_threat=True, drives="heart", to=150,
                   feeling="terror", shows_on="face", shows_value=9, fades_to=2)
    vera.feels("dread", from_body="heart")
    vera.remembers("the_field", cued_by="gunfire", when_above=5, evokes="panic")
    vera.dissociates_when(appraisal="gunfire", exceeds=4,
                          detaching="interoception", repair_after="6y")
    vera.has_mood("desolation", fed_by="dread", relieved_by=None, decay=0.9)
    vera.narrates(downplaying={"terror": "It was a long time ago. I am fine now."})

    # --- Ada: inherits vigilance without the cause ------------------------
    # She reads her mother's face across her childhood, and makes a threat of it.
    # Anxious, and she LEARNS -- the watching hardens into a way of living.
    ada = story.character("Ada", temperament=anxious, clock="life")
    ada.reads(vera, "face", gain=0.7, lag="1y")
    ada.appraises("vera_face", as_threat=True, feeling="dread",
                  updates=True, stops_seeing=True, when="vera_face > 3",
                  shows_on="face", shows_value=8, fades_to=1)
    ada.learns(0.05)
    ada.has_mood("apprehension", fed_by="dread", decay=0.88)
    ada.narrates(voice={"dread": "Something isn't right. I can always tell."})

    # --- Mira: the weather she cannot name --------------------------------
    # Tender, three generations from the field. She reads her mother -- but the
    # signal is thin now, and whether it becomes a feeling at all is the question
    # the perturbation at the bottom of this file asks.
    mira = story.character("Mira", temperament=tender, clock="life")
    mira.reads(ada, "face", gain=0.45, lag="1y")
    mira.appraises("ada_face", as_threat=True, feeling="unease",
                   when="ada_face > 2.5")
    mira.has_mood("disquiet", fed_by="unease", decay=0.8)
    mira.narrates(voice={"unease": "I don't know why. I just feel it sometimes."})

    # --- the war comes in waves, early, and then recedes ------------------
    # Intermittent, not continuous: each wave sends terror down the generations,
    # and the quiet between waves lets each face compose itself again -- so the
    # transmission is visible, and severable.
    waves = [("3y", 9), ("4y", 1), ("7y", 8), ("8y", 1),
             ("12y", 9), ("13y", 1), ("18y", 7), ("19y", 1), ("24y", 2)]
    for (t, v) in waves:
        story.at(t, vera.hears("gunfire", v))
    return story


if __name__ == "__main__":
    story = build()
    if "--source" in sys.argv:
        print(story.source())
    elif "--prose" in sys.argv:
        print(story.prose(genders={"Vera": "she", "Ada": "she", "Mira": "she"}))
    else:
        print(story.run(width=88))
