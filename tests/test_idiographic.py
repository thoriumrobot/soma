"""
Tests for the 0.19 idiographic-inference layer (Bringmann 2021; Epskamp et al.
2018): recovering a person's symptom network from their diary.

Each of the network-inference literature's load-bearing claims is staked: a
driven diary yields estimable time-series; lag-1 VAR recovers the hub even when
individual edges are noisy; two patients with the same symptoms but different
wiring get different (correct) recovered hubs; a hub that does not vary is
unidentifiable (the honest floor); and the recovered network, re-run forward,
reproduces the original's behaviour (the loop closes).
"""
import pytest

from soma.narrative.network import (symptom_network, depression_network,
                                    stress_response, DEPRESSION_SYMPTOMS)
from soma.narrative.idiographic import (simulate_diary, estimate_network,
                                        recovery, rebuild_network,
                                        compare_hubs, Diary, TemporalNetwork)

S = DEPRESSION_SYMPTOMS

ANA_EDGES = [("insomnia", "fatigue"), ("fatigue", "mood"), ("mood", "interest"),
             ("mood", "worthless"), ("mood", "concentration"),
             ("interest", "mood"), ("worthless", "mood"), ("mood", "appetite"),
             ("mood", "suicidal"), ("concentration", "mood"),
             ("fatigue", "concentration")]
BO_EDGES = [("insomnia", "fatigue"), ("insomnia", "concentration"),
            ("insomnia", "mood"), ("insomnia", "interest"),
            ("fatigue", "concentration"), ("fatigue", "psychomotor"),
            ("fatigue", "interest"), ("insomnia", "appetite"),
            ("mood", "worthless"), ("worthless", "suicidal"), ("fatigue", "mood")]


# ---------------------------------------------------------------------------
# the diary
# ---------------------------------------------------------------------------

def test_diary_has_a_series_per_symptom():
    net = depression_network(connectivity=1.0)
    d = simulate_diary(net, days=120, seed=1)
    assert set(d.series) == set(S)
    assert d.days >= 110
    assert len(d.stress) >= d.days
    assert d.truth is net


def test_diary_is_reproducible():
    net = depression_network(connectivity=1.0)
    a = simulate_diary(net, days=80, seed=7)
    b = simulate_diary(net, days=80, seed=7)
    assert a.series["mood"] == b.series["mood"]


def test_diary_keeps_the_person_in_the_dynamic_regime():
    """The estimability precondition: symptoms must move, not lock at ceiling."""
    net = depression_network(connectivity=1.0)
    d = simulate_diary(net, days=150, seed=2)
    v = d.variances()
    # at least the downstream symptoms vary appreciably
    assert v["mood"] > 0.001
    assert max(d.series["mood"]) < 0.99   # not saturated


# ---------------------------------------------------------------------------
# estimation and recovery
# ---------------------------------------------------------------------------

def test_estimate_returns_a_temporal_network():
    net = depression_network(connectivity=1.0)
    est = estimate_network(simulate_diary(net, days=150, seed=3))
    assert isinstance(est, TemporalNetwork)
    assert set(est.A) == set(S)
    assert all(set(est.A[t]) == set(S) for t in S)


def test_recovery_finds_the_hub():
    """The robust, clinically actionable claim: the recovered out-strength hub
    is the true out-degree hub, even where individual edges are noisy."""
    net = depression_network(connectivity=1.0)
    rep = recovery(simulate_diary(net, days=200, seed=3))
    assert rep.hub_correct
    assert rep.edge_recall >= 0.4         # noisy but well above chance


def test_recovery_beats_chance_on_edges():
    net = depression_network(connectivity=1.0)
    rep = recovery(simulate_diary(net, days=250, seed=4))
    # base rate: if you picked K edges at random, expected recall = K/(N*(N-1))
    n = len(S)
    chance = rep.n_true_edges / (n * (n - 1))
    assert rep.edge_recall > 2 * chance   # comfortably above random selection


def test_more_days_do_not_hurt_hub_recovery():
    net = depression_network(connectivity=1.0)
    for days in (100, 200, 320):
        assert recovery(simulate_diary(net, days=days, seed=3)).hub_correct


# ---------------------------------------------------------------------------
# two patients, same symptoms, different wiring
# ---------------------------------------------------------------------------

def test_two_patients_get_different_recovered_hubs():
    ana = symptom_network("Ana", S, ANA_EDGES, connectivity=1.0)
    bo = symptom_network("Bo", S, BO_EDGES, connectivity=1.0,
                         thresholds={"insomnia": 1.5})
    ra = compare_hubs(simulate_diary(ana, days=250, seed=5))
    rb = compare_hubs(simulate_diary(bo, days=250, seed=5))
    assert ra["recovered_hub"] == "mood" and ra["correct"]
    assert rb["recovered_hub"] == "insomnia" and rb["correct"]
    assert ra["recovered_hub"] != rb["recovered_hub"]   # different treatment


# ---------------------------------------------------------------------------
# the identifiability floor
# ---------------------------------------------------------------------------

def test_a_constant_hub_is_unidentifiable():
    """The honest limit: a driver held nearly constant cannot be recovered,
    however central -- and becomes recoverable the moment it varies."""
    constant = symptom_network("Bo", S, BO_EDGES, connectivity=1.0,
                               thresholds={"insomnia": 4.5})
    varying = symptom_network("Bo", S, BO_EDGES, connectivity=1.0,
                              thresholds={"insomnia": 1.5})
    d_const = simulate_diary(constant, days=250, seed=5)
    d_vary = simulate_diary(varying, days=250, seed=5)
    assert d_const.variances()["insomnia"] < d_vary.variances()["insomnia"]
    assert not compare_hubs(d_const)["correct"]           # invisible
    assert compare_hubs(d_vary)["correct"]                # recovered


def test_estimable_flags_low_variance_symptoms():
    net = symptom_network("Bo", S, BO_EDGES, connectivity=1.0,
                          thresholds={"insomnia": 4.5})
    d = simulate_diary(net, days=200, seed=5)
    est = d.estimable(floor=0.001)
    assert est["insomnia"] is False       # the flat driver is flagged


# ---------------------------------------------------------------------------
# closing the loop
# ---------------------------------------------------------------------------

def test_rebuilt_network_runs_and_matches_at_extremes():
    net = depression_network(name="Mara", connectivity=1.0)
    diary = simulate_diary(net, days=220, seed=3)
    rebuilt = rebuild_network(estimate_network(diary), keep=14)
    orig = [n for _, n in stress_response(net, levels=(0, 4)).curve]
    reb = [n for _, n in stress_response(rebuilt, levels=(0, 4)).curve]
    assert orig[0] == reb[0] == 0         # both well with no stress
    assert reb[-1] >= 5                   # both depressed under high stress


def test_rebuild_keeps_only_excitatory_edges():
    net = depression_network(connectivity=1.0)
    est = estimate_network(simulate_diary(net, days=150, seed=3))
    rebuilt = rebuild_network(est, keep=10)
    assert all(w > 0 for w in rebuilt.weights.values())
    assert len(rebuilt.edges) <= 10
