"""
the_shape_of_a_marriage.py -- the landscape a relationship IS, and the space
of marriages it could be.

`the_marriage_that_could_have_held` asked four questions about ONE trajectory.
This study asks the deeper ones the 0.16 layers make askable -- Gottman &
Murray's phase-portrait questions (The Mathematics of Marriage, 2002),
Holling's and Scheffer's resilience questions, and the ensemble-forecasting
question -- each answered by the machine, none asserted:

  I.    THE LANDSCAPE      phase portraits of two Gottman couples: the
                           validating couple's plane has one warm attractor;
                           the hostile couple's plane contains NO good ending
                           at all -- divorce as a property of the landscape,
                           not of any one fight.
  II.   THE BRITTLE COUPLE a couple whose plane is BISTABLE: a warm basin, a
                           cold basin, two pursue-withdraw states, and a
                           separatrix. Which marriage they have is decided by
                           where the evening starts.
  III.  GOTTMAN'S FIT      the influence parameters (uninfluenced state,
                           inertia, ojive influence with FITTED thresholds)
                           regressed from the simulation's own trajectories --
                           the model's famous move performed on the model --
                           and validated: the fitted map must reproduce the
                           empirical attractors, bidirectionally.
  IV.   RESILIENCE         the warm basin's share of the plane, and the kick
                           probe: the largest perturbation the good state
                           recovers from (the basin's radius, measured).
  V.    THE SECOND STABLE  therapy as bifurcation: sweep the couple's mutual
        STATE              gain and find where the warm attractor comes into
                           EXISTENCE -- below it, no opening leads anywhere
                           good; at it, the landscape acquires a good ending.
  VI.   THE SPACE OF       ensemble futures for Soren's slow curdling: across
        MARRIAGES          nearby worlds (learn and precision jittered), the
                           DISTRIBUTION over endings, its entropy (destiny or
                           a coin), and the PIVOTAL DIAL -- which parameter
                           decides the fate, as an effect size.
  VII.  THE LAST GOOD      the original Study IV, deepened from a year to a
        YEAR, AS A CURVE   curve: P(an extraordinary day reaches him | the
                           year it lands), with the honest side-finding that
                           the day's INTENSITY does not matter -- precision
                           arbitration is magnitude-blind; only timing is.

Run:  python3 examples/narrative/the_shape_of_a_marriage.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from soma.narrative import Story, tender, trusting, arc
from soma.narrative.gottman import marry
from soma.narrative.phase import (phase_portrait, fit_influence, resilience,
                                  second_stable_state)
from soma.narrative.futures import futures, pivotal, dose_response, by_outcome

YEAR = 31557600.0
LOOP = "appraising_her_face"


# ---------------------------------------------------------------------------
# builders
# ---------------------------------------------------------------------------

def gottman_couple(kind):
    s = Story(f"{kind}_couple", span="20s", step="1s",
              about="marital friction")
    a = s.character("Ada", temperament=trusting)
    b = s.character("Ben", temperament=trusting)
    marry(s, a, b, kind)
    return s


def brittle_couple(gain=0.9):
    """Warmth met undimmed sustains itself; coldness met coldness sustains
    itself; between them, a separatrix. The couple whose evening decides."""
    s = Story("brittle", span="24s", step="1s", about="marital friction")
    a = s.character("Ada", temperament=trusting)
    b = s.character("Ben", temperament=trusting)
    for ch in (a, b):
        ch._add_sense("manner", "proprio", 5.0, "Expression")
    a.reads(b, "manner", into="their_manner", gain=gain, lag="1s")
    b.reads(a, "manner", into="their_manner", gain=gain, lag="1s")
    for ch in (a, b):
        ch.appraises("their_manner", when="their_manner >= 5.5",
                     feeling="ease", shows_on="manner", shows_value=8.0,
                     expects=5.0)
        ch.appraises("their_manner", when="their_manner <= 4.0",
                     as_threat=True, feeling="friction", shows_on="manner",
                     shows_value=2.0, drives="heart", to=100, expects=5.0)
    return s


def soren_marriage(extraordinary_day=None, learn=0.08):
    """The slow curdling from the_marriage_that_could_have_held."""
    s = Story("the_marriage", span="30y", step="1y", cadence=True,
              about="the slow erosion of intimacy")
    soren = s.character("Soren", temperament=tender, clock="life")
    soren.senses("her_face", baseline=5)
    soren.appraises("her_face", feeling="delight_at_error",
                    when="her_face > 1", precision=0.75, conviction=0.2,
                    updates=True, stops_seeing=True)
    soren.learns(learn)
    s.over(arc.wobble(around=5, span="24y", every="1y", unit="y", amplitude=3),
           lambda v: soren.hears("her_face", v))
    if extraordinary_day is not None:
        y, v = extraordinary_day
        s.at(f"{y}y", soren.hears("her_face", v))
    return s


# ---------------------------------------------------------------------------
# the studies
# ---------------------------------------------------------------------------

def study_landscapes():
    print("=" * 74)
    print("I. THE LANDSCAPE — divorce as a property of the plane")
    print("=" * 74)
    for kind in ("validating", "hostile"):
        p = phase_portrait(gottman_couple(kind), grid=4, beats=16)
        print(f"\n[{kind}]")
        print(p.render())
    print()


def study_bistable():
    print("=" * 74)
    print("II. THE BRITTLE COUPLE — a bistable plane, and the evening decides")
    print("=" * 74)
    p = phase_portrait(brittle_couple(), grid=5, beats=20)
    print(p.render())
    print()
    return p


def study_fit(portrait):
    print("=" * 74)
    print("III. GOTTMAN'S FIT — parameters regressed from the run, validated")
    print("=" * 74)
    m = fit_influence(portrait)
    print(m.render())
    v = m.validate(portrait)
    print(f"  fitted map's own attractors: {v['fitted_attractors']}")
    mark = "CONFIRMED" if v["ok"] else "FALSIFIED"
    print(f"  bidirectional validation against the empirical portrait: {mark}")
    print()


def study_resilience(portrait):
    print("=" * 74)
    print("IV. RESILIENCE — the basin as a region, and its measured radius")
    print("=" * 74)
    r = resilience(brittle_couple(), portrait=portrait)
    print(r.render())
    print()


def study_bifurcation():
    print("=" * 74)
    print("V. THE SECOND STABLE STATE — the gain at which a good ending EXISTS")
    print("=" * 74)
    ls = second_stable_state(
        brittle_couple(),
        ["Ada.manner.gain", "Ben.manner.gain"],
        [0.5, 0.7, 0.9, 1.0],
        target_share=0.2, grid=4, beats=20)
    print(ls.render())
    print("\n  Below the threshold the couple reads each other too faintly for")
    print("  warmth to sustain itself: EVERY opening decays to the cold state.")
    print("  At the threshold the warm attractor comes into existence. That is")
    print("  what an intervention is, formally: a change to the landscape.")
    print()


def study_futures():
    print("=" * 74)
    print("VI. THE SPACE OF MARRIAGES — the distribution over endings")
    print("=" * 74)
    classify = by_outcome("perceive_frac", above=0.6,
                          labels=("stays open", "curdles"))
    rep = futures(soren_marriage(),
                  {f"{LOOP}.learn": (0.0, 0.12),
                   f"{LOOP}.precision": (0.55, 0.95)},
                  classify, samples=40, seed=7)
    print(rep.render())
    piv = pivotal(rep)
    print(f"  pivotal dial: {piv[0][0]} (effect size d={piv[0][1]:+.2f}) — "
          f"vs {piv[1][0]} (d={piv[1][1]:+.2f})")
    print("  The fate of this marriage is a coin, and the coin is the learning")
    print("  rate. Her face, and how much he trusts it, barely move the odds:")
    print("  what decides is how fast being right makes him harder to surprise.")
    print()


def study_last_good_year():
    print("=" * 74)
    print("VII. THE LAST GOOD YEAR, AS A CURVE — timing is the only dose")
    print("=" * 74)

    def make_reaches(year):
        def reaches_him(result):
            for e in result.chronicle:
                if (e.kind == "settle" and e.who.endswith(LOOP)
                        and abs(e.t / YEAR - year) < 0.6
                        and e.detail.get("route") == "perceive"
                        and abs(e.detail.get("error", 0)) > 0.5):
                    return "reaches him"
            return "does not"
        return reaches_him

    # first, the honest null result: intensity is NOT a dose. By year 20 the
    # prior outranks the senses, and arbitration does not care how loud the
    # world is.
    flat = dose_response(
        lambda v: soren_marriage(extraordinary_day=(20, v)),
        doses=[6, 12, 20], classify_at=lambda v: make_reaches(20),
        target="reaches him", dials={f"{LOOP}.learn": (0.05, 0.11)},
        samples=8, seed=3, p_min=0.7,
        intervention="the day's INTENSITY (at year 20)")
    print(flat.render())
    print("  — precision arbitration is magnitude-blind: past the hardening,")
    print("    no intensity of day can reach him. The dose is WHEN, not how")
    print("    bright:\n")

    dr = dose_response(
        lambda y: soren_marriage(extraordinary_day=(y, 9)),
        doses=[16, 12, 10, 8, 6, 4],           # descending: the LATEST safe year
        classify_at=make_reaches,
        target="reaches him", dials={f"{LOOP}.learn": (0.05, 0.11)},
        samples=10, seed=3, p_min=0.7,
        intervention="the YEAR the day lands")
    print(dr.render())
    curve = dict(dr.curve)
    print(f"\n  The original study found one 'last good year'. Across nearby")
    print(f"  worlds it is a curve — from certainty at year 4 "
          f"(P={curve.get(4, 0):.0%}) through the")
    print(f"  contested middle years to no world at all by year 12 "
          f"(P={curve.get(12, 0):.0%}). The")
    print(f"  latest year that still reaches him in most marriages: "
          f"year {dr.minimal_dose}.")
    print()


if __name__ == "__main__":
    study_landscapes()
    p = study_bistable()
    study_fit(p)
    study_resilience(p)
    study_bifurcation()
    study_futures()
    study_last_good_year()
