"""
Tests for the 0.15 characterization layers: behavioral signatures (CAPS),
self-guides (self-discrepancy theory), and density distributions (Whole Trait
Theory). Each layer's load-bearing prediction is asserted, plus the stability
(reproducibility) claims that make the predictions falsifiable.
"""
import pytest

from soma.narrative import Story, anxious, stoic, guarded
from soma.narrative.signature import (signature, similarity,
                                      diagnostic_situation)
from soma.narrative import selfguides
from soma.narrative.density import density, compare as compare_density


# ---------------------------------------------------------------------------
# fixtures: small casts built only from library verbs
# ---------------------------------------------------------------------------

def _wediko_pair():
    """Two characters engineered toward the Wediko contrast: similar mean-level
    defensiveness, different if...then profiles. Ren defends against judgment
    and takes in warmth; Sol defends against warmth and takes in judgment."""
    story = Story("wediko", span="8s", step="1s", about="acute distress")
    ren = story.character("Ren", temperament=guarded)
    ren.senses("judgment"); ren.senses("warmth")
    ren.appraises("judgment", as_threat=True, feeling="fear",
                  precision=0.3, conviction=0.9)          # defends: act route
    ren.appraises("warmth", feeling="comfort",
                  precision=0.9, conviction=0.2, updates=True)  # takes in
    sol = story.character("Sol", temperament=guarded)
    sol.senses("judgment"); sol.senses("warmth")
    sol.appraises("judgment", feeling="fear",
                  precision=0.9, conviction=0.2, updates=True)  # takes in
    sol.appraises("warmth", as_threat=True, feeling="wariness",
                  precision=0.3, conviction=0.9)          # defends
    return story, ren, sol


BATTERY = {
    "a judging eye": {"judgment": 8},
    "an open warmth": {"warmth": 8},
}


# ---------------------------------------------------------------------------
# CAPS signatures
# ---------------------------------------------------------------------------

def test_signature_extracts_if_then_profile():
    story, ren, _ = _wediko_pair()
    sig = signature(story, ren, BATTERY)
    judged = sig.cell("a judging eye")
    warmed = sig.cell("an open warmth")
    assert judged.route == "suppress"
    assert warmed.route == "take-in"
    assert "if a judging eye" in sig.render()


def test_signature_is_stable_across_reruns():
    """CAPS's core empirical claim: the if...then profile reproduces."""
    story, ren, _ = _wediko_pair()
    a = signature(story, ren, BATTERY)
    b = signature(story, ren, BATTERY)
    assert similarity(a, b) == pytest.approx(1.0)


def test_wediko_contrast_same_mean_different_signature():
    """Trait-identical, signature-different: equal suppress rates, crossed
    profiles, low similarity."""
    story, ren, sol = _wediko_pair()
    sr = signature(story, ren, BATTERY)
    ss = signature(story, sol, BATTERY)
    assert sr.mean_level()["suppress_rate"] == ss.mean_level()["suppress_rate"]
    assert similarity(sr, ss) < 0.5


def test_diagnostic_situation_finds_a_separator():
    story, ren, sol = _wediko_pair()
    d = diagnostic_situation(story, ren, sol, BATTERY)
    assert d["situation"] in BATTERY
    assert d["separation"] > 0.5
    assert d["a"].route != d["b"].route


# ---------------------------------------------------------------------------
# self-guides (self-discrepancy theory)
# ---------------------------------------------------------------------------

def _guides_pair():
    story = Story("guides", span="8s", step="1s", about="acute distress")
    nora = story.character("Nora", temperament=anxious)
    theo = story.character("Theo", temperament=anxious)
    p_ideal = selfguides.ideal(nora, "her_craft", standard=9.0)
    p_ought = selfguides.ought(theo, "providing", standard=9.0)
    return story, nora, theo, p_ideal, p_ought


def test_predicted_families_are_derived_not_authored():
    _, _, _, p_ideal, p_ought = _guides_pair()
    assert p_ideal.family == "dejection" and p_ideal.quale == "despair"
    assert p_ought.family == "agitation" and p_ought.quale == "guilt"
    assert p_ideal.focus == "promotion" and p_ought.focus == "prevention"


