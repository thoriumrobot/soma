"""
four_ways_of_leaving: the 0.8 prediction layers, end to end.

One person leaves a room. The library predicts, before any run, four different
people it could happen to -- and then the confabulation gap that only one of
them will show; the emotion a verdict will produce in a fifth person who was
never told what to feel; what happens between two cold negotiators who
correspond perfectly and can't stand each other; and it seals every claim in a
preregistration before checking any of them.

Everything here is a forecast first and a run second. Where a forecast fails,
the report says FALSIFIED -- that is the point of the instrument.

    python3 examples/narrative/four_ways_of_leaving.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from soma.narrative import (Story, anxious, stoic, trusting, guarded, volatile,
                            predict_feeling, predict_pull, Stance)


def separations():
    """Four attachment styles; one separation probe; four staked forecasts."""
    print("=" * 72)
    print("I. FOUR WAYS OF BEING LEFT (soma.narrative.attachment)")
    print("=" * 72)
    for style, temp in (("secure", trusting), ("anxious", anxious),
                        ("avoidant", stoic), ("disorganized", guarded)):
        story = Story(f"leaving_{style}", span="12s", step="1s",
                      about="separation distress")
        mara = story.character("Mara", temperament=temp)
        mara.attaches(style, to="Jonah")
        print()
        print(story.predict_separation("Mara").render())


def the_verdict():
    """The author supplies the appraisal; the library derives the emotion --
    and then must produce it."""
    print()
    print("=" * 72)
    print("II. THE VERDICT SHE NEVER NAMED (soma.narrative.appraisal)")
    print("=" * 72)
    # theory-side, before any story exists:
    pf = predict_feeling(congruence=-0.9, agency="other", certainty=0.9,
                         coping=0.2)
    print(f"\n  appraisal: harmful, other-caused, certain, powerless")
    print(f"  {pf.gloss()}")

    story = Story("the_verdict", span="8s", step="1s")
    vera = story.character("Vera", temperament=anxious)
    vera.senses("verdict")
    vera.appraises_event("verdict", congruence=-0.9, agency="other",
                         certainty=0.9, coping=0.2,
                         when="verdict > 5", drives="heart", to=112,
                         fades_to=72)
    story.at("2s", vera.hears("verdict", 9))

    audit = story.preregister()
    audit.expect_feeling("Vera", pf.quale, by="4s")
    audit.expect_peak("Vera", "heart", at_least=105)
    print()
    print(audit.check().render())


def the_negotiation():
    """Two cold, dominant people: perfect correspondence on warmth, collision
    on dominance -- structurally complementary, affectively corrosive."""
    print()
    print("=" * 72)
    print("III. THE NEGOTIATION (soma.narrative.circumplex)")
    print("=" * 72)
    pull = predict_pull(Stance(dominance=0.6, warmth=-0.6))
    print(f"\n  Rook's opening {Stance(0.6, -0.6).octant()} move {pull.gloss()}")
    print()
    story = Story("the_negotiation", span="14s", step="1s")
    rook = story.character("Rook", temperament=guarded).stance(
        dominance=0.6, warmth=-0.6)
    wren = story.character("Wren", temperament=volatile).stance(
        dominance=0.5, warmth=-0.5)
    story.meet(rook, wren)
    print(story.predict_dyad(rook, wren).render())


if __name__ == "__main__":
    separations()
    the_verdict()
    the_negotiation()
