"""
Tests for the 0.16 landscape layers: phase portraits (attractors, basins,
Gottman's fitted influence model, resilience, therapy-as-bifurcation) and
ensemble futures (distribution over endings, the pivotal dial, dose-response).

Each of the literature's load-bearing claims is staked as an assertion:
Gottman's landscape typology (a regulated couple's plane keeps a warm
attractor; an unregulated couple's plane has none), the recoverability of the
influence parameters from the interaction itself, Holling's resilience-as-basin
reading, the existence bifurcation, and the ensemble's ability to (a) grade
how settled a fate is and (b) name the dial that decides it.
"""
import pytest

from soma.narrative import Story, tender, trusting, arc
from soma.narrative.gottman import marry
from soma.narrative.phase import (phase_portrait, fit_influence, resilience,
                                  second_stable_state)
from soma.narrative.futures import (futures, pivotal, dose_response,
                                    by_outcome, by_break)
from soma.narrative.insight import run_with

YEAR = 31557600.0
LOOP = "appraising_her_face"


# ---------------------------------------------------------------------------
# builders (shared with the_shape_of_a_marriage.py)
# ---------------------------------------------------------------------------

def gottman_couple(kind):
    s = Story(f"{kind}_couple", span="20s", step="1s", about="marital friction")
    a = s.character("Ada", temperament=trusting)
    b = s.character("Ben", temperament=trusting)
    marry(s, a, b, kind)
    return s


def brittle_couple(gain=0.9):
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
    s = Story("the_marriage", span="30y", step="1y", cadence=True,
              about="the slow erosion of intimacy")
    soren = s.character("Soren", temperament=tender, clock="life")
    soren.senses("her_face", baseline=5)
    soren.appraises("her_face", feeling="delight_at_error", when="her_face > 1",
                    precision=0.75, conviction=0.2, updates=True,
                    stops_seeing=True)
    soren.learns(learn)
    s.over(arc.wobble(around=5, span="24y", every="1y", unit="y", amplitude=3),
           lambda v: soren.hears("her_face", v))
    if extraordinary_day is not None:
        y, v = extraordinary_day
        s.at(f"{y}y", soren.hears("her_face", v))
    return s


# ---------------------------------------------------------------------------
# I. the empirical landscape
# ---------------------------------------------------------------------------

def test_regulated_couple_has_a_warm_attractor():
    p = phase_portrait(gottman_couple("validating"), grid=4, beats=16)
    assert p.positive_attractor is not None
    assert p.positive_share > 0.5


def test_unregulated_couple_landscape_has_no_good_ending():
    """Gottman's cascade as a property of the plane: for a hostile couple,
    EVERY opening decays to the cold state."""
    p = phase_portrait(gottman_couple("hostile"), grid=4, beats=16)
    assert p.positive_attractor is None
    assert p.positive_share == 0.0
    assert "NO WARM ATTRACTOR" in p.render()


def test_bistable_couple_has_both_basins_and_the_start_decides():
    p = phase_portrait(brittle_couple(), grid=5, beats=20)
    labels = {at.label() for at in p.attractors}
    assert "warm" in labels and "cold" in labels
    # the corners land in opposite basins: the opening decides the marriage
    assert p.attractor_of(9.0, 9.0).positive
    assert not p.attractor_of(1.0, 1.0).positive


def test_portrait_is_deterministic():
    a = phase_portrait(brittle_couple(), grid=3, beats=16)
    b = phase_portrait(brittle_couple(), grid=3, beats=16)
    assert [(at.a, at.b, at.share) for at in a.attractors] == \
           [(at.a, at.b, at.share) for at in b.attractors]


# ---------------------------------------------------------------------------
# II. Gottman's fit, closed into a loop
# ---------------------------------------------------------------------------

def test_fit_recovers_the_influence_structure_and_validates():
    p = phase_portrait(brittle_couple(), grid=5, beats=20)
    m = fit_influence(p)
    # this couple's influence is plateau-shaped; model selection must find it
    assert m.a.form == "ojive" and m.b.form == "ojive"
    assert m.a.r2 > 0.9 and m.b.r2 > 0.9
    assert m.a.warm_plateau > 1.0 and m.a.cold_plateau < -1.0
    v = m.validate(p)
    assert v["ok"], v


def test_fitted_map_reproduces_warm_and_cold_states():
    p = phase_portrait(brittle_couple(), grid=5, beats=20)
    fitted = fit_influence(p).attractors()
    assert any(a >= 5.5 and b >= 5.5 for a, b in fitted)   # warm exists
    assert any(a < 5.5 and b < 5.5 for a, b in fitted)     # cold exists


# ---------------------------------------------------------------------------
# III. resilience
# ---------------------------------------------------------------------------

def test_resilience_measures_the_basin():
    p = phase_portrait(brittle_couple(), grid=5, beats=20)
    r = resilience(brittle_couple(), portrait=p)
    assert r.attractor is not None
    assert 0.0 < r.basin_share < 1.0
    # small kicks recover, large kicks go over the rim
    assert r.kicks[0][1] is True
    assert r.kicks[-1][1] is False
    assert 0.0 < r.basin_radius < 4.0


