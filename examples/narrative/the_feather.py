"""
THE FEATHER -- system justification in THE UNMOORING, staged and priced.

The novel's quarter lives under a doctrine: the city does not rest on anything,
it is HELD, from above, by the virtue of the perch-lords who came down as
birds. A pillar-diver's widow, Neva, nails the lord's condolence-feather over
her door and says the truest sentence in the book: "If the city hangs from the
sky, my We died of bad luck. If it stands on the posts, he died of their
scrimping bronze -- and I owe the tide-rent either way. Let me have the luck."

That sentence is system justification theory, spoken from inside. This file
stages it with `soma.narrative.legitimacy` (Jost & Banaji 1994; Jost & Hunyady
2002; Laurin, Shepherd & Kay 2010; Wakslak et al. 2007; Friesen et al. 2019):

  I.   THE TRADE        Neva with the feather vs. the mother who will not look
                        at it: the same widowing, one belief apart. The belief
                        buys quiet and charges self-worth -- both, at once.
  II.  THE EXODUS CURVE the doctrine's grip as a function of INESCAPABILITY.
                        A legend of a homeland beyond the Sea of Stars is not
                        a destination; it is a solvent. Open the exit and the
                        same injuries that were suppressed become sufficient.
  III. THE MENDER'S YEAR conscientization, dosed: each session of "fight it,
                        break it, build it back" lowers the FELT inescapability
                        of the machine, and the boy's tipping point falls from
                        out-of-reach to within what the machine itself deals.
  IV.  THE NIGHT        the revelation staged: harm past the tipping point,
                        the belief breaks, the palliation stops -- the grief
                        comes back whole and the outrage becomes available.
                        That is the night the quarter takes the boats.

Run:
    python the_feather.py            # all four studies
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from soma.narrative import Story, guarded, stoic
from soma.narrative.legitimacy import (justifies, palliative_tradeoff,
                                       antecedent_dose, conscientize,
                                       derived_conviction)


# ---------------------------------------------------------------------------
# builders
# ---------------------------------------------------------------------------

def widow(inescapability=0.9, dependence=0.9):
    """Neva: raft-quarter, tide-rent due either way. Dependence and
    inescapability near the ceiling -- the exact regime Laurin et al. (2010)
    showed produces the strongest defense of the system."""
    s = Story("the_feather", span="16s", step="1s", about="acute distress")
    neva = s.character("Neva", temperament=guarded)
    justifies(neva, "perch", dependence=dependence,
              inescapability=inescapability,
              claim="If the city hangs from the sky, my We died of bad luck. "
                    "Let me have the luck.")
    return s


def drifter(inescapability):
    """A raft-quarter drifter as the homeland legend spreads: same dependence,
    same injuries -- only the thinkability of an exit changes."""
    s = Story("the_quarter", span="16s", step="1s", about="acute distress")
    d = s.character("Drifter", temperament=stoic)
    justifies(d, "perch", dependence=0.85, inescapability=inescapability)
    return s


def student(felt_inescapability):
    """Ink in the Cage. The walls are absolute; what the pilot's book changes
    is the FELT inescapability -- a charted sea beyond the machine exists."""
    s = Story("the_cage", span="16s", step="1s", about="acute distress")
    ink = s.character("Ink", temperament=guarded)
    justifies(ink, "machine", dependence=0.7,
              inescapability=felt_inescapability)
    return s


# ---------------------------------------------------------------------------
# I. the trade
# ---------------------------------------------------------------------------

def study_trade():
    print("=" * 74)
    print("I. THE TRADE — the feather over the door, priced")
    print("=" * 74)
    rep = palliative_tradeoff(widow, "Neva", harm=6.0)
    print(rep.render())
    print()
    print("  The WITH row is Neva; the WITHOUT row is the narrator's mother, "
          "who\n  'would never look at it.' The same widowing, one belief "
          "apart: Neva buys\n  the quiet and pays in worth; the mother keeps "
          "her worth and carries the\n  grief raw. Neither woman is a fool. "
          "The model prices what each knows.\n")


# ---------------------------------------------------------------------------
# II. the exodus curve
# ---------------------------------------------------------------------------

def study_exodus():
    print("=" * 74)
    print("II. THE EXODUS CURVE — a legend as a solvent")
    print("=" * 74)
    rep = antecedent_dose(drifter, "Drifter", dial="inescapability",
                          levels=(0.95, 0.75, 0.5, 0.25, 0.1))
    print(rep.render())
    print()
    print("  At the top of the curve the doctrine holds against everything "
          "the city\n  actually deals (the perch's harms run 5-6). At the "
          "bottom, those same\n  harms are past the threshold. Nobody's "
          "injuries changed; the legend of a\n  homeland beyond the Sea of "
          "Stars changed what the injuries were ALLOWED\n  TO MEAN. Laurin, "
          "Shepherd & Kay (2010), run in reverse: the exodus.\n")
    print("  And the lords: declining living standards are a SYSTEM THREAT, "
          "which\n  raises their own justification --")
    for t in (0.0, 0.5, 0.9):
        cv = derived_conviction(dependence=0.6, inescapability=0.6, threat=t)
        print(f"    threat {t:.1f}: the doctrine held at conviction {cv:.3f}")
    print("  -- the decline does not soften the perches; it hardens them, "
          "and the\n  hardening needs someone to blame. The scapegoating is "
          "the doctrine's\n  immune response.\n")


# ---------------------------------------------------------------------------
# III. the Mender's year
# ---------------------------------------------------------------------------

def study_mender():
    print("=" * 74)
    print("III. THE MENDER'S YEAR — conscientization, dosed")
    print("=" * 74)
    rep = conscientize(student, "Ink", start_inescapability=0.95,
                       per_session=0.11, sessions=(0, 2, 4, 6, 8))
    print(rep.render())
    print()
    print("  Laurin et al. (2010) predicts the Cage: restricted exit should "
          "make a\n  prisoner defend the machine MORE -- the standing-water "
          "look, the men who\n  went into it like a boot into mud. At zero "
          "sessions Ink is on that path.\n  The pilot's book is a charted sea "
          "the machine does not own; each argued\n  page lowers the felt "
          "inescapability of the world, and by the year's end\n  the "
          "machine's own ordinary harms are past his threshold. The Mender "
          "did\n  not comfort him. He un-held the belief the walls were "
          "holding.\n")


# ---------------------------------------------------------------------------
# IV. the night
# ---------------------------------------------------------------------------

def study_night():
    print("=" * 74)
    print("IV. THE NIGHT — the belief breaks, and what was quiet comes back")
    print("=" * 74)
    s = drifter(0.1)                        # the legend has done its work
    d = s.characters[0]
    for t in range(2, 12):
        s.at(f"{t}s", d.hears("harm", 6.0))  # the same harms as always
    s.run(width=74)
    r = s.result()
    seen = [k for k in r.channel_hist if k.endswith("_seen")][0]
    anx = r.channel_hist["anxiety"]
    outr = r.channel_hist["outrage"]
    broke = next((i for i, v in enumerate(r.channel_hist[seen]) if v > 5), None)
    print(f"  the belief breaks at beat {broke}: "
          f"anxiety {anx[2]:.0f} -> {max(anx):.0f} (the grief, whole), "
          f"outrage {outr[2]:.0f} -> {max(outr):.0f} (available at last)")
    revs = [e for e in r.chronicle if e.kind == "revelation"]
    if revs:
        n = len({e.who for e in revs})
        print(f"  chronicle: the belief's revelation is logged ({n} loop"
              f"{'s' if n != 1 else ''}) -- "
              f"'{revs[0].detail.get('note', '')}'")
    else:
        print("  chronicle: no revelation")
    print()
    print("  While the doctrine held, the same injury bought quiet at the "
          "price of\n  worth, and the anger was dampened (Wakslak et al., "
          "2007). The moment it\n  breaks, the palliation stops: the grief "
          "arrives whole and the outrage is\n  finally available to act on. "
          "That is the mechanism of the dark-of-moon\n  tide: a whole "
          "quarter's beliefs breaking within days of each other, every\n  "
          "widow's grief arriving at once, every dampened anger un-dampened. "
          "The\n  city did not get crueler that month. The door opened.\n")


if __name__ == "__main__":
    study_trade()
    study_exodus()
    study_mender()
    study_night()
