"""
five_marriages: the Gottman-Murray model, run as five marriages.

Gottman and Murray's mathematics of marriage is the most famous predictive
character simulation there is: parameters read off minutes of one conversation
predicted divorce years out. This simulation rebuilds the model in SOMA -- the
influence functions are couple/lag readings, the negative threshold is a guard
level, repair is an interoceptive bid, emotional inertia is conviction -- and
runs the same contentious conversation through all five couple types.

  I.    five couples, one complaint   the typology's forecasts, checked
  II.   the thin slice                the ending forecast from the first
                                      quarter alone -- the minutes-to-years
                                      claim, in-model and falsifiable
  III.  what saves a hostile couple   minimal intervention: is it the skin
                                      (negative threshold) or the repair?
  IV.   the anatomy of the cascade    negative-affect reciprocity as the
                                      absorbing state, measured

    python3 examples/narrative/five_marriages.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from soma.narrative import Story, tender, trusting, COUPLE_TYPES, marry, gottman_assess


def couple(type_name):
    s = Story(f"marriage_{type_name}", span="20s", step="1s")
    a = s.character("Ash", temperament=trusting)
    b = s.character("Bee", temperament=tender)
    marry(s, a, b, type_name)
    return s


def study():
    print("=" * 74)
    print("I. FIVE COUPLES, ONE COMPLAINT — the typology's forecasts, checked")
    print("=" * 74)
    reports = {}
    for tname in COUPLE_TYPES:
        rep = gottman_assess(couple(tname))
        reports[tname] = rep
        print()
        print(rep.render())

    print()
    print("=" * 74)
    print("II. THE THIN SLICE — the ending, forecast from the first quarter")
    print("=" * 74)
    print()
    print("  couple             slice says   the marriage      forecast")
    hits = 0
    for tname, rep in reports.items():
        actual = "holds" if any("REGULATED" in v[0] and v[3] for v in rep.verdicts) \
                 or rep.stable_forecast and rep.confirmed else "falls"
        # read the actual from the thin-slice verdict's observed field
        thin_v = next(v for v in rep.verdicts if "THIN SLICE" in v[0])
        actual = thin_v[2]
        ok = thin_v[3]
        hits += ok
        print(f"    {tname:<16s} {rep.thin_forecast:<12s} {actual:<16s} "
              f"{'✓ correct' if ok else '✗ wrong'}")
    print(f"\n  {hits}/{len(reports)} endings called from the first quarter of "
          f"one conversation.")
    print("  (Gottman's claim was 94% from minutes of tape; here the mechanism")
    print("  that makes it possible is visible: the slice carries the couple's")
    print("  thresholds, and the thresholds ARE the ending.)")

    print()
    print("=" * 74)
    print("III. WHAT SAVES A HOSTILE COUPLE — the skin, or the repair?")
    print("=" * 74)
    # A hostile couple's two broken dials: a thin skin (friction triggers at
    # received manner <= 4.5) and no repair. Which single change un-cascades
    # them? We test the skin directly: thicken it (lower the guard) until the
    # marriage holds. Repair can't be added by a dial (it is absent wiring),
    # which is itself the finding Gottman's interventions reflect: you can
    # teach repair, but the model must first contain a bid to strengthen.
    s = couple("hostile")
    rep = s.minimal_intervention(
        target=("mood_drift", 0.0),
        dials={"Ash.appraising_their_manner_friction.precision": (0.1, 0.9),
               "Bee.appraising_their_manner_friction.precision": (0.1, 0.9)},
        character="Ash", mood="rapport", steps=16)
    print()
    print(rep.render())
    print()
    print("  (Lowering the friction loop's precision is 'thickening the skin':")
    print("  the same received coldness carries less weight. The instrument")
    print("  reports whether any single skin-thickening saves this marriage,")
    print("  or whether the cascade is over-determined without repair.)")

    print()
    print("=" * 74)
    print("IV. THE ANATOMY OF THE CASCADE — reciprocity as the absorbing state")
    print("=" * 74)
    print()
    print("  couple             negative reciprocity")
    for tname, rep in reports.items():
        bar = "#" * int(rep.reciprocity * 30)
        print(f"    {tname:<16s} {rep.reciprocity:>4.0%}  {bar}")
    print()
    print("  The unstable couples answer friction with friction nearly every")
    print("  beat — Gottman's absorbing state: once in, the cascade feeds")
    print("  itself. The regulated couples' reciprocity is near zero not")
    print("  because nothing negative arrives, but because it is absorbed —")
    print("  by a thicker skin, by repair, or by disengagement.")


if __name__ == "__main__":
    study()
