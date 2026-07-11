"""
SOMA test suite. Run with:  python -m pytest -q   (from the soma_lang dir)
or standalone:               python tests/test_soma.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from soma import parse, run_source
from soma.checker import check, SomaTypeError, ConsentError
from soma.chronicle import Qualia
from soma import winnow
from soma.lexer import tokenize

EX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples")


def _q(e):
    q = e.detail.get("quale", "")
    return q[7:-1] if q.startswith("Qualia<") else q


# ---------- lexer / parser ----------
def test_parse_minimal():
    prog = parse("sim { duration: 2s dt: 1s }\nbody B @cardiac { intero h : BPM baseline 70 }")
    assert prog.sim.duration == 2.0 and prog.sim.dt == 1.0
    assert prog.bodies[0].channels[0].baseline == 70

def test_unicode_aliases_parse():
    # the spec's Unicode loop brackets and down-arrow must still parse
    src = ("body B @cardiac { intero h : BPM baseline 1 }\n"
           "loop l @neural ◜ prior: 0 sense: h precision: 0.9 "
           "act { update ⤋ 5 } ◞")
    prog = parse(src)
    assert prog.loops[0].name == "l"

def test_duration_units():
    prog = parse("sim { duration: 2m dt: 30s }")
    assert prog.sim.duration == 120.0 and prog.sim.dt == 30.0


# ---------- the signature type-level guarantees ----------
def test_qualia_is_opaque_at_runtime():
    q = Qualia("dread")
    with pytest.raises(TypeError):
        float(q)

def test_qualia_opacity_is_a_compile_error():
    # feel() may not be used in arithmetic
    src = ('@consent("x")\nbody B @cardiac { intero h : BPM baseline 1 }\n'
           'loop l @neural { prior: 0 sense: h precision: 0.9 '
           'act { update -> feel(dread) + 1 } }')
    with pytest.raises(SomaTypeError):
        check(parse(src))

def test_consent_required_for_distress():
    src = ('body B @cardiac { intero h : BPM baseline 1 }\n'
           'loop l @neural { prior: 0 sense: h precision: 0.9 '
           'act { emit feel(dread) } }')
    with pytest.raises(ConsentError):
        check(parse(src))

def test_functional_only_bypasses_consent():
    src = ('body B @cardiac { intero h : BPM baseline 1 }\n'
           'loop l @neural { prior: 0 sense: h precision: 0.9 '
           'act { emit feel(dread) } }')
    check(parse(src), functional_only=True)   # must not raise

def test_affine_rebind_rejected():
    src = ('resource budget : Affine<Joule> = metabolic_reserve(100)\n'
           'let budget = 5')
    with pytest.raises(SomaTypeError):
        check(parse(src))


# ---------- affine runtime: the body cannot conjure ----------
def test_budget_never_goes_negative():
    res = run_source(open(os.path.join(EX, "bad_news.soma")).read(), title="bad_news")
    lefts = [e.detail["left"] for e in res.chronicle if e.kind == "spend"]
    assert lefts and min(lefts) >= 0.0
    # and an overspend was recorded once it hit zero
    assert any(e.kind == "budget" for e in res.chronicle)


# ---------- worked examples produce the intended drama ----------
def test_bad_news_confabulation_gap():
    res = run_source(open(os.path.join(EX, "bad_news.soma")).read(), title="bad_news")
    dread = [e for e in res.chronicle if e.kind == "emit" and _q(e) == "dread"]
    assert len(dread) >= 3
    gaps = [e.detail["gap"] for e in res.chronicle if e.kind == "narrate"]
    assert max(gaps) == pytest.approx(0.55)

def test_split_brain_confabulates():
    res = run_source(open(os.path.join(EX, "split_brain.soma")).read(), title="split_brain")
    finds = winnow.sift(res.chronicle, "confabulation")
    assert finds and max(f.score for f in finds) >= 0.9

def test_chronic_pain_precision_pathology():
    res = run_source(open(os.path.join(EX, "chronic_pain.soma")).read(), title="chronic_pain")
    finds = winnow.sift(res.chronicle, "precision-pathology")
    assert finds, "expected a precision pathology to surface"

def test_trauma_crashes_then_repairs():
    res = run_source(open(os.path.join(EX, "trauma.soma")).read(), title="trauma")
    kinds = [e.kind for e in res.chronicle]
    assert "crash" in kinds and "repair" in kinds
    finds = winnow.sift(res.chronicle, "rupture-repair")
    assert finds and "re-supervised" in finds[0].text

def test_grief_body_outlasts_mind():
    res = run_source(open(os.path.join(EX, "grief.soma")).read(), title="grief")
    reaching = [e for e in res.chronicle if e.kind == "emit" and _q(e) == "reaching"]
    assert len(reaching) >= 3
    finds = winnow.sift(res.chronicle, "retained-residual")
    assert finds

def test_love_is_rewarded_by_error():
    res = run_source(open(os.path.join(EX, "in_love.soma")).read(), title="in_love")
    finds = winnow.sift(res.chronicle, "delight-in-error")
    assert finds
    # love is NOT flagged as a distress residual
    assert not winnow.sift(res.chronicle, "retained-residual")




# ============================================================
#  0.3 features: workspace, attention, memory, embodiment,
#  ownership, flows, allostasis, REBUS, queries, phi
# ============================================================

from soma import query as qmod, observables, mathlib
from soma.parser import parse as _parse


def _run(name):
    return run_source(open(os.path.join(EX, name + ".soma")).read(), title=name)


# ---------- new static rules ----------
def test_attention_schema_is_transparent():
    """introspect() on an awareness is a static error (Graziano/ilion rule)."""
    src = ('attention spot = capacity(3)\n'
           'awareness aw tracks spot\n'
           'body B @cardiac { intero h : BPM baseline 1 }\n'
           'loop l @neural { prior: introspect(aw) sense: h precision: 0.9 '
           'act { ignore } }')
    with pytest.raises(SomaTypeError):
        check(_parse(src))


def test_awareness_must_track_declared_attention():
    src = 'awareness aw tracks nonexistent\n'
    with pytest.raises(SomaTypeError):
        check(_parse(src))


def test_memory_register_must_be_known():
    src = ('body B @cardiac { extero s : Smell baseline 0 }\n'
           'memory prophetic m { cue: s when: s > 1 evoke: feel(warmth) }')
    with pytest.raises(SomaTypeError):
        check(_parse(src))


def test_memory_cue_must_be_declared():
    src = ('body B @cardiac { extero s : Smell baseline 0 }\n'
           'memory somatic m { cue: ghost when: s > 1 evoke: feel(warmth) }')
    with pytest.raises(SomaTypeError):
        check(_parse(src))


def test_loop_mode_must_be_habit_or_deliberate():
    src = ('body B @cardiac { intero h : BPM baseline 1 }\n'
           'loop l @neural { prior: 0 sense: h precision: 0.9 mode: dreaming '
           'act { ignore } }')
    with pytest.raises(SomaTypeError):
        check(_parse(src))


def test_somatic_distress_memory_requires_consent():
    src = ('body B @cardiac { extero s : Smell baseline 0 }\n'
           'memory somatic m { cue: s when: s > 1 evoke: feel(terror) }')
    with pytest.raises(ConsentError):
        check(_parse(src))


def test_rebus_requires_consent():
    src = 'intervene rebus { at: 1s strength: 0.5 }'
    with pytest.raises(ConsentError):
        check(_parse(src))


# ---------- syntax additions ----------
def test_unary_minus_parses():
    prog = _parse("body B @cardiac { intero h : BPM baseline 1 }\n"
                  "flow h @cardiac { dynamics: -(h - 70) / 4.0 }")
    assert prog.flows and prog.flows[0].channel == "h"


def test_soft_keywords_may_name_things():
    # `spotlight` and `tolerance` are keywords, but legal as names
    prog = _parse("attention spotlight = capacity(4)\nlet tolerance = 6")
    assert prog.attentions[0].name == "spotlight"
    assert prog.lets[0].name == "tolerance"


# ---------- continuous physiology ----------
def test_flow_integrates_toward_equilibrium():
    src = ("sim { duration: 20s dt: 0.5s }\n"
           "body B @cardiac { intero h : BPM baseline 120 }\n"
           "flow h @cardiac { dynamics: -(h - 70) / 2.0 }")
    res = run_source(src, title="flow")
    assert res.channel_hist["h"][0] > 100
    assert abs(res.channel_hist["h"][-1] - 70) < 1.0   # decays to setpoint


def test_allostat_regulates_predictively():
    res = _run("workspace")
    assert any(e.kind == "allostat" for e in res.chronicle)
    # heart is pushed up toward the allostatic setpoint, above its baseline
    assert max(res.channel_hist["heart"]) > 80


# ---------- body schema vs body image ----------
def test_phantom_limb_conflict_is_a_formal_event():
    res = _run("phantom_limb")
    assert any(e.kind == "conflict" for e in res.chronicle)
    finds = winnow.sift(res.chronicle, "schema-image-conflict")
    assert finds and "not the same hand" in finds[0].text


# ---------- ownership as a dependent type ----------
def test_rubber_hand_ownership_migrates():
    res = _run("rubber_hand")
    own = [e for e in res.chronicle if e.kind == "ownership"]
    states = [e.detail["state"] for e in own]
    # the rubber hand starts alien, becomes his under synchronous stroking,
    # then is disowned when it is moved on its own
    assert "owned" in states and "disowned" in states
    assert states.index("owned") < states.index("disowned")


def test_ownership_initial_state_is_declarable():
    src = """
    sim { duration: 4s dt: 1s }
    body b @cardiac { proprio felt : P baseline 8  proprio seen : P baseline 0 }
    ownership hand { predicted: felt  observed: seen  tolerance: 2  initial: alien }
    loop l @neural { prior: predict(felt) sense: seen precision: 0.9 conviction: 0.3
                     act { emit feel(warmth) when owned(hand) } }
    """
    r = run_source(src)
    # gap is 8 > tolerance 2, and initial is alien, so it is never owned:
    # the guarded emit never fires
    assert not [e for e in r.chronicle if e.kind == "emit"]


# ---------- memory registers ----------
def test_somatic_memory_fires_without_episodic_trace():
    res = _run("flashback")
    som = [e for e in res.chronicle if e.kind == "somatic"]
    assert som
    assert not [e for e in res.chronicle
                if e.kind == "recall" and e.detail.get("register") == "episodic"]
    finds = winnow.sift(res.chronicle, "body-remembers-alone")
    assert finds


# ---------- global workspace ----------
def test_loud_content_ignites_and_quiet_content_does_not():
    res = _run("workspace")
    ignited = {e.detail["content"] for e in res.chronicle if e.kind == "ignite"}
    assert "they_are_watching_me" in ignited
    assert "something_is_wrong" not in ignited     # felt, never known
    finds = winnow.sift(res.chronicle, "never-ignited")
    assert any("something_is_wrong" in f.text for f in finds)


# ---------- attention as an affine spotlight ----------
def test_attention_is_spent_and_can_starve_deliberation():
    res = _run("workspace")
    assert any(e.kind == "attend" for e in res.chronicle)
    assert any(e.kind == "starved" for e in res.chronicle)
    assert min(res.attn_hist["spotlight"]) >= 0.0     # never negative


def test_habit_loops_do_not_pay_attention():
    src = ("sim { duration: 3s dt: 1s }\n"
           "attention spot = capacity(1)\n"
           "body B @cardiac { intero h : BPM baseline 0 }\n"
           "stimulus h { at 1s: 9 }\n"
           "loop cheap @neural { prior: 0 sense: h precision: 0.9 mode: habit "
           "act { move ! flinch } }")
    res = run_source(src, title="habit")
    assert not [e for e in res.chronicle if e.kind == "starved"]
    assert [e for e in res.chronicle if e.kind == "move"]


# ---------- reafference ----------
def test_efference_copy_cancels_self_caused_signal():
    """You cannot tickle yourself: the self-caused part of the afferent signal
    is subtracted before the error is formed."""
    base = ("sim {{ duration: 4s dt: 1s }}\n"
            "body B @cardiac {{ intero h : BPM baseline 0 gain 1.0 "
            "extero w : S baseline 0 }}\n"
            "stimulus w {{ at 1s: 9 }}\n"
            "loop actor @neural {{ prior: 0 sense: w precision: 0.9 "
            "act {{ move ! set(h, 10) }} }}\n"
            "loop feeler @cardiac {{ prior: 0 sense: h precision: 0.9 {eff} "
            "act {{ move ! notice }} }}")
    with_eff = run_source(base.format(eff="efference: actor"), title="eff")
    no_eff = run_source(base.format(eff=""), title="noeff")
    n_with = len([e for e in with_eff.chronicle if e.kind == "move"
                  and e.who == "feeler"])
    n_without = len([e for e in no_eff.chronicle if e.kind == "move"
                     and e.who == "feeler"])
    assert n_without > 0
    assert n_with < n_without   # the self-caused signal stopped being news


# ---------- REBUS ----------
def test_rebus_relaxes_priors_and_lets_the_world_in():
    res = _run("rebus")
    routes = [(e.t, e.detail["route"]) for e in res.chronicle if e.kind == "settle"]
    before = [r for t, r in routes if t < 30]
    after = [r for t, r in routes if t > 30]
    assert set(before) == {"act"}          # nothing got in
    assert set(after) == {"perceive"}      # everything did
    # the entrenched belief actually moves toward the evidence
    assert any(e.kind == "rebus" for e in res.chronicle)


def test_ignore_only_suppresses_while_the_prior_outranks():
    res = _run("rebus")
    ignores = [e.t for e in res.chronicle if e.kind == "ignore"]
    assert ignores and max(ignores) < 30.0


# ---------- the general query language ----------
def test_query_engine_joins_and_filters():
    prog = _parse(open(os.path.join(EX, "flashback.soma")).read())
    res = _run("flashback")
    rows = qmod.run_query(prog.queries[0], res.chronicle)
    assert rows and "the_road" in rows[0].text


def test_query_where_clause_prunes():
    src = ('sim { duration: 4s dt: 1s }\n'
           'body B @cardiac { extero w : S baseline 0 }\n'
           'stimulus w { at 1s: 9 }\n'
           'loop l @neural { prior: 0 sense: w precision: 0.9 '
           'act { emit feel(delight) } }\n'
           'query "late only" { feel ?lp ?q ?t  where ?t > 2  '
           'surface "{?lp} at {?t}" }')
    res = run_source(src, title="q")
    prog = _parse(src)
    rows = qmod.run_query(prog.queries[0], res.chronicle)
    assert rows and all(r.t > 2 for r in rows)


# ---------- integrated information ----------
def test_phi_is_zero_for_an_uncoupled_system():
    src = ("sim { duration: 3s dt: 1s }\n"
           "body B @cardiac { intero a : X baseline 1  intero b : Y baseline 1 }\n"
           "stimulus a { at 1s: 5 }\nstimulus b { at 1s: 5 }")
    res = run_source(src, title="uncoupled")
    phi = observables.integrated_information(res.interp, ["a", "b"])
    assert phi["ok"] and phi["phi_bits"] == pytest.approx(0.0, abs=1e-6)


def test_phi_detects_coupling():
    res = _run("bad_news")
    phi = observables.integrated_information(res.interp, ["ear", "heart", "gut"])
    assert phi["ok"] and phi["phi_bits"] > 0.0
    assert 0.0 <= phi["determinism"] <= 1.0


def test_phi_does_not_pollute_the_chronicle():
    """A counterfactual intervention must not enter the character's history."""
    res = _run("bad_news")
    before = len(res.chronicle)
    observables.integrated_information(res.interp, ["ear", "heart"])
    assert len(res.chronicle) == before