def test_no_resilience_without_a_warm_attractor():
    r = resilience(gottman_couple("hostile"))
    assert r.attractor is None and r.basin_share == 0.0
    assert "none" in r.render()


# ---------------------------------------------------------------------------
# IV. therapy as bifurcation
# ---------------------------------------------------------------------------

def test_second_stable_state_finds_the_existence_threshold():
    """Below a mutual gain, the warm attractor does not exist; the sweep must
    find where the landscape acquires its good ending."""
    ls = second_stable_state(brittle_couple(),
                             ["Ada.manner.gain", "Ben.manner.gain"],
                             [0.5, 0.7, 0.9, 1.0],
                             target_share=0.2, grid=4, beats=20)
    shares = {v: s for v, s, _ in ls.curve}
    assert shares[0.5] == 0.0 and shares[0.7] == 0.0
    assert shares[0.9] >= 0.2
    assert ls.threshold == 0.9
    assert "bifurcation" in ls.render()


# ---------------------------------------------------------------------------
# V. ensemble futures
# ---------------------------------------------------------------------------

CLASSIFY = by_outcome("perceive_frac", above=0.6,
                      labels=("stays open", "curdles"))
DIALS = {f"{LOOP}.learn": (0.0, 0.12), f"{LOOP}.precision": (0.55, 0.95)}


def test_futures_distribution_and_entropy():
    rep = futures(soren_marriage(), DIALS, CLASSIFY, samples=24, seed=7)
    assert abs(sum(rep.endings.values()) - 1.0) < 1e-9
    assert set(rep.endings) == {"stays open", "curdles"}
    assert 0.0 < rep.entropy <= 1.0        # a contested fate, not a destiny
    assert rep.modal == "curdles"


def test_futures_reproducible_given_seed():
    a = futures(soren_marriage(), DIALS, CLASSIFY, samples=12, seed=3)
    b = futures(soren_marriage(), DIALS, CLASSIFY, samples=12, seed=3)
    assert a.endings == b.endings


def test_destiny_has_low_entropy():
    """With the learning pinned at zero, every nearby world stays open: the
    ensemble must read that as destiny, not a coin."""
    rep = futures(soren_marriage(),
                  {f"{LOOP}.precision": (0.55, 0.95)}, CLASSIFY,
                  samples=10, seed=1,
                  base_overrides={f"{LOOP}.learn": 0.0})
    assert rep.endings == {"stays open": 1.0}
    assert rep.entropy == 0.0


def test_pivotal_dial_is_the_learning_rate():
    """The sensitivity study's conclusion, recovered as an effect size: what
    decides this marriage is `learn`, not `precision`."""
    rep = futures(soren_marriage(), DIALS, CLASSIFY, samples=30, seed=7)
    ranks = pivotal(rep)
    assert ranks[0][0] == f"{LOOP}.learn"
    assert abs(ranks[0][1]) > 1.0          # a large effect
    assert abs(ranks[-1][1]) < 0.5         # precision barely moves the odds


# ---------------------------------------------------------------------------
# VI. dose-response
# ---------------------------------------------------------------------------

def _make_reaches(year):
    def reaches_him(result):
        for e in result.chronicle:
            if (e.kind == "settle" and e.who.endswith(LOOP)
                    and abs(e.t / YEAR - year) < 0.6
                    and e.detail.get("route") == "perceive"
                    and abs(e.detail.get("error", 0)) > 0.5):
                return "reaches him"
        return "does not"
    return reaches_him


def test_intensity_is_not_a_dose():
    """The honest null: precision arbitration is magnitude-blind. By year 20
    no intensity of extraordinary day reaches him."""
    dr = dose_response(lambda v: soren_marriage(extraordinary_day=(20, v)),
                       doses=[6, 12, 20],
                       classify_at=lambda v: _make_reaches(20),
                       target="reaches him",
                       dials={f"{LOOP}.learn": (0.05, 0.11)},
                       samples=6, seed=3, p_min=0.7)
    assert all(p == 0.0 for _, p in dr.curve)
    assert dr.minimal_dose is None


def test_timing_is_the_dose_and_the_curve_is_monotone():
    """The last good year, as a curve: P(reaches him) falls as the day lands
    later, from certainty in the early marriage to zero past the hardening."""
    dr = dose_response(lambda y: soren_marriage(extraordinary_day=(y, 9)),
                       doses=[14, 8, 4],           # descending year
                       classify_at=_make_reaches,
                       target="reaches him",
                       dials={f"{LOOP}.learn": (0.05, 0.11)},
                       samples=8, seed=3, p_min=0.7)
    curve = dict(dr.curve)
    assert curve[4] >= 0.9                  # early: near-certain
    assert curve[14] <= 0.1                 # late: near-impossible
    assert curve[4] >= curve[8] >= curve[14]
    assert dr.minimal_dose == 4             # the latest year clearing p_min


def test_by_break_classifier():
    """by_break names endings from revelations; the marriage has no lie loop,
    so every world classifies as kept."""
    rep = futures(soren_marriage(), {f"{LOOP}.learn": (0.0, 0.1)},
                  by_break(), samples=6, seed=0)
    assert rep.endings == {"kept": 1.0}
