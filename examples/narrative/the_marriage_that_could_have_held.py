"""
the_marriage_that_could_have_held: the study layer turned on a slow curdling.

Soren's delight in Mira depends on her surprising him -- delight_at_error, a
low-conviction prior being sweetly wrong. His `learn` rate is the tragedy dial:
every firing hardens the prior, and the curdling is not that the flicker of
feeling stops -- it is that the ROUTE flips. Early, a surprise routes to
`perceive`: she moves him, his picture of her revises. Late, the same surprise
routes to `act`: he resists it, defends the picture, and the feeling that still
fires is a feeling *about* his model, not about her. Nothing visible changes.
That is the point.

Four studies, each a question a novelist actually asks about this marriage:

  I.    the run              when the route flips: the year he stops taking her in
  II.   sensitivity          is the tragedy the learning, or the trusting?
  III.  counterfactual       the smallest change to him that keeps him open
  IV.   the last good year   the latest year one extraordinary day still REACHES
                             him -- a point of no return, computed, not asserted

Study IV is composed directly from the insight substrate (run_with + the
chronicle) rather than a canned instrument: the substrate is the API, the
instruments are just its most common compositions.

    python3 examples/narrative/the_marriage_that_could_have_held.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from soma.narrative import Story, tender, arc, run_with, outcome


LOOP = "appraising_her_face"
YEAR = 31557600.0            # one soma year, in the seconds the Chronicle keeps


def build(extraordinary_day=None, learn=0.08):
    """The marriage. If `extraordinary_day` is (year, value), one unscripted,
    astonishing day is inserted -- the intervention Study IV searches over."""
    s = Story("the_marriage", span="30y", step="1y", cadence=True,
              about="the slow erosion of intimacy")
    soren = s.character("Soren", temperament=tender, clock="life")
    soren.senses("her_face", baseline=5)
    soren.appraises("her_face", feeling="delight_at_error", when="her_face > 1",
                    precision=0.75, conviction=0.2,
                    updates=True, stops_seeing=True)
    soren.learns(learn)
    s.over(arc.wobble(around=5, span="24y", every="1y", unit="y", amplitude=3),
           lambda v: soren.hears("her_face", v))
    if extraordinary_day is not None:
        year, value = extraordinary_day
        s.at(f"{year}y", soren.hears("her_face", value))
    return s


def study():
    print("=" * 74)
    print("I. THE RUN — the year he stops taking her in")
    print("=" * 74)
    r = run_with(build())
    beats = [(e.t / YEAR, e.detail["route"]) for e in r.chronicle
             if e.kind == "settle" and e.who.endswith(LOOP)]
    first_act = next((y for y, route in beats if route == "act"), None)
    last_perc = max((y for y, route in beats if route == "perceive"), default=None)
    frac = outcome(r, "perceive_frac", character="Soren")
    print(f"\n  her face goes on varying for 24 years. He takes it in "
          f"(`perceive`) for the")
    print(f"  early marriage; the route first flips to resisting (`act`) at "
          f"year {first_act:.0f},")
    print(f"  and the last beat that truly reaches him is year {last_perc:.0f}. "
          f"Over the whole")
    print(f"  marriage the world gets in on only {frac:.0%} of beats. The "
          f"delight still")
    print(f"  flickers afterward — but it is delight at his own model, "
          f"defended.\n")

    print("=" * 74)
    print("II. SENSITIVITY — is the tragedy the learning, or the trusting?")
    print("=" * 74)
    rep = build().sensitivity(
        params={f"{LOOP}.learn": (0.0, 0.12),
                f"{LOOP}.conviction": (0.05, 0.6),
                f"{LOOP}.precision": (0.4, 0.95)},
        outcome_name="perceive_frac", character="Soren",
        n_base=24, seed=11)
    print()
    print(rep.render())
    print()
    print("  (The outcome is the fraction of his life the world still gets in.)")
    print()

    print("=" * 74)
    print("III. COUNTERFACTUAL — the smallest change that keeps him open")
    print("=" * 74)
    base_frac = outcome(run_with(build()), "perceive_frac", character="Soren")
    print(f"\n  target: the world gets in on at least half his beats "
          f"(baseline: {base_frac:.0%}).")
    rep = build().minimal_intervention(
        target=("perceive_frac", 0.5),
        dials={f"{LOOP}.learn": (0.0, 0.08),
               f"{LOOP}.conviction": (0.05, 0.2),
               f"{LOOP}.precision": (0.75, 0.98)},
        character="Soren", steps=16)
    print()
    print(rep.render())
    print()

    print("=" * 74)
    print("IV. THE LAST GOOD YEAR — a point of no return, computed")
    print("=" * 74)
    print("\n  One extraordinary day — her face at 9.5, utterly unforeseen —")
    print("  inserted at year Y. Does it still REACH him (route: perceive),")
    print("  or does he resist it (route: act)?\n")
    last_good = None
    for year in range(2, 26, 2):
        r = run_with(build(extraordinary_day=(year, 9.5)))
        routes = [e.detail["route"] for e in r.chronicle
                  if e.kind == "settle" and e.who.endswith(LOOP)
                  and abs(e.t / YEAR - year) < 0.6]
        reached = "perceive" in routes
        print(f"    year {year:>2d}: "
              f"{'it reaches him — she moves him' if reached else 'he resists it — the picture holds'}")
        if reached:
            last_good = year
    print(f"\n  POINT OF NO RETURN: after year {last_good}, no single day, "
          f"however astonishing,")
    print("  routes to perceive — his hardened prior outranks anything one day "
          "can say.")
    print("  The marriage's fate is settled years before anything visible "
          "happens,")
    print("  and the year it was settled is computable.")


if __name__ == "__main__":
    study()