# ---------- ported ilion stdlib functions ----------
def test_ilion_stdlib_functions_are_callable_from_soma():
    src = ("sim { duration: 2s dt: 1s }\n"
           "body B @cardiac { intero h : BPM baseline 0 }\n"
           "stimulus h { at 1s: 9 }\n"
           "loop l @neural { prior: 0 sense: h "
           "precision: 0.9 act { move ! set(h, sigmoid(2.0)) } }")
    res = run_source(src, title="stdlib")
    assert any(e.kind == "drive" for e in res.chronicle)


def test_exafference_and_intero_precision_math():
    assert mathlib.exafference(10, 10, 1.0) == pytest.approx(0.0)
    hi = mathlib.intero_precision(arousal=0.0, noise=0.5)
    lo = mathlib.intero_precision(arousal=3.0, noise=0.5)
    assert hi > lo      # an aroused body trusts its own signals less




# ============================================================================
# 0.4 -- intersubjectivity, narrative structure, learning, guards
# ============================================================================

TWO = """
body A_only @cardiac { extero f : E baseline 1 }
character Ana {
  body flesh @cardiac { proprio face : E baseline 5  extero his : E baseline 5 }
}
character Ivo {
  body flesh @cardiac { extero her : E baseline 5 }
}
couple Ana.face -> Ivo.her { gain 0.5 lag 2s }
"""


