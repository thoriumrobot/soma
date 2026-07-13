"""Fusion (identity fusion / ritual modes) and hope (Snyder agency x
pathways): each test pins a claim of the grounding literature as the layer
implements it."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from soma.narrative import Story, guarded, stoic
from soma.narrative.fusion import (derived_fusion, derived_identification,
                                   sacrifice_willingness, loyalty_under_defeat,
                                   fuses, identifies_with, sacrifice_table,
                                   defeat_curve)
from soma.narrative.hope import voyage, hope_surface, dyad, hopes


# ---------------------------------------------------------------------------
# fusion: the derivations
# ---------------------------------------------------------------------------

def test_reflection_mediates_fusion():
    # Jong et al. (2015): intensity without reflection washes out
    raw = derived_fusion(intensity=0.9, reflection=0.1)
    turned_over = derived_fusion(intensity=0.9, reflection=0.9)
    assert turned_over > raw + 0.3


def test_unshared_ordeal_transforms_without_fusing():
    shared = derived_fusion(intensity=0.9, reflection=0.8, shared=True)
    alone = derived_fusion(intensity=0.9, reflection=0.8, shared=False)
    assert alone < 0.5 * shared + 0.1


def test_doctrinal_participation_caps_below_fusion_ceiling():
    assert derived_identification(participation=1.0) <= 0.85
    with pytest.raises(ValueError):
        derived_identification(participation=1.5)


# ---------------------------------------------------------------------------
# fusion: the predictions
# ---------------------------------------------------------------------------

def test_fused_pay_what_identified_applaud():
    # matched bond strength; the worst hour separates them
    f = sacrifice_willingness(0.7, kind="fused", threat=0.95)
    i = sacrifice_willingness(0.7, kind="identified", threat=0.95)
    assert f > 2 * i


def test_threat_amplifies_the_fused_response_more():
    f_gain = (sacrifice_willingness(0.7, kind="fused", threat=0.95)
              - sacrifice_willingness(0.7, kind="fused", threat=0.1))
    i_gain = (sacrifice_willingness(0.7, kind="identified", threat=0.95)
              - sacrifice_willingness(0.7, kind="identified", threat=0.1))
    assert f_gain > 2 * i_gain


def test_defeat_reprices_identification_not_fusion():
    ident = loyalty_under_defeat(0.7, kind="identified", defeats=3)
    fused = loyalty_under_defeat(0.7, kind="fused", defeats=3,
                                 reflection=0.8)
    assert ident[-1][1] < 0.35 * ident[0][1]      # the bet, re-priced
    assert fused[-1][1] > 0.85 * fused[0][1]      # the self, near-stable


def test_fusion_wiring_mobilizes_the_body():
    s = Story("t", span="12s", step="1s", about="the worst hour")
    c = s.character("Topman", temperament=stoic)
    b = fuses(c, "fleet", intensity=0.9, reflection=0.8)
    for t in range(2, 10):
        s.at(f"{t}s", c.hears("fleet_threat", 8))
    r = s.result()
    assert max(r.channel_hist["for_the_group"]) > 60
    assert "fused" in b.gloss()


def test_identification_wiring_attends_not_pays():
    s = Story("t", span="12s", step="1s", about="the worst hour")
    c = s.character("Rowholder", temperament=guarded)
    identifies_with(c, "perch", participation=0.85)
    for t in range(2, 10):
        s.at(f"{t}s", c.hears("perch_threat", 8))
    r = s.result()
    assert max(r.channel_hist["for_the_group"]) < 45


def test_study_renders_carry_their_claims():
    rep = defeat_curve([("a", "fused", 0.7), ("b", "identified", 0.7)])
    assert "re-prices" in rep.render()
    rep2 = sacrifice_table([("a", "fused", 0.7)])
    assert "fusion pays" in rep2.render()


# ---------------------------------------------------------------------------
# hope: the machine
# ---------------------------------------------------------------------------

def test_hope_is_multiplicative_not_additive():
    surf = hope_surface(levels=(0.2, 0.8), blockages=7, samples=16)
    hi_hi = surf.grid[(0.8, 0.8)]
    a_only = surf.grid[(0.8, 0.2)]
    p_only = surf.grid[(0.2, 0.8)]
    assert hi_hi >= 0.85
    assert a_only < 0.5 and hi_hi > a_only + 0.4
    assert hi_hi > p_only            # the product beats either component


def test_overcome_blockages_feed_agency():
    v = voyage(0.6, 0.9, blockages=7, seed=2)
    assert v.reached
    assert v.agency_final > v.agency0     # the catalog of past effectiveness


def test_low_pathways_turns_back_and_agency_erodes():
    outs = [voyage(0.85, 0.15, blockages=7, seed=100 + s * 17, max_beats=90)
            for s in range(12)]
    fails = [v for v in outs if not v.reached]
    assert len(fails) >= 8
    assert all(v.agency_final < v.agency0 for v in fails)


def test_dyad_pools_into_one_high_hope_agent():
    d = dyad(blockages=7, samples=16, stores=90)
    assert d.together >= 0.85
    assert d.together > d.alone_a + 0.4
    assert d.together > d.alone_p + 0.2


def test_hopes_wiring_routes_or_despairs():
    s = Story("t", span="12s", step="1s", about="a wall")
    high = s.character("Ink", temperament=guarded)
    hopes(high, "the far shore", agency=0.8, pathways=0.9)
    s2 = Story("t2", span="12s", step="1s", about="a wall")
    low = s2.character("Vane", temperament=guarded)
    hopes(low, "the far shore", agency=0.8, pathways=0.1)
    for t in range(2, 10):
        s.at(f"{t}s", high.hears("blockage", 8))
        s2.at(f"{t}s", low.hears("blockage", 8))
    r1, r2 = s.result(), s2.result()
    assert max(r1.channel_hist["resolve"]) > max(r2.channel_hist["resolve"])
    assert max(r2.channel_hist["despair"]) > max(r1.channel_hist["despair"])


def test_hope_dials_validated():
    s = Story("t", span="6s", step="1s", about="x")
    c = s.character("N", temperament=guarded)
    with pytest.raises(ValueError):
        hopes(c, "goal", agency=1.5, pathways=0.5)
