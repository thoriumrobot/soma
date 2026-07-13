"""
the_strange_situation: the canonical probe, run whole, and turned on itself.

Ainsworth's Strange Situation is the most consequential standardized experiment
in the study of character: eight scripted episodes -- play, a stranger, two
separations, two reunions -- and a coding scheme that reads a child's whole
relational pattern from four behaviors in the two reunions. This simulation
runs the entire protocol on SOMA children and then makes the strongest claim a
model of the instrument can make:

  I.    four children, one script    the same eight episodes produce four
                                     textbook-distinct coded profiles
  II.   construct validity           the classifier never sees the installed
                                     style, only the behavior stream -- and
                                     must recover all four (parameter recovery,
                                     the identifiability standard)
  III.  the child nobody labeled     a hand-built child, no style installed
                                     from the table, classified honestly from
                                     tape -- what the instrument is FOR
  IV.   what the tape can't show     the avoidant child's narrated calm over a
                                     racing heart, preregistered and checked

    python3 examples/narrative/the_strange_situation.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from soma.narrative import (Story, trusting, anxious, stoic, guarded,
                            strange_situation, validate_instrument)


TEMPS = {"secure": trusting, "anxious": anxious,
         "avoidant": stoic, "disorganized": guarded}


def child_with(style):
    s = Story(f"ss_{style}", span="24s", step="1s",
              about="separation distress in a standardized protocol")
    child = s.character("Noa", temperament=TEMPS[style])
    child.attaches(style, to="mother")
    return s, child


def study():
    print("=" * 74)
    print("I. FOUR CHILDREN, ONE SCRIPT — the protocol codes them apart")
    print("=" * 74)
    for style in TEMPS:
        s, c = child_with(style)
        print()
        print(f"  [installed: {style} — the coder below never sees this]")
        print(strange_situation(s, c).render())

    print()
    print("=" * 74)
    print("II. CONSTRUCT VALIDITY — blind recovery of every installed style")
    print("=" * 74)
    results = validate_instrument(child_with)
    print()
    for style in TEMPS:
        mark = "✓" if results[style] == style else "✗"
        print(f"    {mark} installed {style:<13s} -> classified {results[style]}")
    print(f"\n    INSTRUMENT {'VALID' if results['recovered'] else 'INVALID'}: "
          f"{'all four styles recovered from behavior alone' if results['recovered'] else 'recovery failed'}")

    print()
    print("=" * 74)
    print("III. THE CHILD NOBODY LABELED — classification as discovery")
    print("=" * 74)
    # a hand-built child: no style bundle. High-precision alarm, a hair-trigger
    # protest, contact sought hard but never soothing -- built from raw verbs,
    # the way an author actually works.
    s = Story("ss_unlabeled", span="24s", step="1s",
              about="separation distress in a standardized protocol")
    kit = s.character("Kit", temperament=anxious)
    kit.senses("mother_near", baseline=8.0)
    kit.appraises("mother_near", as_threat=True, when="mother_near < 3",
                  drives="heart", to=122, fades_to=101, precision=0.97,
                  conviction=0.2, expects=8.0,
                  shows_on="protest_face", shows_value=9.0)
    kit.feels("dread", from_body="heart", threshold=95.0)
    kit.appraises("mother_near", when="mother_near * heart > 650",
                  shows_on="clings", shows_value=9.0, expects=8.0)
    kit.appraises("mother_near", when="mother_near * heart > 700",
                  shows_on="protest_face", shows_value=8.0, expects=8.0)
    kit._attachment = dict(style="?", figure="mother", near="mother_near",
                           resting=72.0, arousal_to=122.0)
    rep = strange_situation(s, kit)
    print()
    print(rep.render())
    print("\n  (No table was consulted. The tape says who this child is: the")
    print("  clinging that will not soothe — coded as the pattern it matches.)")

    print()
    print("=" * 74)
    print("IV. WHAT THE TAPE CAN'T SHOW — preregistered, then checked")
    print("=" * 74)
    s, c = child_with("avoidant")
    audit = s.preregister()
    audit.expect_gap("Noa", at_least=0.4)      # says calm...
    audit.expect_peak("Noa", "heart", at_least=95)  # ...over a racing heart
    audit.expect_feeling("Noa", "dread")
    # run the protocol timeline through the same story so the claims are
    # checked against the actual Strange Situation, not an empty room
    rep = strange_situation(s, c)   # (installs the protocol wiring)
    print()
    print("  The avoidant child LOOKS calm on the tape. The instrument that")
    print("  sees both registers — the narrated account and the body's own")
    print("  record — was preregistered to find them split:")
    print()
    print(f"  physiological arousal over displayed calm: "
          f"{'PRESENT — confirmed' if rep.physio_over_display else 'absent — falsified'}"
          f" (peak {rep.detail['peak']}, classified {rep.classification})")
    print("\n  (Sroufe & Waters 1977; Diamond et al. 2006: the A-pattern's")
    print("  independence is a performance the heart never joins.)")


if __name__ == "__main__":
    study()