def test_character_scoping_qualifies_names():
    p = parse(TWO)
    names = {c.name for b in p.bodies for c in b.channels}
    assert "Ana.face" in names and "Ivo.her" in names
    assert "f" in names                      # unscoped decls stay bare
    assert p.characters == ["Ana", "Ivo"]


def test_dotted_names_are_single_tokens():
    toks = [t for t in tokenize("couple Bob.face -> Ann.sees")]
    ids = [t.value for t in toks if t.type == "ID"]
    assert "Bob.face" in ids and "Ann.sees" in ids
    # ...and a float is still a float
    assert any(t.type == "NUM" and t.value == "1.5" for t in tokenize("x 1.5"))


def test_couple_transmits_with_gain_and_lag():
    src = """
    sim { duration: 6s dt: 1s }
    character Ana { body b @cardiac { proprio face : E baseline 0 } }
    character Ivo { body b @cardiac { extero her : E baseline 0 } }
    couple Ana.face -> Ivo.her { gain 0.5 lag 2s }
    stimulus Ana.face { at 1s: 10 }
    """
    r = run_source(src)
    her = r.channel_hist["Ivo.her"]
    assert her[1] == 0.0                     # the lag is real: not yet
    assert any(abs(v - 5.0) < 1e-6 for v in her)   # gain 0.5 applied


