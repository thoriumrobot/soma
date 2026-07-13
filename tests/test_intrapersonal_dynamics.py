"""
Tests for the 0.17 intrapersonal-dynamics layer: chained-comparison guards,
affine insolvency enforced at the act, the state portrait of a single psyche,
the hysteresis instrument, cyclic attractors, and the two flagship character
systems (Robinaugh's panic network; Rinaldi's relaxation-oscillator poet).

Each of the literatures' load-bearing claims is an assertion: the disorder is
an attractor (a region of starting states, not a level); the trigger is not
the release (hysteresis); the metabolic budget bounds a runaway loop
(burnout); reappraisal dissolves the attractor (bifurcation); safety behavior
abolishes the acute attack; and a poet's steady state can be a cycle with a
measurable amplitude and period.
"""
import pytest

from soma.narrative import Story, anxious, tender, stoic
from soma.narrative.insight import run_with
from soma.narrative.phase import (state_portrait, hysteresis, _tail_motion)


# ---------------------------------------------------------------------------
# builders (shared with the_vicious_cycle.py)
# ---------------------------------------------------------------------------

def panic_person(schema=0.6, escape=False, budget=None, span="60s"):
    guard = round(85 - 50 * schema)
    s = Story("panic", span=span, step="1s", about="acute distress")
    p = s.character("Noa", temperament=anxious)
    if budget is not None:
        p.has_budget(budget)
    p.senses("stressor", baseline=0.0)
    p.appraises("stressor", as_threat=True, when="stressor > 4",
                drives="arousal", to=70, fades_to=20, expects=0.0,
                precision=0.9, conviction=0.2)
    p.appraises("arousal", as_threat=True, when=f"arousal > {guard}",
                feeling="dread", drives="perceived_threat", to=90, fades_to=5,
                expects=20.0, precision=0.9, conviction=0.3)
    if escape:
        p.appraises("perceived_threat", when="perceived_threat > 80",
                    feeling="flees", drives="perceived_threat", to=5,
                    expects=5.0, precision=0.95, conviction=0.2)
    p.appraises("perceived_threat", as_threat=True, when="perceived_threat > 50",
                feeling="terror", drives="arousal", to=95, fades_to=20,
                expects=5.0, precision=0.9, conviction=0.3, spend_first=True)
    return s


def pulse(s, t0=5, n=3, v=8):
    c = s.characters[0]
    for i in range(n):
        s.at(f"{t0+i}s", c.hears("stressor", v))
    s.at(f"{t0+n}s", c.hears("stressor", 0))
    return s


def poet():
    s = Story("the_poet", span="80s", step="1s",
              about="the erosion of intimacy")
    p = s.character("Petrarch", temperament=tender)
    p.has_body_signal("ardour", baseline=60)
    p.has_body_signal("inspiration", baseline=25)
    p.appraises("ardour", when="ardour > 55", feeling="rapture",
                drives="inspiration", to=90, fades_to=25, expects=60.0,
                precision=0.6, conviction=0.2)
    p.appraises("inspiration", as_threat=True, when="inspiration > 70",
                feeling="despair", drives="ardour", to=15, fades_to=60,
                expects=25.0, precision=0.6, conviction=0.2)
    return s


# ---------------------------------------------------------------------------
# core language: chained comparisons and the affine act
# ---------------------------------------------------------------------------

def test_chained_comparison_is_a_band():
    """`3 < x < 7` must mean (3 < x) and (x < 7), not ((3 < x) < 7)."""
    s = Story("chain", span="6s", step="1s", about="acute distress")
    c = s.character("T", temperament=stoic)
    c.senses("x", baseline=0)
    c.appraises("x", when="3 < x < 7", feeling="inband", expects=0.0,
                precision=0.9, conviction=0.2)
    s.at("1s", c.hears("x", 5))
    s.at("2s", c.hears("x", 9))
    s.at("3s", c.hears("x", 2))
    r = run_with(s)
    hits = [e.t for e in r.chronicle if e.kind == "emit"]
    assert 1.0 in hits          # x=5: in band
    assert 2.0 not in hits      # x=9: above the band
    assert 3.0 not in hits      # x=2: below the band


def test_insolvent_act_does_not_happen():
    """The affine commitment enforced at the act: with a finite budget, the
    terror loop's drive on the body (spend_first) starves when the reserve
    runs dry, and the attack decays instead of sustaining."""
    r = run_with(pulse(panic_person(schema=0.85, budget=120)))
    ar = r.channel_hist.get("arousal", [])
    assert max(ar) >= 90                       # the attack ignites
    assert sum(ar[-5:]) / 5 < 35               # ...and burns out
    assert any(e.kind == "budget" for e in r.chronicle)


