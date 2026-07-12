"""
Tests for the 0.18 symptom-network layer (Cramer et al. 2016 + Post 1992).

Each of the network theory's load-bearing claims is staked as an assertion:
connectivity is vulnerability (the strongly connected network tips at lower
stress); the strongly connected network shows spontaneous non-recovery
(hysteresis); it settles at the poles more often (bimodality / the cusp); each
episode lowers the threshold for the next until episodes become autonomous
(kindling); and the most-connected symptom is the treatment target.
"""
import pytest

from soma.narrative.network import (symptom_network, depression_network,
                                    stress_response, tipping_stress,
                                    hysteresis_loop, equilibrium_modes,
                                    kindling, target_symptom,
                                    DEPRESSION_SYMPTOMS)


RESILIENT = 0.45
VULNERABLE = 1.4


# ---------------------------------------------------------------------------
# compilation and basic dynamics
# ---------------------------------------------------------------------------

def test_network_compiles_to_soma_and_runs():
    net = depression_network(connectivity=1.0)
    src = net.source()
    assert src.count("flow ") == len(DEPRESSION_SYMPTOMS)
    assert "sigmoid(" in src
    # a high stress activates the network
    sr = stress_response(net, levels=(0, 4))
    assert sr.curve[0][1] == 0            # no stress -> no symptoms
    assert sr.curve[-1][1] >= 5           # high stress -> depressed


def test_negative_threshold_source_is_valid():
    """Kindling drives thresholds negative; the source must stay parseable
    (a `- -x` term would break the lexer)."""
    net = depression_network(connectivity=1.0, threshold=-0.5)
    src = net.source()
    assert "- -" not in src
    assert "+ 0.5" in src
    sr = stress_response(net, levels=(0,))   # must run without a parse error
    assert sr.curve[0][1] >= 0


# ---------------------------------------------------------------------------
# I. connectivity is vulnerability
# ---------------------------------------------------------------------------

def test_connectivity_lowers_the_tipping_stress():
    resilient = tipping_stress(depression_network(connectivity=RESILIENT))
    vulnerable = tipping_stress(depression_network(connectivity=VULNERABLE))
    assert resilient is not None and vulnerable is not None
    assert vulnerable < resilient


def test_stress_response_is_monotone():
    sr = stress_response(depression_network(connectivity=1.0))
    counts = [n for _, n in sr.curve]
    assert counts == sorted(counts)      # more stress never means fewer symptoms
    assert counts[0] == 0 and counts[-1] >= 5


# ---------------------------------------------------------------------------
# II. spontaneous non-recovery (hysteresis)
# ---------------------------------------------------------------------------

def test_vulnerable_network_is_hysteretic_but_recovers():
    """The vulnerable network's depression OUTLIVES its cause -- it releases
    only well below its trigger -- but lowering the stress far enough does
    lift it. Hysteresis is the weaker claim; non-recovery is the stronger."""
    h = hysteresis_loop(depression_network(connectivity=VULNERABLE))
    assert h.triggers_at is not None
    assert h.width > 0
    assert h.releases_at is not None
    assert not h.spontaneous_nonrecovery


def test_severe_network_shows_true_spontaneous_non_recovery():
    """At severe connectivity the network holds itself down at ZERO stress:
    removing the stressor does not lift the episode. This -- not mere
    hysteresis -- is Cramer et al.'s spontaneous non-recovery."""
    h = hysteresis_loop(depression_network(connectivity=3.2))
    assert h.triggers_at is not None
    assert h.releases_at is None
    assert h.spontaneous_nonrecovery
    assert h.width == float("inf")


def test_resilient_network_recovers():
    h = hysteresis_loop(depression_network(connectivity=RESILIENT))
    # the resilient network releases at a stress not far below its trigger
    assert h.triggers_at is not None
    assert h.releases_at is not None
    assert h.width <= 2


def test_vulnerable_loop_is_wider_than_resilient():
    hr = hysteresis_loop(depression_network(connectivity=RESILIENT))
    hv = hysteresis_loop(depression_network(connectivity=VULNERABLE))
    wr = hr.width if hr.width != float("inf") else 99
    wv = hv.width if hv.width != float("inf") else 99
    assert wv >= wr


# ---------------------------------------------------------------------------
# III. bimodality / the cusp
# ---------------------------------------------------------------------------

def test_connectivity_raises_the_depressed_share():
    """Same stress band, more connectivity -> more runs end depressed."""
    lo = equilibrium_modes(depression_network(connectivity=RESILIENT),
                           samples=50, seed=2).depressed_share
    hi = equilibrium_modes(depression_network(connectivity=VULNERABLE),
                           samples=50, seed=2).depressed_share
    assert hi > lo


def test_equilibria_are_bimodal():
    em = equilibrium_modes(depression_network(connectivity=VULNERABLE),
                           samples=60, seed=1)
    assert em.bimodality > 0.5           # most equilibria sit at a pole


# ---------------------------------------------------------------------------
# IV. kindling
# ---------------------------------------------------------------------------

def test_kindling_lowers_the_trigger_over_episodes():
    k = kindling(depression_network(connectivity=1.0), episodes=6,
                 sensitization=0.4)
    triggers = [ts for _, ts, _ in k.episodes]
    # the required trigger is non-increasing and strictly falls overall
    assert triggers[0] > triggers[-1]
    assert all(a >= b for a, b in zip(triggers, triggers[1:]))


def test_kindling_reaches_autonomy():
    k = kindling(depression_network(connectivity=1.1), episodes=10,
                 sensitization=0.45)
    assert k.became_autonomous_at is not None
    # the autonomous episodes need zero stress
    autonomous = [ts for n, ts, _ in k.episodes
                  if k.became_autonomous_at and n >= k.became_autonomous_at]
    assert all(ts <= 0.001 for ts in autonomous)


def test_low_sensitization_does_not_kindle_to_autonomy():
    k = kindling(depression_network(connectivity=0.8), episodes=4,
                 sensitization=0.1)
    assert k.became_autonomous_at is None


# ---------------------------------------------------------------------------
# V. the treatment target
# ---------------------------------------------------------------------------

def test_target_is_the_most_connected_symptom():
    net = depression_network(connectivity=1.15)
    t = target_symptom(net, stress=3.0)
    deg = net.degree()
    best = t["best_target"]
    # the named target reduces the symptom count, and is the highest-degree
    # node (the hub), not merely any symptom
    assert t["best_result"] < t["baseline"]
    assert deg[best] == max(deg.values())


def test_disabling_a_leaf_barely_helps():
    """A weakly-connected symptom, disabled, leaves most of the network up --
    the contrast that makes the hub result meaningful."""
    net = depression_network(connectivity=1.15)
    t = target_symptom(net, stress=3.0)
    deg = net.degree()
    leaf = min(deg, key=deg.get)
    hub = t["best_target"]
    assert t["per_symptom"][leaf] >= t["per_symptom"][hub]


# ---------------------------------------------------------------------------
# custom networks
# ---------------------------------------------------------------------------

def test_custom_small_network():
    net = symptom_network("Mini", ["a", "b", "c"],
                          [("a", "b"), ("b", "c"), ("c", "a")],
                          connectivity=2.0, threshold=1.5)
    sr = stress_response(net, levels=(0, 3), depressed_at=2)
    assert sr.curve[0][1] == 0
    assert sr.curve[-1][1] >= 2