def test_no_character_may_sense_anothers_interior():
    src = """
    character Ana { body b @cardiac { intero gut : T baseline 1 } }
    character Ivo {
      body b @cardiac { extero x : E baseline 0 }
      loop pry @neural { prior: 0 sense: Ana.gut precision: 0.9 act { ignore } }
    }
    """
    with pytest.raises(SomaTypeError):
        check(parse(src))


def test_couple_may_not_carry_interoception():
    src = """
    character Ana { body b @cardiac { intero gut : T baseline 1 } }
    character Ivo { body b @cardiac { extero x : E baseline 0 } }
    couple Ana.gut -> Ivo.x { gain 1.0 }
    """
    with pytest.raises(SomaTypeError):
        check(parse(src))


def test_learn_hardens_the_prior_until_route_flips():
    src = """
    sim { duration: 20s dt: 1s }
    body b @cardiac { extero f : E baseline 0 }
    loop l @neural {
      prior: predict(5) sense: f precision: 0.5 conviction: 0.2 learn: 0.1
      act { emit feel(calm) }
    }
    stimulus f { at 0s: 0 }
    """
    r = run_source(src)
    settles = [e for e in r.chronicle if e.kind == "settle" and e.who == "l"]
    pis = [e.detail["pi_p"] for e in settles]
    assert pis[-1] > pis[0]                  # experience hardened it
    routes = [e.detail["route"] for e in settles]
    assert routes[0] == "perceive" and routes[-1] == "act"   # and it flipped


def test_learn_is_capped():
    from soma.interpreter import LEARN_CAP
    src = """
    sim { duration: 200s dt: 1s }
    body b @cardiac { extero f : E baseline 0 }
    loop l @neural { prior: predict(9) sense: f precision: 0.1 conviction: 0.1
                     learn: 0.5 act { ignore } }
    """
    r = run_source(src)
    pis = [e.detail["pi_p"] for e in r.chronicle if e.kind == "settle"]
    assert max(pis) <= 0.1 + LEARN_CAP + 1e-9


def test_guard_suppresses_the_act():
    src = """
    sim { duration: 4s dt: 1s }
    body b @cardiac { extero f : E baseline 9 }
    loop l @neural { prior: predict(0) sense: f precision: 0.9 conviction: 0.1
                     act { emit feel(calm) when f < 1 } }
    """
    r = run_source(src)
    assert not [e for e in r.chronicle if e.kind == "emit"]


def test_guard_permits_the_act_when_true():
    src = """
    sim { duration: 4s dt: 1s }
    body b @cardiac { extero f : E baseline 9 }
    loop l @neural { prior: predict(0) sense: f precision: 0.9 conviction: 0.1
                     act { emit feel(calm) when f > 1 } }
    """
    r = run_source(src)
    assert [e for e in r.chronicle if e.kind == "emit"]


def test_consent_is_checked_through_a_guard():
    src = """
    body b @cardiac { extero f : E baseline 9 }
    loop l @neural { prior: 0 sense: f precision: 0.9
                     act { emit feel(terror) when f > 1 } }
    """
    with pytest.raises(ConsentError):
        check(parse(src))          # a guard is not a way to smuggle distress in


def test_scenes_partition_the_chronicle():
    src = """
    sim { duration: 6s dt: 1s }
    scene "one" from 0s to 2s
    scene "two" from 3s to 6s
    body b @cardiac { extero f : E baseline 0 }
    """
    r = run_source(src)
    marks = [e.who for e in r.chronicle if e.kind == "scene"]
    assert marks == ["one", "two"]


def test_each_character_spends_only_their_own_spotlight():
    """Nadia's capacity to attend is not available to Hal."""
    src = """
    sim { duration: 6s dt: 1s }
    character Nadia {
      body b @cardiac { extero f : E baseline 9 }
      attention spotlight = capacity(1)
      loop think @neural { prior: predict(0) sense: f precision: 0.9
                           conviction: 0.1 mode: deliberate act { ignore } }
    }
    character Hal {
      body b @cardiac { extero g : E baseline 9 }
      loop talk @neural { prior: predict(0) sense: g precision: 0.9
                          conviction: 0.1 mode: deliberate act { move ! set(g, 3) } }
    }
    """
    r = run_source(src)
    starved = {e.who for e in r.chronicle if e.kind == "starved"}
    assert "Hal.talk" not in starved          # he has no spotlight to starve
    assert [e for e in r.chronicle if e.kind == "drive" and e.who == "Hal.talk"]


def test_priors_may_read_embodiment_channels():
    """Channels must exist before any loop evaluates its prior."""
    src = """
    sim { duration: 2s dt: 1s }
    embodiment e { pair arm : schema = 7 image = 2 tolerance 9 }
    loop l @neural { prior: predict(arm_image) sense: arm_schema
                     precision: 0.9 conviction: 0.1 act { ignore } }
    """
    r = run_source(src)
    first = [e for e in r.chronicle if e.kind == "settle"][0]
    assert first.detail["belief"] == 2.0      # not 0.0


def test_efference_copy_cancels_the_change_not_the_world():
    """Subtracting the absolute action value would make the body deny itself."""
    src = """
    sim { duration: 3s dt: 1s }
    body b @cardiac { intero h : BPM baseline 70 efference mover gain 1.0 }
    loop mover @neural { prior: predict(70) sense: h precision: 0.9 conviction: 0.1
                         act { move ! set(h, 90) } }
    """
    r = run_source(src)
    settles = [e for e in r.chronicle if e.kind == "settle"]
    # after the mover raises h to 90, the sensed value is corrected back toward
    # baseline by exactly the change it caused -- not to -20.
    assert all(s.detail["sense"] > 0 for s in settles)


def test_stimulus_beats_a_coupling_in_the_same_frame():
    src = """
    sim { duration: 4s dt: 1s }
    character A { body b @cardiac { proprio face : E baseline 0 } }
    character B { body b @cardiac { extero seen : E baseline 0 } }
    couple A.face -> B.seen { gain 1.0 }
    stimulus B.seen { at 2s: 42 }
    """
    r = run_source(src)
    assert 42.0 in r.channel_hist["B.seen"]   # the world can interrupt a face


