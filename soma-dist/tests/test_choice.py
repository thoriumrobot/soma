"""
Tests for the 0.20 choice layer (active inference / expected free energy;
Friston et al. 2015, 2016). Each of the theory's load-bearing claims is staked:
choice decomposes into pragmatic + curiosity-weighted epistemic value; a
high-uncertainty option offers more information; curiosity trades exploration
against exploitation with a per-character crossover; preference is a target so
a chooser declines overshoot; and a character's curiosity is derivable from the
same temperament dials that drive their feelings.
"""
import pytest

from soma.narrative import Story, anxious, stoic, tender, guarded
from soma.narrative.choice import (Option, decide, expected_free_energy,
                                   explore_exploit, temptation, curiosity_of)


# ---------------------------------------------------------------------------
# expected free energy decomposition
# ---------------------------------------------------------------------------

def test_efe_decomposes_into_pragmatic_and_epistemic():
    o = Option("x", reward=6, uncertainty=2.0)
    efe = expected_free_energy(o, preference=8, curiosity=1.0)
    assert set(efe) == {"pragmatic", "epistemic", "G"}
    assert efe["G"] == pytest.approx(efe["pragmatic"] + efe["epistemic"])


def test_higher_uncertainty_offers_more_epistemic_value():
    """A vague option collapses further when chosen -- more to learn."""
    familiar = Option("familiar", reward=6, uncertainty=0.6)
    novel = Option("novel", reward=6, uncertainty=3.5)
    ef = expected_free_energy(familiar, preference=8, curiosity=1.0)
    en = expected_free_energy(novel, preference=8, curiosity=1.0)
    assert en["epistemic"] > ef["epistemic"]


def test_pragmatic_value_peaks_at_preference():
    """Closeness to target, not maximization: reward AT preference beats reward
    above it."""
    at = expected_free_energy(Option("a", reward=8, uncertainty=0.5),
                              preference=8, curiosity=0.0)
    over = expected_free_energy(Option("b", reward=11, uncertainty=0.5),
                                preference=8, curiosity=0.0)
    assert at["pragmatic"] > over["pragmatic"]


# ---------------------------------------------------------------------------
# deciding
# ---------------------------------------------------------------------------

def test_decision_is_a_distribution():
    d = decide((8, 1.0), [Option("a", 6, 0.6), Option("b", 5, 2.5)])
    assert abs(sum(d.probs.values()) - 1.0) < 1e-9
    assert d.choice in d.probs


def test_zero_curiosity_takes_the_higher_reward():
    """With no curiosity it is pure reward-closeness: the option nearer the
    preference wins regardless of uncertainty."""
    d = decide((8, 0.0), [Option("near", 7.5, 0.5),
                          Option("far", 5.0, 3.5)])
    assert d.choice == "near"


def test_decisiveness_sharpens_the_choice():
    opts = [Option("a", 7.5, 0.5), Option("b", 6.5, 0.5)]
    soft = decide((8, 0.0), opts, decisiveness=0.5)
    sharp = decide((8, 0.0), opts, decisiveness=6.0)
    assert sharp.p("a") > soft.p("a")   # more decisive -> more on the best


def test_decision_is_reproducible():
    a = decide((8, 1.2), [Option("a", 6, 1.0), Option("b", 5, 2.0)])
    b = decide((8, 1.2), [Option("a", 6, 1.0), Option("b", 5, 2.0)])
    assert a.probs == b.probs


# ---------------------------------------------------------------------------
# explore / exploit
# ---------------------------------------------------------------------------

def test_curiosity_drives_exploration_crossover():
    """The signature: the same safe/uncertain pair, and P(risky) rises with
    curiosity, crossing from exploit to explore."""
    safe = Option("safe", reward=6, uncertainty=0.6)
    risky = Option("risky", reward=5, uncertainty=3.5)
    ee = explore_exploit(safe, risky, preference=8,
                         curiosities=(0, 0.5, 1, 2, 4))
    ps = [p for _, p in ee.curve]
    assert ps == sorted(ps)              # monotone rising
    assert ps[0] < 0.5 and ps[-1] > 0.5  # crosses over
    assert ee.crossover is not None


def test_low_curiosity_never_explores_a_worse_bet():
    safe = Option("safe", reward=7, uncertainty=0.5)
    risky = Option("risky", reward=4, uncertainty=3.5)
    ee = explore_exploit(safe, risky, preference=8, curiosities=(0, 0.1))
    assert ee.curve[0][1] < 0.5          # at zero curiosity, exploit


# ---------------------------------------------------------------------------
# temptation
# ---------------------------------------------------------------------------

def test_temptation_threshold_rises_with_reward():
    safe = Option("safe", reward=7, uncertainty=0.5)
    t = temptation((8, 0.3), safe, risky_uncertainty=0.5,
                   rewards=(5, 6, 7, 8, 9))
    ps = [p for _, p in t.curve]
    # more reward on the gamble (up to the preference) makes it more tempting
    assert t.curve[0][1] <= t.curve[3][1]


# ---------------------------------------------------------------------------
# curiosity from temperament
# ---------------------------------------------------------------------------

def test_curiosity_derives_from_temperament():
    """The open, trusting temperament is more curious than the guarded,
    convinced one -- read off the same dials that drive their feelings."""
    def cur(temp):
        s = Story("t", span="4s", step="1s", about="acute distress")
        return curiosity_of(s.character("C", temperament=temp))
    assert cur(tender) > cur(anxious)
    assert cur(anxious) > cur(guarded)
    assert cur(guarded) < 1.0 < cur(tender)


def test_temperament_determines_the_choice():
    """No choice authored: the guarded temperament holds the known road, the
    tender one leaves -- from disposition alone."""
    safe = Option("stay", reward=8, uncertainty=0.5)
    risky = Option("leave", reward=5.5, uncertainty=2.5)

    def choose(temp):
        s = Story("t", span="4s", step="1s", about="acute distress")
        c = s.character("C", temperament=temp)
        return decide(c, [safe, risky], preference=8, decisiveness=2.5,
                      sigma_pref=1.5).choice
    assert choose(guarded) == "stay"
    assert choose(tender) == "leave"


def test_character_preference_attribute_is_used():
    s = Story("t", span="4s", step="1s", about="acute distress")
    c = s.character("C", temperament=stoic)
    c._preference = 5
    # with preference 5, the reward-5 option is the target
    d = decide(c, [Option("five", 5, 0.5), Option("nine", 9, 0.5)],
               curiosity=0.0)
    assert d.choice == "five"
