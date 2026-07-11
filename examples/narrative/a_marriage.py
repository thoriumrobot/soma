"""
a_marriage, in the narrative library: thirty years, and a prior that hardens.

The `learns()` rate is the whole tragedy. Every time Soren's model of Mira is
confirmed, his conviction rises, until she can no longer surprise him -- and the
delight that depended on surprise becomes its absence. The `arc.wobble` gives
her a living, varying face for twenty-four years; then the chair is empty and
the prior goes on predicting her anyway.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from soma.narrative import Story, tender, arc


def build():
    story = Story("a_marriage", span="30y", step="1y", cadence=True,
                  about="the slow erosion of intimacy, and grief")

    soren = story.character("Soren", temperament=tender, clock="life")
    soren.senses("her_face", baseline=5)
    # low conviction + being wrong = delight; learning turns it to certainty.
    # updates=True: he revises his picture of her. stops_seeing=True: once the
    # hardened prior outranks his senses, he stops taking her in.
    soren.appraises("her_face", feeling="delight_at_error", when="her_face > 1",
                    precision=0.75, conviction=0.2,
                    updates=True, stops_seeing=True)
    soren.learns(0.055)
    # and when her face is gone -- the channel fallen to nothing where a person
    # used to be -- the same body that delighted now grieves. It goes on
    # expecting her (expects=5); finding absence is the error that becomes grief.
    soren.appraises("her_face", feeling="grief", when="her_face < 1",
                    expects=5, precision=0.9, conviction=0.2, learn=0.0)
    soren.narrates(voice={"delight_at_error": "She surprised me. Still.",
                          "grief": "The house is so quiet now."})

    # her face varies for 24 years, then she is gone
    face = arc.wobble(around=5, span="24y", every="2y") + arc.hold(0, at="25y")
    for (t, v) in face:
        story.at(t, soren.hears("her_face", v))
    return story


if __name__ == "__main__":
    story = build()
    print(story.source() if "--source" in sys.argv else story.run(width=88))