def test_flow_resolves_channels_in_its_owner_scope():
    src = """
    sim { duration: 5s dt: 1s }
    character Ana {
      body b @cardiac { intero heart : BPM baseline 74 }
      flow heart @cardiac { dynamics: -(heart - 74) / 4.0 }
    }
    """
    r = run_source(src)
    h = r.channel_hist["Ana.heart"]
    assert all(abs(v - 74.0) < 1e-6 for v in h)   # at rest it stays at rest


def test_perturb_diffs_the_story():
    from soma.perturb import perturb, PerturbError
    src = """
    @consent("test")
    sim { duration: 20s dt: 1s }
    body b @cardiac { extero f : E baseline 0 }
    loop l @neural { prior: predict(9) sense: f precision: 0.8 conviction: 0.2
                     act { emit feel(dread) ignore } }
    """
    d = perturb(src, "l.conviction=0.99")
    assert "l.conviction" in d.change
    assert d.gained or d.lost or d.shifted     # the dial was load-bearing
    with pytest.raises(PerturbError):
        perturb(src, "nosuchloop.precision=0.5")


def test_prose_renders_from_logged_events_only():
    from soma import prose
    src = """
    @consent("test")
    sim { duration: 4s dt: 1s }
    scene "beat" from 0s to 4s
    body b @cardiac { extero f : E baseline 9 }
    loop l @neural { prior: predict(0) sense: f precision: 0.9 conviction: 0.1
                     act { emit feel(dread) } }
    """
    r = run_source(src)
    text = prose.render(r, genders={"l": "she"})
    assert "beat" in text
    assert "stomach" in text            # the dread lexicon fired
    assert "Qualia<" not in text        # no machine tokens leak onto the page


def test_perturb_reaches_beyond_loops():
    """The novelist's best question is often not about a loop."""
    from soma.perturb import perturb
    src = """
    sim { duration: 8s dt: 1s }
    body b @cardiac { extero f : E baseline 0 }
    attention spotlight = capacity(3)
    workspace mind { ignite at 0.9 }
    loop l @neural {
      prior: predict(9) sense: f precision: 0.8 conviction: 0.2
      act { broadcast a_quiet_worry salience: 0.5 }
    }
    """
    r0 = run_source(src)
    assert not [e for e in r0.chronicle if e.kind == "ignite"]
    d = perturb(src, "mind.threshold=0.3")
    assert "threshold" in d.change
    assert [e for e in d.new_result.chronicle if e.kind == "ignite"]

    d2 = perturb(src, "spotlight.capacity=99")
    assert "capacity" in d2.change


# ============================================================================
# 0.5 -- dynamic precision, readable arbitration, signed moods
# ============================================================================

def test_precision_may_be_an_expression_reevaluated_each_moment():
    src = """
    sim { duration: 6s dt: 1s }
    body b @cardiac { intero pain : P baseline 8  extero deference : D baseline 0 }
    loop feel_it @cardiac {
      prior: predict(0) sense: pain
      precision: clamp(0.95 - 0.7 * deference, 0.2, 1.0)
      conviction: 0.5 act { ignore }
    }
    stimulus deference { at 3s: 1.0 }
    """
    r = run_source(src)
    pis = [e.detail["pi_s"] for e in r.chronicle if e.kind == "settle"]
    assert pis[0] > 0.9 and pis[-1] < 0.5
    routes = [e.detail["route"] for e in r.chronicle if e.kind == "settle"]
    # high sensory precision -> perceive; once it falls below conviction -> act
    assert routes[0] == "perceive" and routes[-1] == "act"


def test_precision_driven_to_the_floor_is_ignored():
    """A channel attenuated to the ATTENUATED floor carries no usable evidence,
    so it is ignored -- the belief can be neither updated nor acted out on it."""
    src = """
    sim { duration: 6s dt: 1s }
    body b @cardiac { intero pain : P baseline 8  extero deference : D baseline 0 }
    loop feel_it @cardiac {
      prior: predict(0) sense: pain
      precision: clamp(0.95 - 0.9 * deference, 0.05, 1.0)
      conviction: 0.5 act { move ! set(pain, 99) } }
    stimulus deference { at 3s: 1.0 }
    """
    r = run_source(src)
    routes = [e.detail["route"] for e in r.chronicle if e.kind == "settle"]
    assert routes[-1] == "ignore"
    # and nothing was driven while ignored
    late = [e for e in r.chronicle if e.kind == "drive" and e.t >= 3]
    assert not late


def test_precision_expression_is_clamped_nonnegative():
    src = """
    sim { duration: 2s dt: 1s }
    body b @cardiac { intero p : P baseline 5 }
    loop l @neural { prior: predict(0) sense: p precision: 0 - 4 conviction: 0.5
                     act { ignore } }
    """
    r = run_source(src)
    assert all(e.detail["pi_s"] >= 0 for e in r.chronicle if e.kind == "settle")


def test_qualia_may_not_be_coerced_into_a_precision():
    src = """
    body b @cardiac { intero p : P baseline 1 }
    loop l @neural { prior: 0 sense: p precision: feel(dread) act { ignore } }
    """
    with pytest.raises(SomaTypeError):
        check(parse(src))


def test_acting_and_perceiving_are_readable():
    """The arbitration outcome is visible to the program that made it."""
    base = """
    sim { duration: 4s dt: 1s }
    body b @cardiac { extero f : E baseline 2  proprio v : V baseline 0 }
    loop l @neural { prior: predict(9) sense: f precision: 0.4 conviction: %s
      act { move ! set(v, 7) when acting  move ! set(v, 1) when perceiving } }
    """
    assert 7.0 in run_source(base % "0.9").channel_hist["v"]    # prior wins: acts
    assert 1.0 in run_source(base % "0.05").channel_hist["v"]   # senses win: perceives


def test_belief_builtin_reads_a_loop():
    src = """
    sim { duration: 3s dt: 1s }
    body b @cardiac { extero f : E baseline 4  proprio out : O baseline 0 }
    loop l @neural { prior: predict(9) sense: f precision: 0.9 conviction: 0.1
                     act { update -> revised } }
    loop m @neural { prior: predict(0) sense: f precision: 0.9 conviction: 0.1
                     act { move ! set(out, belief(l)) } }
    """
    r = run_source(src)
    assert max(r.channel_hist["out"]) > 0     # m could read l's expectation


