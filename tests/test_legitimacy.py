"""The legitimacy layer: system justification, the palliative trade, the
exodus curve, and conscientization. Each test pins a claim of the theory as
the layer implements it (Jost & Hunyady 2002; Laurin, Shepherd & Kay 2010;
Wakslak et al. 2007; Friesen et al. 2019)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from soma.narrative import Story, guarded, stoic
from soma.narrative.legitimacy import (justifies, derived_conviction,
                                       derived_evidence_trust,
                                       palliative_tradeoff, antecedent_dose,
                                       conscientize)


# ---------------------------------------------------------------------------
# the derivations
# ---------------------------------------------------------------------------

def test_conviction_rises_with_each_antecedent():
    base = derived_conviction(dependence=0.2, inescapability=0.2)
    assert derived_conviction(dependence=0.8, inescapability=0.2) > base
    assert derived_conviction(dependence=0.2, inescapability=0.8) > base
    assert derived_conviction(dependence=0.2, inescapability=0.2,
                              threat=0.8) > base


def test_inescapability_is_the_strongest_lever():
    # Laurin et al. (2010): restricted exit is the standout antecedent
    dep = derived_conviction(dependence=0.9, inescapability=0.1)
    ine = derived_conviction(dependence=0.1, inescapability=0.9)
    assert ine > dep


def test_motivated_ignorance_lowers_evidence_trust():
    open_world = derived_evidence_trust(dependence=0.2, inescapability=0.1)
    closed = derived_evidence_trust(dependence=0.9, inescapability=0.9)
    assert closed < open_world
    assert closed >= 0.05                      # floored, never fully deaf


def test_antecedents_validated():
    import pytest
    with pytest.raises(ValueError):
        derived_conviction(dependence=1.5, inescapability=0.5)


# ---------------------------------------------------------------------------
# the wiring
# ---------------------------------------------------------------------------

def _widow(e=0.9, d=0.9):
    s = Story("t", span="16s", step="1s", about="acute distress")
    c = s.character("Neva", temperament=guarded)
    j = justifies(c, "perch", dependence=d, inescapability=e)
    return s, j


def test_justifies_wires_channels_and_lie():
    s, j = _widow()
    src = s.source()
    for ch in ("anxiety", "worth", "outrage", "harm"):
        assert ch in src
    assert "the_lie_the_perch_is_just" in src
    assert j.conviction == derived_conviction(dependence=0.9,
                                              inescapability=0.9)
    assert "let me have the luck" in j.gloss().lower() or "Neva" in j.gloss()


def test_evidence_trust_reaches_the_generated_loop():
    s, _ = _widow()
    trust = derived_evidence_trust(dependence=0.9, inescapability=0.9)
    assert f"precision:  {trust:g}" in s.source()


def test_believes_default_trust_unchanged():
    # backward compatibility: believes() without evidence_trust compiles 0.35
    s = Story("t", span="6s", step="1s", about="x")
    c = s.character("N", temperament=guarded)
    c.believes("a_lie", claim="x", disconfirmed_by="ev", breakable=True)
    assert "precision:  0.35" in s.source()


# ---------------------------------------------------------------------------
# study 1: the trade
# ---------------------------------------------------------------------------

def test_palliative_tradeoff_buys_quiet_and_charges_worth():
    def build():
        s, _ = _widow()
        return s
    rep = palliative_tradeoff(build, "Neva", harm=6.0)
    # Jost & Hunyady (2002): the belief quiets anxiety...
    assert rep.palliation > 10
    # ...and Jost & Thompson (2000): for the disadvantaged it costs worth
    assert rep.cost > 5
    assert "priced" in rep.render()


def test_advantaged_pay_no_worth_cost():
    def build():
        s = Story("t", span="16s", step="1s", about="acute distress")
        c = s.character("Lord", temperament=stoic)
        justifies(c, "perch", dependence=0.6, inescapability=0.6,
                  disadvantaged=False)
        return s
    rep = palliative_tradeoff(build, "Lord", harm=6.0)
    assert rep.palliation > 10          # the quiet is for everyone
    assert abs(rep.cost) < 5            # the bill is not


# ---------------------------------------------------------------------------
# study 2: the exodus curve
# ---------------------------------------------------------------------------

def test_exodus_tipping_point_falls_as_exits_open():
    def make(e):
        s = Story("t", span="16s", step="1s", about="acute distress")
        c = s.character("D", temperament=stoic)
        justifies(c, "perch", dependence=0.85, inescapability=e)
        return s
    rep = antecedent_dose(make, "D", levels=(0.95, 0.5, 0.1))
    tips = [tip for (_, _, tip) in rep.rows]
    assert all(t is not None for t in tips)
    assert tips[0] > tips[-1]           # closed world holds harder
    assert "solvent" in rep.render()


# ---------------------------------------------------------------------------
# study 3: conscientization
# ---------------------------------------------------------------------------

def test_conscientization_lowers_the_tipping_point():
    def make(e):
        s = Story("t", span="16s", step="1s", about="acute distress")
        c = s.character("Ink", temperament=guarded)
        justifies(c, "machine", dependence=0.7, inescapability=e)
        return s
    rep = conscientize(make, "Ink", start_inescapability=0.95,
                       per_session=0.11, sessions=(0, 8))
    (n0, _, t0), (n8, _, t8) = rep.rows
    assert t0 is not None and t8 is not None
    assert t8 < t0                       # the year with the Mender worked
    assert "thinkable" in rep.render()


# ---------------------------------------------------------------------------
# study 4: the night
# ---------------------------------------------------------------------------

def test_revelation_returns_the_grief_and_frees_the_outrage():
    s = Story("t", span="16s", step="1s", about="acute distress")
    d = s.character("D", temperament=stoic)
    justifies(d, "perch", dependence=0.85, inescapability=0.1)
    for t in range(2, 12):
        s.at(f"{t}s", d.hears("harm", 6.0))
    s.run(width=60)
    r = s.result()
    assert any(e.kind == "revelation" for e in r.chronicle)
    anx = r.channel_hist["anxiety"]
    outr = r.channel_hist["outrage"]
    assert max(anx) > 80                # the grief, whole
    assert max(outr) > 80               # the outrage, available at last


def test_closed_world_belief_survives_the_same_harm():
    s = Story("t", span="16s", step="1s", about="acute distress")
    d = s.character("D", temperament=stoic)
    justifies(d, "perch", dependence=0.85, inescapability=0.95)
    for t in range(2, 12):
        s.at(f"{t}s", d.hears("harm", 6.0))
    s.run(width=60)
    r = s.result()
    lie_revs = [e for e in r.chronicle
                if e.kind == "revelation" and e.who.startswith("the_lie_")]
    assert not lie_revs                 # at harm 6 the closed world holds
