"""
Tests for the 0.21 mentalizing layer (recursive theory of mind; Devaine,
Hollard & Daunizeau 2014; Camerer's cognitive hierarchy). The literature's
load-bearing claims are staked as generated results: the competitive ladder
(deeper exploits shallower), cooperation's saturation, the catastrophic cost
of strict over-mentalizing, chance against noise, the coin hypothesis, and the
inverse problem — depth read from moves, legible only when exercised.
"""
import random

import pytest

from soma.narrative.mentalizing import (Mind, RandomMind, play, tournament,
                                        depth_advantage, detect_depth,
                                        hide_and_seek, coordination)


# ---------------------------------------------------------------------------
# the games and the mind itself
# ---------------------------------------------------------------------------

def test_hide_and_seek_is_zero_sum():
    for a in (0, 1):
        for o in (0, 1):
            assert hide_and_seek(0, a, o) + hide_and_seek(1, o, a) == 1.0


def test_coordination_is_common_interest():
    for a in (0, 1):
        for o in (0, 1):
            assert coordination(0, a, o) == coordination(1, o, a)


def test_policy_is_a_probability():
    for k in (0, 1, 2, 3):
        m = Mind(k, seat=0)
        assert 0.0 <= m.policy() <= 1.0


def test_match_scores_are_zero_sum_in_hide_and_seek():
    m = play(1, 1, rounds=40, reps=5, seed=1)
    assert m.score_a + m.score_b == pytest.approx(1.0, abs=1e-9)


def test_play_is_reproducible():
    a = play(2, 1, rounds=40, reps=5, seed=7)
    b = play(2, 1, rounds=40, reps=5, seed=7)
    assert a.score_a == b.score_a and a.history == b.history


# ---------------------------------------------------------------------------
# I. the ladder: competition rewards depth
# ---------------------------------------------------------------------------

def test_competitive_ladder_holds():
    t = tournament((0, 1, 2), rounds=60, reps=25)
    assert t.ladder_holds()


def test_equal_depth_is_a_fair_fight():
    t = tournament((0, 1, 2), rounds=60, reps=25)
    for k in (0, 1, 2):
        assert abs(t.matrix[(k, k)] - 0.5) < 0.05


def test_one_step_depth_advantage():
    for k, score in depth_advantage(2, rounds=60, reps=25):
        assert score > 0.52          # each rung pays


# ---------------------------------------------------------------------------
# II. cooperation saturates at one level
# ---------------------------------------------------------------------------

def test_first_level_of_tom_helps_coordination():
    naive = play(0, 0, game="coordination", rounds=60, reps=25, beta=3.0)
    one = play(1, 0, game="coordination", rounds=60, reps=25, beta=3.0)
    joint_naive = (naive.score_a + naive.score_b) / 2
    joint_one = (one.score_a + one.score_b) / 2
    assert joint_one > joint_naive + 0.03


def test_depth_saturates_in_coordination():
    one = play(1, 1, game="coordination", rounds=60, reps=25, beta=3.0)
    three = play(3, 3, game="coordination", rounds=60, reps=25, beta=3.0)
    j1 = (one.score_a + one.score_b) / 2
    j3 = (three.score_a + three.score_b) / 2
    assert abs(j3 - j1) < 0.04       # no further gain from depth


# ---------------------------------------------------------------------------
# III. the cost of over-mentalizing
# ---------------------------------------------------------------------------

def test_strict_over_mentalizing_is_catastrophic():
    """A strict 2-ToM that insists its naive opponent is a 1-ToM schemer is
    itself the predictable one; the level-inferring mind keeps its edge."""
    strict = play(2, 0, infer_level=False, rounds=60, reps=25)
    infer = play(2, 0, infer_level=True, rounds=60, reps=25)
    assert strict.score_a < 0.35
    assert infer.score_a > 0.52
    assert infer.score_a - strict.score_a > 0.2