def test_mood_weights_may_be_signed():
    """A weight multiplies a quale's valence, so a negative weight inverts it."""
    src = """
    sim { duration: 4s dt: 1s }
    body b @cardiac { extero f : E baseline 9 }
    loop l @neural { prior: predict(0) sense: f precision: 0.9 conviction: 0.1
                     act { emit feel(calm) } }
    mood weather : Affect @mood integrates { calm * %s } decay 0.9
    """
    pos = run_source(src % "0.6").mood_hist["weather"][-1]
    neg = run_source(src % "-0.6").mood_hist["weather"][-1]
    assert pos > 0 > neg


def test_a_narrator_speaks_only_for_its_own_character():
    src = """
    sim { duration: 3s dt: 1s }
    character Ana {
      body b @cardiac { extero f : E baseline 9 }
      loop l @neural { prior: predict(0) sense: f precision: 0.9 conviction: 0.1
                       act { move ! flinch() } }
      narrator self subscribes { l } confabulates true
    }
    character Ivo {
      body b @cardiac { extero g : E baseline 9 }
      loop m @neural { prior: predict(0) sense: g precision: 0.9 conviction: 0.1
                       act { move ! shrug() } }
      narrator self subscribes { m } confabulates true
    }
    """
    r = run_source(src)
    for e in r.chronicle:
        if e.kind == "narrate":
            about = e.detail.get("about", "")
            if e.who == "Ana.self":
                assert about != "shrug"       # she does not explain his shrug
            if e.who == "Ivo.self":
                assert about != "flinch"


def test_confabulation_never_gives_a_bare_number_as_a_reason():
    src = """
    sim { duration: 3s dt: 1s }
    body b @cardiac { extero f : E baseline 9  extero g : E baseline 9 }
    loop seen @neural { prior: predict(3) sense: f precision: 0.9 conviction: 0.1
                        act { ignore } }
    loop unseen @neural { prior: predict(0) sense: g precision: 0.9 conviction: 0.1
                          act { move ! bolt_the_door() } }
    narrator self subscribes { seen } confabulates true
    """
    r = run_source(src)
    quotes = [e.detail["quote"] for e in r.chronicle if e.kind == "narrate"]
    assert quotes
    assert not any(q.rstrip(".").endswith(("0", "3", "9")) for q in quotes)


def test_learned_not_to_feel_pattern():
    """Precision collapses; the somatic register goes on firing."""
    src = """
    @consent("test")
    sim { duration: 12s dt: 1s }
    body b @cardiac { intero pain : P baseline 8  extero told : A baseline 0 }
    flow told @cardiac { dynamics: (9 - told) / 3s }
    loop knowing @cardiac {
      prior: predict(0) sense: pain
      precision: clamp(0.95 - 0.1 * told, 0.05, 1.0)
      conviction: 0.4 act { emit feel(pain) }
    }
    memory somatic kept { cue: pain  when: pain > 6  evoke: feel(anguish) strength: 1.0 }
    """
    r = run_source(src)
    pats = {f.pattern for f in winnow.sift(r.chronicle)}
    assert "learned not to feel" in pats


def test_perturb_accepts_several_dials():
    from soma.perturb import perturb
    src = """
    @consent("test")
    sim { duration: 20s dt: 1s }
    body b @cardiac { extero f : E baseline 0 }
    loop l @neural { prior: predict(9) sense: f precision: 0.8 conviction: 0.2
                     learn: 0.1 act { emit feel(dread) ignore } }
    """
    d = perturb(src, ["l.conviction=0.05", "l.learn=0.0"])
    assert "conviction" in d.change and "learn" in d.change


# ============================================================================
# 0.5 -- scoped, cyclic dissociation across supervision bands
# ============================================================================

def test_dissociation_can_be_scoped_to_a_modality():
    """Proprioception may detach while interoception stays online."""
    src = """
    @consent("test")
    sim { duration: 10s dt: 1s }
    body b @cardiac { intero heart : BPM baseline 70  proprio pos : P baseline 5 }
    loop feel @cardiac { prior: predict(0) sense: heart precision: 0.9
                         conviction: 0.2 act { emit feel(terror) } }
    loop locate @breath { prior: predict(0) sense: pos precision: 0.9
                          conviction: 0.2 act { emit feel(numbness) } }
    stimulus pos { at 2s: 9 }
    handle band with {
      when error(locate) > 3.0 : dissociate(proprioception) with precision -> titrate(0.1)
      after 3s : repair { reattach(proprioception) with precision -> titrate(0.3) }
    }
    """
    r = run_source(src)
    crashes = {e.detail["scope"] for e in r.chronicle if e.kind == "crash"}
    assert crashes == {"proprioception"}          # only the named band
    # interoception kept feeling; proprioception flattened to numbness
    qualia = {e.detail.get("quale", "") for e in r.chronicle if e.kind == "emit"}
    assert any("terror" in q for q in qualia)


def test_dissociation_is_a_repeatable_cycle():
    """A band that repairs can crash again if pressed again."""
    src = """
    @consent("test")
    sim { duration: 40s dt: 1s }
    body b @cardiac { intero heart : BPM baseline 70 }
    loop feel @cardiac { prior: predict(70) sense: heart precision: 0.95
                         conviction: 0.1 act { emit feel(terror) } }
    stimulus heart { at 2s: 120  at 12s: 70  at 22s: 120  at 32s: 70 }
    handle band with {
      when error(feel) > 8.0 : dissociate(interoception) with precision -> titrate(0.1)
      after 4s : repair { reattach(interoception) with precision -> titrate(0.2) }
    }
    """
    r = run_source(src)
    crashes = [e for e in r.chronicle if e.kind == "crash"]
    repairs = [e for e in r.chronicle if e.kind == "repair"]
    assert len(crashes) >= 2 and len(repairs) >= 2   # more than one cycle


