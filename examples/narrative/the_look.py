"""
the_look -- two people misreading each other, and the spiral it starts.

Ana and Ivo are across a table. Neither says the wrong thing; the trouble is
entirely in the reading. Ana is anxious and makes shame of Ivo's face; Ivo is
guarded and makes contempt of Ana's. And because each feeling shows on the face
the other is reading, the misreadings feed each other: her shame stiffens her
face, which he reads as coldness, which hardens his contempt, which shows, which
deepens her shame. Nobody intends any of it.

The simulation is built so the spiral is real and severable: cut one coupling
(one person stops reading the other's face) and the escalation should fall apart.

    python examples/narrative/the_look.py            # the dashboard
    python examples/narrative/the_look.py --source   # the generated SOMA
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from soma.narrative import Story, anxious, guarded


def build():
    story = Story("the_look", span="12s", step="1s", about="mutual misreading")

    ana = story.character("Ana", temperament=anxious)
    ivo = story.character("Ivo", temperament=guarded)

    # each reads the other's face, one second late
    ana.reads(ivo, "face", gain=1.0, lag="1s")
    ivo.reads(ana, "face", gain=1.0, lag="1s")

    # each makes a feeling of the other's face -- and the feeling SHOWS, so it
    # becomes the very signal the other misreads. shows_on + fades_to closes the
    # loop: the face gives them away, then composes, then gives them away again.
    # The gain is 1.0 (not attenuated): a face that reaches 9 clears the threat-
    # prior by enough to keep firing, so the spiral is mutual rather than
    # one-sided -- both of them misread, both of them escalate.
    ana.appraises("ivo_face", as_threat=True, feeling="shame",
                  shows_on="face", shows_value=9, fades_to=3, when="ivo_face > 4")
    ivo.appraises("ana_face", as_threat=True, feeling="contempt",
                  shows_on="face", shows_value=9, fades_to=3, when="ana_face > 4")

    # each keeps a mood: the evening's residue, rising as the spiral turns
    ana.has_mood("humiliation", fed_by="shame", decay=0.85)
    ivo.has_mood("disdain", fed_by="contempt", decay=0.85)

    ana.narrates(voice={"shame": "He sees straight through me."})
    ivo.narrates(voice={"contempt": "She wants something from me."})

    # one glance sets it off; after that the two faces drive each other
    story.at("2s", ana.shows("face", 9), ivo.shows("face", 9))
    story.at("6s", ana.shows("face", 9), ivo.shows("face", 9))
    return story


if __name__ == "__main__":
    story = build()
    print(story.source() if "--source" in sys.argv else story.run(width=88))