def test_unlimited_body_sustains_the_attack():
    """Without the budget, the same person's attack is self-sustaining."""
    r = run_with(pulse(panic_person(schema=0.85)))
    ar = r.channel_hist.get("arousal", [])
    assert sum(ar[-5:]) / 5 >= 90


# ---------------------------------------------------------------------------
# the disorder as an attractor
# ---------------------------------------------------------------------------

def test_state_portrait_finds_calm_and_panic_attractors():
    p = state_portrait(panic_person(schema=0.85), "Noa",
                       ("arousal", "perceived_threat"),
                       grid=5, lo=0, hi=100, beats=24,
                       high_label="panic", low_label="calm",
                       healthy_is="low")
    labels = sorted({at.label() for at in p.attractors})
    assert len(p.attractors) == 2
    assert 0.0 < p._healthy_share < 1.0
    # the panic attractor sits at high arousal AND high threat
    panic = max(p.attractors, key=lambda at: at.a)
    assert panic.a >= 85 and panic.b >= 80


def test_schema_scales_the_panic_basin():
    """Vulnerability as a region: a higher arousal schema means a larger
    panic basin, and a low enough schema dissolves the attractor entirely."""
    shares = {}
    for schema in (0.2, 0.5, 0.85):
        p = state_portrait(panic_person(schema=schema), "Noa",
                           ("arousal", "perceived_threat"),
                           grid=5, lo=0, hi=100, beats=24, healthy_is="low")
        shares[schema] = 1 - p._healthy_share
    assert shares[0.2] == 0.0                  # no panic attractor at all
    assert shares[0.2] <= shares[0.5] <= shares[0.85]
    assert shares[0.85] > 0.5


def test_safety_behavior_abolishes_the_acute_attack():
    p = state_portrait(panic_person(schema=0.85, escape=True), "Noa",
                       ("arousal", "perceived_threat"),
                       grid=5, lo=0, hi=100, beats=24, healthy_is="low")
    assert p._healthy_share == 1.0


# ---------------------------------------------------------------------------
# hysteresis
# ---------------------------------------------------------------------------

def test_panic_hysteresis_trigger_is_not_the_release():
    h = hysteresis(panic_person(schema=0.85), "Noa", "stressor", "arousal",
                   levels=[0, 2, 4, 5, 6, 7, 8, 9], dwell=5)
    assert h.bistable
    assert h.triggers_at is not None
    assert h.releases_at is None               # the trap: no release in range
    assert h.width == float("inf")
    assert "self-sustaining" in h.render()


def test_healthy_person_shows_no_hysteresis():
    h = hysteresis(panic_person(schema=0.2), "Noa", "stressor", "arousal",
                   levels=[0, 2, 4, 5, 6, 7, 8, 9], dwell=5)
    assert not h.bistable
    assert "reversible" in h.render()


# ---------------------------------------------------------------------------
# cyclic attractors: the poet
# ---------------------------------------------------------------------------

def test_tail_motion_reads_cycles():
    settled = [5.0] * 12
    wave = [50 + (20 if i % 4 < 2 else -20) for i in range(16)]
    c1, a1, _ = _tail_motion(settled)
    c2, a2, p2 = _tail_motion(wave, tail=16)
    assert a1 == 0.0
    assert a2 >= 30 and abs(c2 - 50) < 6
    assert 3 <= p2 <= 5


def test_poet_rest_state_is_a_cycle():
    """Rinaldi's claim, staked: from EVERY starting state the poet flows into
    the same oscillation -- one cyclic attractor holding the whole plane,
    with a stable amplitude and period."""
    p = state_portrait(poet(), "Petrarch", ("ardour", "inspiration"),
                       grid=4, lo=10, hi=90, beats=48, osc_tol=12,
                       healthy_is=None)
    assert len(p.attractors) == 1
    at = p.attractors[0]
    assert at.cyclic
    assert at.share == 1.0
    assert at.amplitude > 25
    assert 5 <= at.period <= 12


def test_poet_cycle_is_reproducible():
    a = state_portrait(poet(), "Petrarch", ("ardour", "inspiration"),
                       grid=3, lo=10, hi=90, beats=48, osc_tol=12,
                       healthy_is=None)
    b = state_portrait(poet(), "Petrarch", ("ardour", "inspiration"),
                       grid=3, lo=10, hi=90, beats=48, osc_tol=12,
                       healthy_is=None)
    assert (a.attractors[0].period, a.attractors[0].amplitude) == \
           (b.attractors[0].period, b.attractors[0].amplitude)


def test_panic_attractors_are_fixed_not_cyclic():
    """Contrast case: the panic system's attractors are points, not cycles --
    the classifier must tell the two dynamical objects apart."""
    p = state_portrait(panic_person(schema=0.85), "Noa",
                       ("arousal", "perceived_threat"),
                       grid=4, lo=0, hi=100, beats=24, healthy_is="low")
    assert all(at.kind == "fixed" for at in p.attractors)