def test_handler_condition_reads_a_specific_loops_error():
    src = """
    @consent("test")
    sim { duration: 6s dt: 1s }
    body b @cardiac { intero a : A baseline 0  intero c : C baseline 0 }
    loop loud  @cardiac { prior: predict(0) sense: a precision: 0.9 conviction: 0.1 act { ignore } }
    loop quiet @cardiac { prior: predict(0) sense: c precision: 0.9 conviction: 0.1 act { ignore } }
    stimulus a { at 1s: 20 }
    handle band with {
      when error(quiet) > 3.0 : dissociate(interoception) with precision -> titrate(0.1)
      after 2s : repair { reattach(interoception) with precision -> titrate(0.3) }
    }
    """
    r = run_source(src)
    # `loud` has huge error, but the band watches `quiet`, which is calm
    assert not [e for e in r.chronicle if e.kind == "crash"]


def test_interpreter_confabulates_a_labelled_reason_across_a_split():
    """The narrator explains an action from a loop it does not subscribe to."""
    src = """
    @consent("test")
    sim { duration: 4s dt: 1s }
    body b @cardiac { intero heart : BPM baseline 70  extero q : Q baseline 0 }
    loop body_loop @cardiac { prior: predict(70) sense: heart precision: 0.9
                              conviction: 0.2 act { move ! ask_for_water() } }
    loop voice @neural { prior: predict(0) sense: q precision: 0.5 conviction: 0.6
                         act { move ! say_something() } }
    stimulus heart { at 1s: 120 }
    narrator interp subscribes { voice } confabulates true
      voice { ask_for_water: "I asked for water; it was a long session." }
    """
    r = run_source(src)
    conf = [e for e in r.chronicle
            if e.kind == "narrate" and e.detail.get("about") == "ask_for_water"]
    assert conf and all(e.detail["gap"] >= 0.9 for e in conf)   # high gap = confabulation


# ============================================================================
# 0.5.1 -- example-driven language additions
# ============================================================================

def test_owned_builtin_gates_an_action():
    """A defensive response fires only for a limb that is currently owned."""
    src = """
    @consent("test")
    sim { duration: 6s dt: 1s }
    body b @cardiac { proprio felt : P baseline 0  proprio seen : P baseline 0
                      intero startle : BPM baseline 70 }
    ownership hand { predicted: felt  observed: seen  tolerance: 3  initial: owned }
    loop guard @cardiac { prior: predict(70) sense: startle precision: 0.9
                          conviction: 0.2
                          act { emit feel(terror) when owned(hand) } }
    stimulus startle { at 1s: 120 }
    stimulus seen { at 3s: 20 }
    """
    r = run_source(src)
    # owned until the seen hand leaps away at 3s; terror only while owned
    # (the ownership check runs after loops settle, so t=3 is the last owned frame)
    terrors = [e.t for e in r.chronicle if e.kind == "emit"]
    assert terrors and all(t <= 3 for t in terrors)
    assert not [e for e in r.chronicle if e.kind == "emit" and e.t > 3]


def test_love_curdling_pattern():
    from soma.perturb import perturb
    src = """
    sim { duration: 20y dt: 1y cadence: true }
    body b @breath { extero face : E baseline 5 }
    stimulus face { at 1y: 9  at 3y: 2  at 5y: 8  at 7y: 4  at 9y: 9
                    at 11y: 3  at 13y: 7  at 15y: 2  at 17y: 9  at 19y: 5 }
    loop courtship @breath {
      prior: predict(face) sense: face precision: 0.85 conviction: 0.2 learn: 0.0
      act { emit feel(delight_at_error) when perceiving
            emit feel(contempt) when acting }
    }
    """
    d = perturb(src, "courtship.learn=0.12")
    pats = {f.pattern for f in winnow.sift(d.new_result.chronicle)}
    assert "love curdling" in pats
    # and the un-hardened original does NOT curdle
    base_pats = {f.pattern for f in winnow.sift(d.base_result.chronicle)}
    assert "love curdling" not in base_pats


def test_contempt_is_a_negative_valence_quale():
    src = """
    sim { duration: 3s dt: 1s }
    body b @cardiac { extero f : E baseline 9 }
    loop l @neural { prior: predict(0) sense: f precision: 0.9 conviction: 0.1
                     act { emit feel(contempt) } }
    mood m : Affect @mood integrates { contempt * 1.0 } decay 0.9
    """
    r = run_source(src)
    assert r.mood_hist["m"][-1] < 0     # contempt pushes the mood down


def test_single_character_prose_gets_pronouns():
    from soma import prose
    src = """
    @consent("test")
    sim { duration: 4s dt: 1s }
    scene "beat" from 0s to 4s
    body Wren @cardiac { intero heart : BPM baseline 68 }
    loop alarm @cardiac { prior: predict(68) sense: heart precision: 0.9
                          conviction: 0.2 act { emit feel(terror) } }
    stimulus heart { at 1s: 120 }
    """
    r = run_source(src)
    text = prose.render(r, genders={"Wren": "he"})
    assert " he " in text or " his " in text     # not defaulting to "they"
    assert "they" not in text.lower().split("(")[0]


# ============================================================================
# 0.5.2 -- correctness fixes surfaced by audit
# ============================================================================

def test_qualia_opacity_covers_let_bindings():
    with pytest.raises(SomaTypeError):
        check(parse("let x = feel(dread)"))


def test_coupled_flows_conserve():
    """Two flows dx=-x, dy=+x must keep x+y constant: they integrate in
    lock-step, not one-then-the-other."""
    src = """
    sim { duration: 10s dt: 1s }
    body b @cardiac { intero x : X baseline 10  intero y : Y baseline 0 }
    flow x @cardiac { dynamics: -x / 5s }
    flow y @cardiac { dynamics: x / 5s }
    """
    r = run_source(src)
    totals = [a + b for a, b in zip(r.channel_hist["x"], r.channel_hist["y"])]
    assert all(abs(tot - 10.0) < 1e-6 for tot in totals)


