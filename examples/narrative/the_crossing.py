"""
THE CROSSING -- what holds a fleet together, and what carries it across.

THE UNMOORING's second half is a voyage: a quarter's worth of drifters in
salvaged boats, crossing seven seas toward a homeland that exists in a legend
and nowhere else confirmed. Two questions decide whether that story is
believable, and this file stages both with soma.narrative:

  I.   THE TWO LOYALTIES   Why does the fleet hold when the city didn't?
                           Goldhaven's order ran on the DOCTRINAL mode --
                           routinized observance, the descent-feast rows --
                           which makes identification: loyalty as a bet. The
                           fleet's bond is made the IMAGISTIC way -- the Maw,
                           the storms, the shared dysphoria, reflected on in
                           the night watches -- which makes fusion: loyalty as
                           self (Whitehouse & Lanman, 2014; Swann et al.,
                           2012; Jong et al., 2015). Defeat re-prices a bet.
                           It cannot re-price a self.
  II.  THE PRICE           What each bond pays in the worst hour (Topman
                           holding the course over the Maw; the Coat's eleven
                           days at the gate). The fused pay what the
                           identified only applaud.
  III. THE DYAD            Ink has the ways (a boy made of charts and books);
                           Sound has the will (first over the side, always).
                           Snyder's hope theory (1994-2002): hope = agency x
                           pathways, multiplicative. Alone, each half fails
                           its own way. Pooled, they cross.
  IV.  THE SEVEN SEAS      The crossing itself as a hope trajectory: seven
                           blockages, agency fed by each one overcome (the
                           catalog of past effectiveness) -- and the
                           counterfactual crossing without the Mender's
                           pathways, which turns back in the third sea.

Run:
    python the_crossing.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from soma.narrative.fusion import (derived_fusion, derived_identification,
                                   sacrifice_table, defeat_curve)
from soma.narrative.hope import voyage, hope_surface, dyad


def study_loyalties():
    print("=" * 74)
    print("I. THE TWO LOYALTIES — a bet, and a self")
    print("=" * 74)
    perch = derived_identification(participation=0.85)
    fleet = derived_fusion(intensity=0.9, reflection=0.8)
    print(f"  the perch's bond (doctrinal: feast-rows, gate-letters, "
          f"tide-rent): {perch:.3f}")
    print(f"  the fleet's bond (imagistic: the Maw, reflected on in the "
          f"watches): {fleet:.3f}")
    print()
    print(defeat_curve([("the perch's identification", "identified", perch),
                        ("the fleet's fusion", "fused", fleet)],
                       defeats=3, reflection=0.8).render())
    print()
    print("  On a calm day the two loyalties measure nearly the same. Then "
          "the hard\n  year comes: the doctrinal bond falls by more than "
          "half at the first defeat\n  — which is why a declining city must "
          "find someone to blame (see 0.25's\n  threat study) — while the "
          "fused bond barely moves, because a shared defeat,\n  reflected "
          "on, is one more share of the thing the bond is made of.\n")


def study_price():
    print("=" * 74)
    print("II. THE PRICE — what each bond pays in the worst hour")
    print("=" * 74)
    fleet = derived_fusion(intensity=0.9, reflection=0.8)
    perch = derived_identification(participation=0.85)
    unshared = derived_fusion(intensity=0.9, reflection=0.8, shared=False)
    print(sacrifice_table([
        ("fused at the Maw (the fleet)", "fused", fleet),
        ("descent-feast rows (the perch)", "identified", perch),
        ("same ordeal, borne alone", "fused", unshared),
    ]).render())
    print()
    print("  The third row is the control the theory demands: the same "
          "storm, suffered\n  alone, transforms a person without fusing them "
          "to anyone — intensity\n  without communion. Topman aloft over the "
          "Maw and the Coat's eleven days at\n  the gate are the first row's "
          "receipts: the fused pay what the identified\n  only applaud.\n")


def study_dyad():
    print("=" * 74)
    print("III. THE DYAD — will, ways, and the pair as one agent")
    print("=" * 74)
    print(hope_surface(levels=(0.2, 0.5, 0.8), blockages=7,
                       samples=20).render())
    print()
    print(dyad(blockages=7, samples=20, stores=90).render())
    print()
    print("  Sound is the first row's failure: first over the side, and "
          "shattered at\n  the third closed strait, because a wall does not "
          "answer to courage. Ink is\n  the second: a boy made of charts who "
          "can find a route around anything and\n  cannot make himself owed "
          "the attempt. The book's central pair is a single\n  high-hope "
          "agent in two bodies, and the model says so with a number.\n")


def study_seven_seas():
    print("=" * 74)
    print("IV. THE SEVEN SEAS — the crossing, and the counterfactual")
    print("=" * 74)
    with_book = voyage(0.85, 0.85, who="the fleet (the Mender's pathways)",
                       blockages=7, seed=11, max_beats=90)
    print(with_book.render())
    print()
    # the counterfactual, honestly: over twenty seeded crossings, not one
    # lucky draw. Without the book, pathways thinking is what a mixed crowd
    # improvises (0.2): most crossings turn back, and early.
    def fates(p, label):
        outs = [voyage(0.85, p, blockages=7, seed=1000 + s * 17,
                       max_beats=90) for s in range(20)]
        reach = sum(v.reached for v in outs)
        backs = sorted(v.blockages_met for v in outs if not v.reached)
        mid = backs[len(backs) // 2] if backs else None
        print(f"  {label}: {reach}/20 crossings reach"
              + (f"; the rest turn back around sea {mid}" if backs else ""))
    fates(0.85, "with the book   (pathways 0.85)")
    fates(0.20, "without the book (pathways 0.20)")
    print()
    print("  The same boats, the same seas, the same courage — twenty "
          "crossings each.\n  With the Mender's pathways every one reaches, "
          "and each strait passed feeds\n  the next attempt (agency rising: "
          "the catalog of past effectiveness). With\n  will alone, most "
          "crossings turn back in the middle seas. The Mender never\n  "
          "crossed anything. He is why the crossing works.\n")


if __name__ == "__main__":
    study_loyalties()
    study_price()
    study_dyad()
    study_seven_seas()
