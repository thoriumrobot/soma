"""
the_negotiator -- the most complete single character the library can express.

Cass runs hostage negotiations. She is, professionally, the calmest person in any
room. This simulation is built to show that the calm is a structure with a cost,
by putting every layer of the library on one person at once:

  * INTERNAL PARTS. Under pressure a loud protector ("the professional") bids for
    consciousness and wins; a quiet exile (the frightened child she once was)
    feels terror that never reaches awareness -- felt, never known.
  * THE RELATIONAL SELF. She is a different person with the man across the table
    (guarded, reading threat) than with the colleague on the radio in her ear
    (open, trusting) -- the same woman, two selves, indexed by whom she is with.
  * AMBIVALENCE. She wants the connection that would end the standoff and fears
    it in equal measure; the bond channel is pulled two ways and settles nowhere.
  * A VALUE, AND ITS BREACH. She holds "I never lie to the people I'm talking
    down" -- and breaks it every time she composes her voice into false calm.
  * CONFABULATION. The self that narrates all of this insists she is fine.

Run --character for the portrait; run the sift and the divided self is on the
page: the protector speaks, the exile is never ignited, the value is broken, the
bond is torn, and she is two people before the hour is out.

    python examples/narrative/the_negotiator.py            # the dashboard
    python examples/narrative/the_negotiator.py --character # the portrait
    python examples/narrative/the_negotiator.py --source    # the generated SOMA
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from soma.narrative import Story, guarded, tender


def build():
    story = Story("the_negotiator", span="20s", step="1s",
                  about="the cost of the calmest person in the room")

    story.scene("The call comes in", frm="0s", to="6s")
    story.scene("At the door", frm="7s", to="14s")
    story.scene("The long minute", frm="15s", to="20s")

    cass = story.character("Cass", temperament=guarded)
    # the two people she is with: the subject at the door, the colleague in her ear
    subject = story.character("Subject", temperament=tender)
    partner = story.character("Partner", temperament=tender)

    # --- the relational self: two people, from one body --------------------
    cass.with_person(subject, feeling="wariness", precision=0.85, conviction=0.3,
                     says="I hear you. I'm right here.")
    cass.with_person(partner, feeling="tenderness", precision=0.4, conviction=0.7,
                     says="Tell me you've got the back door.")

    # --- internal parts: the professional, and the child she was -----------
    cass.part("the-professional", role="protector", reacts_to="pressure",
              feeling="resolve", salience=0.95,
              says="I've done this a hundred times. Breathe. Work the problem.",
              when="pressure > 3")
    cass.part("the-child", role="exile", reacts_to="pressure",
              feeling="terror", salience=0.28, when="pressure > 3")

    # --- ambivalence: she wants the connection, and fears it ---------------
    cass.wants("rapport", toward=9, strength=0.28)
    cass.fears("rapport", toward=1, strength=0.28)

    # --- the value, and the composed voice that breaks it ------------------
    cass.has_body_signal("composed_voice", baseline=2)
    cass.appraises("pressure", as_threat=True, drives="composed_voice", to=8,
                   feeling="apprehension", when="pressure > 3", fades_to=2)
    cass.values("candor", says="I never lie to the ones I'm talking down.",
                betrayed_when="composed_voice > 6", on_channel="composed_voice")

    cass.has_mood("depletion", fed_by="apprehension", decay=0.9)
    cass.narrates(voice={
        "apprehension": "I'm fine. This is just the job.",
        "self_betrayal": "That wasn't a lie. That was the work.",
        "resolve": "Breathe. Work the problem.",
    })

    # the hour: pressure climbs, the faces come and go
    story.at("3s", cass.hears("pressure", 6), subject.shows("face", 7))
    story.at("6s", cass.hears("pressure", 8), partner.shows("face", 7))
    story.at("9s", cass.hears("pressure", 9), subject.shows("face", 8))
    story.at("12s", cass.hears("pressure", 7))
    story.at("15s", cass.hears("pressure", 9), subject.shows("face", 9))
    story.at("18s", cass.hears("pressure", 5), partner.shows("face", 6))
    return story


if __name__ == "__main__":
    story = build()
    if "--source" in sys.argv:
        print(story.source())
    elif "--character" in sys.argv:
        print(story.characterize(width=86))
    else:
        print(story.run(width=92))