def test_standpoint_refines_the_quale():
    s = Story("st", span="4s", step="1s", about="acute distress")
    c = s.character("C", temperament=anxious)
    p = selfguides.predict_shortfall(c, "ideal", "art", standpoint="other")
    q = selfguides.predict_shortfall(c, "ought", "duty", standpoint="other")
    assert p.quale == "shame" and q.quale == "fear"


def test_same_failure_different_emotion_family():
    """SDT's signature experiment: the same shortfall dejects the ideal-holder
    and agitates the ought-holder, and the predicted qualia actually fire."""
    story, nora, theo, _, _ = _guides_pair()
    out = selfguides.contrast(story, nora, theo, severity=4.0)
    assert out["Nora"]["predicted_family"] == "dejection"
    assert out["Theo"]["predicted_family"] == "agitation"
    assert out["Nora"]["confirmed"], out["Nora"]
    assert out["Theo"]["confirmed"], out["Theo"]


def test_no_shortfall_no_emission():
    """The guide is quiet while the actual self meets the standard."""
    story, nora, _, p, _ = _guides_pair()
    pred = story.predict(nora, {p.domain: 9.0})
    assert p.quale not in pred.feelings


def test_regulatory_focus_reads_off_the_guides():
    _, nora, theo, _, _ = _guides_pair()
    assert selfguides.regulatory_focus(nora)["focus"] == "promotion"
    rf = selfguides.regulatory_focus(theo)
    assert rf["focus"] == "prevention"
    assert rf["boundary_bias"] > 1.0     # prevention decides more cautiously


# ---------------------------------------------------------------------------
# density distributions (Whole Trait Theory)
# ---------------------------------------------------------------------------

def _width_pair():
    """Same mean-ish arousal, different width: Wren's heart is driven hard but
    only by strong situations (reactive -> wide); Moss's is driven a little by
    everything (flat -> narrow)."""
    story = Story("widths", span="8s", step="1s", about="acute distress")
    wren = story.character("Wren", temperament=anxious)
    wren.senses("news")
    wren.appraises("news", as_threat=True, drives="heart", to=118,
                   when="news > 6", fades_to=70)
    moss = story.character("Moss", temperament=stoic)
    moss.senses("news")
    moss.appraises("news", as_threat=True, drives="heart", to=94,
                   fades_to=70)
    return story, wren, moss


def test_density_reports_the_distribution():
    story, wren, _ = _width_pair()
    d = density(story, wren, "news", samples=12, seed=1)
    assert len(d.states) == 12
    assert d.spread[1] >= d.mean >= d.spread[0]
    assert "mean" in d.render()


def test_density_parameters_are_stable_individual_differences():
    """Fleeson: re-sample (new seed, unseen situations) and the distribution's
    parameters reproduce."""
    story, wren, _ = _width_pair()
    d1 = density(story, wren, "news", samples=16, seed=1)
    d2 = density(story, wren, "news", samples=16, seed=2)
    scale = max(d1.spread[1] - d1.spread[0], 1e-9)
    assert abs(d1.mean - d2.mean) / scale < 0.25
    assert abs(d1.sd - d2.sd) / scale < 0.25


def test_width_separates_characters_reactivity_explains_it():
    """The Fleeson contrast: the reactive character is the wide one."""
    story, wren, moss = _width_pair()
    dw = density(story, wren, "news", samples=16, seed=3)
    dm = density(story, moss, "news", samples=16, seed=3)
    cmp = compare_density(dw, dm)
    assert cmp["wider"] == "Wren"
    assert not cmp["same_width"]
    # Wren's states track the cue's strength; that reactivity is the width.
    assert dw.reactivity > 0.5


def test_defense_measure_reads_routes():
    story, ren, sol = _wediko_pair()
    dr = density(story, ren, "judgment", measure="defense",
                 state_channel="judgment", samples=8, seed=4)
    ds = density(story, sol, "judgment", measure="defense",
                 state_channel="judgment", samples=8, seed=4)
    assert dr.mean > ds.mean    # Ren defends against judgment; Sol takes it in