# ---------------------------------------------------------------------------
# IV. the coin: noise, bias, and knowing when not to attribute a mind
# ---------------------------------------------------------------------------

def test_no_depth_beats_pure_noise():
    for k in (0, 1, 2):
        m = play(k, 0, random_b=0.5, rounds=60, reps=25)
        assert abs(m.score_a - 0.5) < 0.05


def test_coin_hypothesis_lets_mentalizers_exploit_bias():
    """Against a mindless bias, the coin hypothesis keeps the mentalizer near
    the naive tracker's profit instead of attributing strategy to habit."""
    for k in (1, 2):
        m = play(k, 0, random_b=0.8, rounds=60, reps=25)
        assert m.score_a > 0.55


def test_mentalizer_comes_to_believe_coin_when_facing_one():
    rng = random.Random(3)
    M = Mind(1, seat=0)
    B = RandomMind(0.8, seat=1)
    for _ in range(80):
        a, b = M.act(rng), B.act(rng)
        M.observe(a, b)
    assert M.believed_opponent_level() == "coin"


# ---------------------------------------------------------------------------
# V. reading depth from moves — and its identifiability law
# ---------------------------------------------------------------------------

def test_detect_depth_recovers_shallow_minds():
    for true_k in (0, 1):
        m = play(0, true_k, rounds=120, reps=1, seed=4)
        r = detect_depth(m.history, seat=1, candidates=(0, 1, 2))
        assert r.inferred == true_k


def test_depth_is_only_legible_when_exercised():
    """A 2-ToM facing a naive opponent behaves like a 1-ToM (its second level
    is never needed) and is read as one; against a 1-ToM its depth is
    exercised and becomes visible. The 0.19 law, for minds."""
    easy = play(0, 2, rounds=150, reps=1, seed=4)
    hard = play(1, 2, rounds=150, reps=1, seed=4)
    r_easy = detect_depth(easy.history, seat=1, candidates=(0, 1, 2))
    r_hard = detect_depth(hard.history, seat=1, candidates=(0, 1, 2))
    assert r_easy.inferred == 1
    assert r_hard.inferred == 2


# ---------------------------------------------------------------------------
# VI. the tell: decisiveness is legibility; the guarded are read
# ---------------------------------------------------------------------------

def test_legibility_rises_with_decisiveness():
    """The shallower mind's own beta is its exploitability: monotone, from a
    near-escape at low beta to a rout at high."""
    from soma.narrative.mentalizing import legibility
    r = legibility(shallow_k=1, deep_k=2, betas=(2, 5, 12), reps=25)
    assert r.monotone()
    assert r.curve[0][1] < 0.56          # hesitation is armor
    assert r.curve[-1][1] > 0.65         # conviction is a tell


def test_social_params_derive_from_temperament():
    from soma.narrative.mentalizing import social_params_of
    from soma.narrative import guarded, tender
    a_g, b_g = social_params_of(guarded)
    a_t, b_t = social_params_of(tender)
    assert b_g > b_t                     # conviction -> decisiveness
    assert a_t > a_g                     # precision -> volatility


def test_the_guarded_are_more_legible_than_the_tender():
    """The cross-layer, unauthored result: conviction protects the interior
    and betrays the surface."""
    from soma.narrative.mentalizing import face_off
    from soma.narrative import guarded, tender, stoic
    vs_guarded = face_off(stoic, guarded, k_a=2, k_b=1, reps=25)
    vs_tender = face_off(stoic, tender, k_a=2, k_b=1, reps=25)
    assert vs_guarded.score_a > vs_tender.score_a + 0.04


def test_per_seat_parameters_override_shared():
    a = play(2, 1, rounds=40, reps=10, seed=3, beta_b=2.0)
    b = play(2, 1, rounds=40, reps=10, seed=3, beta_b=12.0)
    assert a.score_a < b.score_a         # the decisive hider loses more