def test_dissociated_channel_is_ignored_not_acted():
    """A detached interoceptive channel carries no usable evidence; a loop must
    not act on the strength of a signal attenuated to the floor."""
    src = """
    @consent("test")
    sim { duration: 6s dt: 1s }
    body b @cardiac { intero heart : BPM baseline 70 }
    loop feel @cardiac { prior: predict(70) sense: heart precision: 0.95
      conviction: 0.1 act { move ! set(heart, 999) } }
    stimulus heart { at 1s: 200 }
    handle band with {
      when error(feel) > 8.0 : dissociate(interoception) with precision -> titrate(0.05)
      after 100s : repair { reattach(interoception) with precision -> titrate(0.1) }
    }
    """
    r = run_source(src)
    # once dissociated, the loop must route to ignore and drive nothing
    diss_settles = [e for e in r.chronicle
                    if e.kind == "settle" and e.detail["pi_s"] <= 0.05]
    assert diss_settles and all(e.detail["route"] == "ignore" for e in diss_settles)
    # the loop drives at t=1 (before the crash), but never once dissociated
    first_diss = min(e.t for e in diss_settles)
    assert not [e for e in r.chronicle
                if e.kind == "drive" and e.t >= first_diss]


def test_lag_phrase_reads_one_second_correctly():
    """A one-second (one-frame) coupling lag reads as 'a second late', not
    'a half-second late' -- the boundary bug the tutorial audit found."""
    from soma.prose import _lag_phrase
    assert _lag_phrase(0) == "almost at once"
    assert _lag_phrase(0.5) == "a half-second late"
    assert _lag_phrase(1) == "a second late"
    assert _lag_phrase(2) == "2 seconds late"
    assert _lag_phrase(60) == "a minute late"
    assert _lag_phrase(86400) == "a day late"


def test_dashboard_never_exceeds_requested_width():
    """Every non-trace panel line must fit the configured width, at desktop and
    mobile sizes -- the invariant that keeps the browser output from needing
    horizontal scroll on a phone."""
    import soma.viz as viz
    for width in (44, 52, 72, 92):
        viz.configure(color=False, unicode=True, width=width)
        for name in ("the_dinner_party", "the_appointment", "trauma", "workspace"):
            res = _run(name)
            findings = winnow.sift(res.chronicle)
            from soma import query as qmod
            qr = qmod.run_all(res.program, res.chronicle)
            report = viz.render_report(res, findings=findings, trace_rows=6,
                                       qresults=qr)
            in_trace = False
            for ln in report.splitlines():
                if "CHRONICLE" in ln:
                    in_trace = True          # the trace is intentionally wide
                if not in_trace:
                    assert len(ln) <= width, (
                        f"{name} at width {width}: line {len(ln)} > {width}: {ln!r}")
    viz.configure(color=True, unicode=True, width=None)


def test_coupling_lag_renders_readably():
    """A coupling lag is shown in human units (days/seconds), not raw seconds."""
    import soma.viz as viz
    viz.configure(color=False, unicode=True, width=88)
    res = _run("the_appointment")           # a lineage-scale couple, lag in days
    social = viz.render_social(res)
    assert "2592000" not in social          # not raw seconds
    assert "lag" in social and ("d," in social or "s," in social)
    viz.configure(color=True, unicode=True, width=None)


if __name__ == "__main__":
    # standalone runner (no pytest needed)
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        try:
            fn(); passed += 1; print(f"  ok   {fn.__name__}")
        except Exception as e:
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{passed}/{len(fns)} passed")


def test_overwhelm_breaks_a_defended_belief():
    """A high-conviction loop suppresses disconfirming evidence (self-deception),
    but when it declares `overwhelm`, the accumulated raw surprise eventually
    forces it to perceive -- a mechanistic self-revelation. Without `overwhelm`
    the same belief never yields (backward-compatible default)."""
    src = """
    @consent("a defended belief and its breaking point")
    sim {{ duration: 12s  dt: 1s }}
    body M @cardiac {{ extero worth : Signal baseline 0 }}
    loop belief @cardiac {{
      prior:      predict(0)
      sense:      worth
      precision:  0.35
      conviction: 0.85
      {ov}
      act {{ emit feel(dread) when worth < 3 }}
    }}
    stimulus worth {{ at 3s: 8  at 6s: 9  at 9s: 9 }}
    """
    from soma import parse
    from soma.interpreter import Interpreter
    # with overwhelm: the belief breaks (at least one revelation, some perceive)
    r = Interpreter(parse(src.format(ov="overwhelm: 20"))).run()
    revs = [e for e in r.chronicle if e.kind == "revelation"]
    routes = [e.detail.get("route") for e in r.chronicle
              if e.kind == "settle" and e.who == "belief"]
    assert revs, "a breakable belief should reveal under overwhelming evidence"
    assert "perceive" in routes, "the broken belief should perceive"
    # without overwhelm: the belief suppresses forever (never perceives the shock)
    r2 = Interpreter(parse(src.format(ov=""))).run()
    assert not any(e.kind == "revelation" for e in r2.chronicle)
    late = [e.detail.get("route") for e in r2.chronicle
            if e.kind == "settle" and e.who == "belief" and e.t >= 3]
    assert late and all(rt == "act" for rt in late), \
        "without overwhelm, high conviction must keep suppressing the evidence"


def test_overwhelm_auto_scales_with_conviction():
    """`overwhelm: auto` derives the breaking point from the belief's own strengths:
    the same evidence breaks a softly-held belief and is resisted by a hard-held one,
    with no author-set threshold."""
    from soma import parse
    from soma.interpreter import Interpreter

    def first_break(conv):
        src = f"""
        @consent("auto overwhelm")
        sim {{ duration: 18s  dt: 1s }}
        body M @cardiac {{ extero worth : Signal baseline 0 }}
        loop belief @cardiac {{
          prior: predict(0)
          sense: worth
          precision: 0.35
          conviction: {conv}
          learn: 0.03
          overwhelm: auto
          act {{ emit feel(dread) when worth < 3 }}
        }}
        stimulus worth {{ at 3s: 7  at 6s: 8  at 9s: 8  at 12s: 9  at 15s: 9 }}
        """
        r = Interpreter(parse(src)).run()
        revs = [e.t for e in r.chronicle if e.kind == "revelation"]
        return revs[0] if revs else None

    soft, hard = first_break(0.6), first_break(1.4)
    assert soft is not None and hard is not None
    assert hard >= soft, "a harder-held belief must resist at least as long"
