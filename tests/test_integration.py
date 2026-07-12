"""
Integration tests: the "whole character" claim, staked across layers.

SOMA's arc holds that a character is not a bag of independent modules: the same
two temperament dials -- PRECISION (trust in the senses) and CONVICTION (grip
on beliefs) -- drive their feelings (0.15's arbitration), their choices
(0.20's curiosity), and their social fate (0.22's decisiveness/legibility).
These tests stake the coherence itself: the derivations must agree in
direction, one temperament must carry consistent consequences across every
layer, and the layers must compose without adapters.
"""
import pytest

from soma.narrative import Story, guarded, tender, stoic, anxious
from soma.narrative.choice import Option, decide, curiosity_of
from soma.narrative.mentalizing import (face_off, mind_of, social_params_of,
                                        Mind)


# ---------------------------------------------------------------------------
# one temperament, coherent consequences everywhere
# ---------------------------------------------------------------------------

def test_openness_orders_both_curiosity_and_illegibility():
    """The open temperament (tender) is both the most curious chooser (0.20)
    and the least legible opponent (0.22); the guarded one is the least
    curious and among the most legible. One disposition, aligned fates."""
    def cur(temp):
        s = Story("t", span="4s", step="1s", about="acute distress")
        return curiosity_of(s.character("C", temperament=temp))
    _, beta_tender = social_params_of(tender)
    _, beta_guarded = social_params_of(guarded)
    assert cur(tender) > cur(guarded)          # more curious
    assert beta_tender < beta_guarded          # and harder to read


def test_the_same_dials_drive_choice_and_social_play():
    """A Character built once serves both layers with no adapters: decide()
    reads its temperament for curiosity; mind_of() reads the same temperament
    for social parameters."""
    s = Story("t", span="4s", step="1s", about="acute distress")
    c = s.character("Vera", temperament=anxious)
    d = decide(c, [Option("stay", 8, 0.5), Option("go", 6, 2.5)],
               preference=8)
    m = mind_of(c, k=1)
    assert d.who == "Vera"
    assert isinstance(m, Mind) and m.k == 1
    a, b = social_params_of(anxious)
    assert (m.alpha, m.beta) == (a, b)


def test_temperament_consequences_compose_into_a_social_fate():
    """End to end: two characters authored only by temperament meet, and who
    exploits whom follows from disposition and depth together."""
    s = Story("t", span="4s", step="1s", about="acute distress")
    reader = s.character("Iris", temperament=stoic)
    open_soul = s.character("Wren", temperament=tender)
    closed = s.character("Gil", temperament=guarded)
    m_open = face_off(reader, open_soul, k_a=2, k_b=1, reps=25)
    m_closed = face_off(reader, closed, k_a=2, k_b=1, reps=25)
    # the deeper reader profits from both, but the guarded one bleeds more
    assert m_closed.score_a > 0.55
    assert m_closed.score_a > m_open.score_a


def test_bare_temperaments_are_accepted_everywhere():
    """Usability: the bridges take a bare Temperament as well as a Character,
    so quick studies need no Story at all."""
    m = mind_of(guarded, k=1)
    assert isinstance(m, Mind)
    match = face_off(stoic, tender, k_a=1, k_b=1, rounds=30, reps=10)
    assert 0.0 <= match.score_a <= 1.0


def test_probe_and_face_off_share_a_character():
    """The 0.15 predictive layer and the 0.22 social layer run off the same
    Story character in the same session."""
    s = Story("t", span="4s", step="1s", about="acute distress")
    c = s.character("Ada", temperament=anxious)
    c.senses("noise", baseline=20)
    c.appraises("noise", as_threat=50, feeling="dread")
    rep = s.probe("Ada", {"noise": 70}, beats=3)
    assert rep is not None
    m = face_off(c, guarded, k_a=1, k_b=1, rounds=30, reps=10)
    assert 0.0 <= m.score_a <= 1.0
