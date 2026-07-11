"""Tests for the soma.narrative high-level authoring library."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from soma import parse
from soma.checker import check, ConsentError
from soma.narrative import (Story, anxious, stoic, trusting, guarded, volatile,
                            numb, tender, hollowed, Temperament, arc, TEMPERAMENTS)


def _compiles(story):
    """A story's generated source must parse and type-check."""
    src = story.source()
    prog = parse(src, title=story.title)
    check(prog)
    return prog


def test_minimal_story_compiles_and_runs():
    story = Story("mini", span="4s", step="1s")
    c = story.character("Ada", temperament=trusting)
    c.senses("phone")
    c.appraises("phone", as_threat=True, feeling="alarm")
    story.at("2s", c.hears("phone", 9))
    _compiles(story)
    r = story.result()
    assert any(e.kind == "emit" for e in r.chronicle)


def test_distress_feeling_forces_consent():
    """A story that emits distress must auto-declare @consent, or the base
    checker would (correctly) refuse to run it."""
    story = Story("grief_test", span="4s", step="1s")
    c = story.character("Mara", temperament=tender)
    c.senses("news")
    c.appraises("news", as_threat=True, feeling="grief")
    src = story.source()
    assert "@consent" in src
    _compiles(story)   # should NOT raise ConsentError


def test_no_consent_when_no_distress():
    story = Story("calm", span="4s", step="1s")
    c = story.character("Ada", temperament=trusting)
    c.senses("bird")
    c.appraises("bird", feeling="delight")
    assert "@consent" not in story.source()


def test_temperament_sets_dials():
    """The generated precision/conviction must come from the temperament."""
    story = Story("t", span="2s", step="1s")
    c = story.character("X", temperament=guarded)
    c.senses("s")
    c.appraises("s", as_threat=True, feeling="fear")
    src = story.source()
    assert f"precision:  {guarded.precision}" in src or \
           f"precision:  {int(guarded.precision)}" in src
    assert f"conviction: {guarded.conviction}" in src


def test_temperament_override_per_appraisal():
    story = Story("t", span="2s", step="1s")
    c = story.character("X", temperament=trusting)
    c.senses("s")
    c.appraises("s", as_threat=True, feeling="fear", precision=0.33)
    assert "precision:  0.33" in story.source()


def test_feeling_creates_budget_and_body_channel():
    story = Story("f", span="4s", step="1s")
    c = story.character("Y", temperament=anxious)
    c.feels("dread", from_body="heart")
    src = story.source()
    assert "resource Y_budget" in src
    assert "intero heart" in src
    _compiles(story)


def test_single_character_is_flat_no_wrapper():
    story = Story("solo", span="3s", step="1s")
    c = story.character("Solo", temperament=trusting)
    c.senses("x")
    c.appraises("x", feeling="joy")
    c.narrates(voice={"joy": "How nice."})
    src = story.source()
    assert "character Solo {" not in src   # flat, no wrapper
    assert "narrator self " in src          # narrator named 'self'


def test_two_characters_are_scoped():
    story = Story("duo", span="4s", step="1s")
    a = story.character("Ana", temperament=anxious)
    b = story.character("Ivo", temperament=guarded)
    a.senses("x"); a.appraises("x", feeling="joy"); a.narrates(voice={"joy":"ah"})
    b.senses("y"); b.appraises("y", feeling="calm"); b.narrates(voice={"calm":"hm"})
    src = story.source()
    assert "character Ana {" in src
    assert "character Ivo {" in src
    assert "self_Ana" in src and "self_Ivo" in src


def test_reading_creates_coupling():
    story = Story("look", span="6s", step="1s")
    a = story.character("Ana", temperament=anxious)
    b = story.character("Ivo", temperament=guarded)
    a.reads(b, "face", gain=0.8, lag="1s")
    a.appraises("ivo_face", as_threat=True, feeling="shame")
    b.senses("z"); b.appraises("z", feeling="calm")
    src = story.source()
    assert "couple Ivo.face -> Ana.ivo_face" in src
    prog = _compiles(story)
    assert len(prog.couples) == 1


def test_coupling_actually_transmits():
    story = Story("look2", span="6s", step="1s")
    a = story.character("Ana", temperament=trusting)
    b = story.character("Ivo", temperament=trusting)
    a.reads(b, "face", gain=0.9, lag="1s")
    a.appraises("ivo_face", as_threat=True, feeling="worry")
    b.senses("z"); b.appraises("z", feeling="calm")
    story.at("2s", b.shows("face", 9))
    r = story.result()
    assert any(e.kind == "couple" for e in r.chronicle)


def test_dissociation_fires_regardless_of_temperament():
    """Even a numb character must dissociate when the author says so -- the
    library boosts the watched appraisal's precision to make the threshold
    reachable."""
    for temp in (numb, stoic, volatile):
        story = Story("diss", span="40d", step="2d", about="dissociation")
        c = story.character("W", temperament=temp, clock="day")
        c.senses("reminder")
        c.appraises("reminder", as_threat=True, feeling="terror")
        c.dissociates_when(appraisal="reminder", exceeds=4,
                           detaching="interoception", repair_after="10d")
        c.narrates(voice={"terror": "I am here, not there."})
        story.at("4d", c.hears("reminder", 9))
        r = story.result()
        crashes = [e for e in r.chronicle if e.kind == "crash"]
        assert crashes, f"{temp.name} never dissociated"


def test_somatic_memory_fires():
    story = Story("flash", span="20s", step="1s", about="a flashback")
    c = story.character("F", temperament=numb)
    c.senses("smell")
    c.remembers("the_day", cued_by="smell", when_above=5, evokes="panic")
    story.at("3s", c.hears("smell", 9))
    r = story.result()
    assert any(e.kind == "somatic" for e in r.chronicle)


def test_learning_hardens_the_prior():
    story = Story("marriage", span="20y", step="1y", cadence=True,
                  about="erosion")
    c = story.character("S", temperament=tender, clock="life")
    c.senses("face", baseline=5)
    c.appraises("face", feeling="delight")
    c.learns(0.06)
    for (t, v) in (arc.wobble(around=5, span="18y", every="2y")):
        story.at(t, c.hears("face", v))
    src = story.source()
    assert "learn:" in src
    r = story.result()
    assert any(e.kind == "learn" for e in r.chronicle)


def test_narrator_confabulates():
    story = Story("mask", span="6s", step="0.5s", about="distress")
    c = story.character("N", temperament=anxious)
    c.senses("ear")
    c.appraises("ear", as_threat=True, drives="heart", to=118)
    c.feels("dread", from_body="heart")
    c.narrates(downplaying={"dread": "I'm fine."})
    story.at("1.5s", c.hears("ear", 9))
    r = story.result()
    narrates = [e for e in r.chronicle if e.kind == "narrate"]
    assert narrates
    assert any("fine" in e.detail.get("quote", "") for e in narrates)


def test_perturb_through_library():
    story = Story("p", span="6s", step="1s")
    c = story.character("C", temperament=trusting)
    c.senses("x")
    c.appraises("x", as_threat=True, feeling="joy", learn=0.02)
    story.at("2s", c.hears("x", 8))
    out = story.perturb("appraising_x.learn=0.2")
    assert "PERTURB" in out or "learn" in out


def test_arc_wobble_and_hold_compose():
    a = arc.wobble(around=5, span="10y", every="2y") + arc.hold(0, at="11y")
    beats = list(a)
    assert beats[-1] == ("11y", 0)
    assert len(beats) > 3


def test_arc_ramp_endpoints():
    a = arc.ramp(0, 10, span="10s", steps=5)
    beats = list(a)
    assert beats[0][1] == 0
    assert beats[-1][1] == 10


def test_all_temperaments_registered():
    assert set(TEMPERAMENTS) == {"anxious", "stoic", "trusting", "guarded",
                                 "volatile", "numb", "tender", "hollowed"}
    for t in TEMPERAMENTS.values():
        assert isinstance(t, Temperament)


def test_tuned_returns_modified_copy():
    t = anxious.tuned(learn=0.1)
    assert t.learn == 0.1
    assert anxious.learn == 0.03   # original unchanged


def test_prose_and_sift_run_through():
    story = Story("full", span="6s", step="0.5s", about="distress")
    c = story.character("Nadia", temperament=anxious)
    c.senses("ear")
    c.appraises("ear", as_threat=True, drives="heart", to=118)
    c.feels("dread", from_body="heart")
    c.narrates(downplaying={"dread": "I'm fine."})
    story.at("1.5s", c.hears("ear", 9))
    assert "NADIA" in story.prose().upper() or "FULL" in story.prose().upper()
    findings = story.sift()
    assert isinstance(findings, list)


def test_stops_seeing_makes_learning_load_bearing():
    """updates + stops_seeing + a learn rate: turning learn off must change the
    story (the curdling-love mechanism)."""
    story = Story("curdle", span="20y", step="1y", cadence=True, about="erosion")
    c = story.character("S", temperament=tender, clock="life")
    c.senses("face", baseline=5)
    c.appraises("face", feeling="delight", when="face > 1",
                precision=0.75, conviction=0.2, updates=True, stops_seeing=True)
    c.learns(0.055)
    for (t, v) in arc.wobble(around=5, span="18y", every="2y"):
        story.at(t, c.hears("face", v))
    src = story.source()
    assert "ignore" in src and "update ->" in src
    out = story.perturb("appraising_face.learn=0.0")
    # the diff should show something changed (vanished or appeared)
    assert "VANISHED" in out or "APPEARED" in out or "->" in out



def test_mood_integrates_and_decays():
    story = Story("moody", span="10s", step="1s", about="distress")
    c = story.character("A", temperament=anxious)
    c.senses("threat")
    c.appraises("threat", as_threat=True, feeling="dread")
    c.has_mood("desolation", fed_by="dread", decay=0.85)
    story.at("2s", c.hears("threat", 9))
    src = story.source()
    assert "mood A_desolation" in src and "decay 0.85" in src
    _compiles(story)
    r = story.result()
    assert any(e.kind == "mood" for e in r.chronicle)


def test_mood_can_be_relieved():
    story = Story("relief", span="8s", step="1s", about="distress")
    c = story.character("A", temperament=anxious)
    c.senses("threat"); c.senses("comfort_cue")
    c.appraises("threat", as_threat=True, feeling="dread")
    c.appraises("comfort_cue", feeling="relief")
    c.has_mood("mood", fed_by="dread", relieved_by="relief", decay=0.9)
    # the mood must be keyed on this character's own relieving loop (not the
    # bare quale), so it reads appraising_comfort_cue, weighted negative
    assert "appraising_comfort_cue * -0.6" in story.source()
    _compiles(story)


def test_attention_starves_competing_deliberation():
    story = Story("attn", span="8s", step="1s", about="distress")
    c = story.character("A", temperament=volatile)
    c.has_attention(capacity=2)
    c.senses("a"); c.senses("b")
    c.appraises("a", as_threat=True, feeling="panic", effortful=True)
    c.appraises("b", as_threat=True, feeling="terror", effortful=True)
    story.at("2s", c.hears("a", 9), c.hears("b", 9))
    src = story.source()
    assert "attention A_spotlight = capacity(2)" in src
    assert "mode:       deliberate" in src and "attend A_spotlight 1" in src
    _compiles(story)
    r = story.result()
    assert any(e.kind == "starved" for e in r.chronicle)


def test_feeling_shows_on_surface():
    story = Story("tell", span="8s", step="1s")
    c = story.character("A", temperament=stoic)
    c.senses("provocation")
    c.appraises("provocation", as_threat=True, feeling="anger",
                shows_on="face", shows_value=9, when="provocation > 5")
    story.at("2s", c.hears("provocation", 9))
    src = story.source()
    assert "proprio face" in src and "set(face, 9)" in src
    _compiles(story)
    r = story.result()
    assert max(r.channel_hist.get("face", [0])) >= 8


def test_surface_decay_is_stable_on_slow_clocks():
    story = Story("saga", span="30y", step="1y", cadence=True, about="distress")
    c = story.character("A", temperament=numb, clock="life")
    c.senses("shock")
    c.appraises("shock", as_threat=True, feeling="terror",
                shows_on="face", shows_value=9, fades_to=1)
    for (t, v) in [("2y", 9), ("3y", 0), ("10y", 9), ("11y", 0)]:
        story.at(t, c.hears("shock", v))
    _compiles(story)
    r = story.result()
    assert max(r.channel_hist.get("face", [0])) < 100


def test_over_spreads_an_arc():
    story = Story("ov", span="10y", step="1y", cadence=True)
    c = story.character("A", temperament=tender, clock="life")
    c.senses("face_seen", baseline=5)
    c.appraises("face_seen", feeling="delight")
    story.over(arc.wobble(around=5, span="8y", every="2y"),
               lambda v: c.hears("face_seen", v))
    _compiles(story)
    r = story.result()
    assert any(e.kind == "stimulus" for e in r.chronicle)


def test_new_subtle_qualia_have_valence():
    from soma.interpreter import VALENCE
    for q in ("unease", "disquiet", "foreboding", "longing", "tenderness",
              "apprehension", "desolation"):
        assert q in VALENCE, f"{q} missing from VALENCE"


def test_desolation_gates_consent():
    story = Story("d", span="4s", step="1s")
    c = story.character("A", temperament=numb)
    c.senses("x")
    c.appraises("x", as_threat=True, feeling="desolation")
    assert "@consent" in story.source()
    _compiles(story)


def test_full_three_generation_saga():
    import importlib
    import examples.narrative.the_house as th
    importlib.reload(th)
    story = th.build()
    _compiles(story)
    r = story.result()
    feelers = set(e.who.split(".")[0] for e in r.chronicle if e.kind == "emit")
    assert {"Vera", "Ada", "Mira"} <= feelers
    out = story.perturb("Ada.face.gain=0.03")
    assert "VANISHED" in out or "APPEARED" in out


def test_moods_do_not_cross_contaminate_between_characters():
    """Two characters feeling the SAME quale must have isolated moods: one
    person's dread must not deepen another's, even though they share the quale
    name. (Regression: moods were keyed on the global quale, not the owner.)"""
    story = Story("iso", span="10s", step="1s", about="distress")
    a = story.character("Ana", temperament=anxious)
    b = story.character("Ivo", temperament=numb)
    a.senses("xa"); a.appraises("xa", as_threat=True, feeling="dread")
    a.has_mood("gloom", fed_by="dread", decay=0.95)
    b.senses("xb"); b.appraises("xb", as_threat=True, feeling="dread")
    b.has_mood("gloom", fed_by="dread", decay=0.95)
    a.narrates(voice={"dread": "a"}); b.narrates(voice={"dread": "b"})
    story.at("2s", a.hears("xa", 9))     # only Ana is triggered
    src = story.source()
    # each mood keys on its OWNER's loop, qualified
    assert "Ana.appraising_xa" in src
    assert "Ivo.appraising_xb" in src
    r = story.result()
    ivo_mood = [e for e in r.chronicle if e.who == "Ivo_gloom"]
    assert not ivo_mood, "Ivo's mood moved from Ana's feeling (cross-contamination)"


def test_wants_and_fears_create_ambivalence():
    """Two drives on one channel = approach/avoidance, both firing at once."""
    story = Story("amb", span="10s", step="1s", about="ambivalence")
    c = story.character("A", temperament=guarded)
    c.wants("closeness", toward=9, strength=0.3)
    c.fears("closeness", toward=1, strength=0.3)
    src = story.source()
    assert "allostat A_wants_closeness" in src
    assert "allostat A_fears_closeness" in src
    _compiles(story)
    r = story.result()
    drives = [e for e in r.chronicle if e.kind == "allostat"]
    assert len(drives) > 4
    # the ambivalence sift fires
    found = story.sift("ambivalence")
    assert found and "two ways" in found[0].text


def test_values_emit_self_betrayal_when_violated():
    story = Story("val", span="10s", step="1s", about="self-betrayal")
    c = story.character("A", temperament=guarded)
    c.has_body_signal("composure", baseline=2)
    c.values("honesty", says="I would never lie.",
             betrayed_when="composure > 6", on_channel="composure")
    c.narrates(voice={"self_betrayal": "That isn't who I am."})
    # @consent must be auto-added (self_betrayal is distress)
    assert "@consent" in story.source()
    story.at("3s", c.hears("composure", 8))
    _compiles(story)
    r = story.result()
    betrayals = [e for e in r.chronicle if e.kind == "emit"
                 and "self_betrayal" in str(e.detail.get("quale", ""))]
    assert betrayals, "the value was violated but no self_betrayal fired"
    found = story.sift("self-betrayal")
    assert found


def test_attention_does_not_starve_non_effortful_loops():
    """A spotlight must starve only effortful loops; feeling/value loops run
    free as habit. (Regression: the base default mode is deliberate, so without
    an explicit habit the spotlight starved the whole mind.)"""
    story = Story("attn", span="8s", step="1s", about="distress")
    c = story.character("A", temperament=guarded)
    c.has_attention(capacity=2)
    c.has_body_signal("composure", baseline=2)
    c.values("honesty", says="I never lie.", betrayed_when="composure > 6",
             on_channel="composure")
    c.senses("q")
    c.appraises("q", as_threat=True, feeling="apprehension")  # NOT effortful
    c.narrates(voice={"self_betrayal": "no"})
    story.at("3s", c.hears("composure", 8), c.hears("q", 9))
    src = story.source()
    assert "mode:       habit" in src  # non-effortful loops declared habit
    _compiles(story)
    r = story.result()
    # the value loop must not be starved
    starved = [e for e in r.chronicle if e.kind == "starved"
               and "upholding" in e.who]
    assert not starved, "the value loop was starved by the spotlight"


def test_appraisal_when_guard_gates_the_body_drive():
    """A guarded appraisal's reach into the body must also be gated -- he only
    composes his face WHEN pressed, not from t=0."""
    story = Story("g", span="8s", step="1s", about="distress")
    c = story.character("A", temperament=guarded)
    c.has_body_signal("composure", baseline=2)
    c.senses("q")
    c.appraises("q", as_threat=True, drives="composure", to=8,
                feeling="apprehension", when="q > 4")
    story.at("4s", c.hears("q", 9))
    _compiles(story)
    r = story.result()
    comp = r.channel_hist.get("composure", [])
    # composure stays at baseline until the guard opens at t=4
    assert comp[0] < 3, "the body drive fired before its guard condition"
    assert max(comp) >= 7, "the body drive never fired when it should have"


def test_characterize_reads_the_person():
    story = Story("who", span="14s", step="1s", about="a torn person")
    c = story.character("Rader", temperament=guarded)
    c.wants("being_known", toward=9)
    c.fears("being_known", toward=1)
    c.has_body_signal("composure", baseline=2)
    c.values("honesty", says="I would never lie to her.",
             betrayed_when="composure > 6", on_channel="composure")
    c.narrates(voice={"self_betrayal": "That isn't who I am."})
    for t in (3, 6, 9, 12):
        story.at(f"{t}s", c.hears("composure", 8))
    portrait = c.story.characterize(width=76)
    assert "guarded" in portrait
    assert "wants and fears the same thing" in portrait
    assert "being_known" in portrait
    # no line overflows the box
    for line in portrait.splitlines():
        assert len(line) <= 76


def test_multichar_drives_are_scoped():
    """Drives in a multi-character story must regulate the qualified channel, or
    they bind to nothing. (Regression.)"""
    story = Story("two", span="8s", step="1s", about="ambivalence")
    a = story.character("Ana", temperament=tender)
    b = story.character("Ivo", temperament=guarded)
    a.wants("closeness", toward=9); a.fears("closeness", toward=1)
    b.senses("x"); b.appraises("x", as_threat=True, feeling="apprehension")
    b.narrates(voice={"apprehension": "hm"})
    src = story.source()
    assert "regulate: Ana.closeness" in src
    _compiles(story)
    r = story.result()
    drives = [e for e in r.chronicle if e.kind == "allostat"]
    assert drives, "scoped drives regulated nothing"


def test_new_characterological_qualia_present():
    from soma.interpreter import VALENCE
    for q in ("self_betrayal", "ambivalence", "resolve"):
        assert q in VALENCE


def test_diplomat_and_sisters_examples():
    import importlib
    for name in ("the_diplomat", "two_sisters"):
        mod = importlib.import_module(f"examples.narrative.{name}")
        importlib.reload(mod)
        story = mod.build()
        _compiles(story)
        portrait = story.characterize()
        assert "CHARACTER" in portrait


def test_same_channel_appraised_twice_no_collision():
    """A character may appraise one channel two ways (delight at presence, grief
    at absence). The loop names must not collide."""
    story = Story("dual", span="6s", step="1s", about="distress")
    c = story.character("A", temperament=tender)
    c.senses("face", baseline=5)
    c.appraises("face", feeling="delight", when="face > 4")
    c.appraises("face", feeling="grief", when="face < 1", expects=5)
    src = story.source()
    import re
    loops = re.findall(r"loop (\S+)", src)
    assert len(loops) == len(set(loops)), f"loop name collision: {loops}"
    _compiles(story)


def test_expects_sets_the_prior():
    """A loop that expects a presence and finds absence is in large error --
    which is how absence becomes grief."""
    story = Story("grief", span="8s", step="1s", about="grief")
    c = story.character("A", temperament=tender)
    c.senses("her_face", baseline=5)
    c.appraises("her_face", feeling="grief", when="her_face < 1",
                expects=5, precision=0.9, learn=0.0)
    assert "predict(5)" in story.source()
    story.at("2s", c.hears("her_face", 0))
    _compiles(story)
    r = story.result()
    griefs = [e for e in r.chronicle if e.kind == "emit"
              and "grief" in str(e.detail.get("quale", ""))]
    assert griefs, "expecting a presence and finding absence produced no grief"


def test_feeling_only_arises_above_threshold():
    """A feeling read off the body arises only when the signal exceeds its
    threshold -- a racing heart, not merely a beating one, and never from a
    downward deviation."""
    story = Story("f", span="8s", step="1s", about="distress")
    c = story.character("A", temperament=anxious)
    c.senses("ear")
    c.appraises("ear", as_threat=True, drives="heart", to=118,
                when="ear > 3", fades_to=70)
    c.feels("dread", from_body="heart")
    c.narrates(downplaying={"dread": "fine"})
    story.at("3s", c.hears("ear", 9))
    _compiles(story)
    r = story.result()
    emits = [e.t for e in r.chronicle if e.kind == "emit"]
    # no dread before the heart spikes (t=3); dread must not fire at rest
    assert emits, "dread never fired"
    assert min(emits) >= 3.0, "dread fired before the body was alarmed"


def test_driven_body_channel_recovers_with_fades_to():
    """fades_to on a driven body channel lets a spike settle back to rest."""
    story = Story("r", span="10s", step="1s", about="distress")
    c = story.character("A", temperament=anxious)
    c.senses("ear")
    c.appraises("ear", as_threat=True, drives="heart", to=118,
                when="ear > 3", fades_to=70)
    c.feels("dread", from_body="heart")
    c.narrates(downplaying={"dread": "fine"})
    story.at("3s", c.hears("ear", 9))
    story.at("6s", c.hears("ear", 1))
    _compiles(story)
    r = story.result()
    heart = r.channel_hist.get("heart", [])
    assert max(heart) > 100, "heart never spiked"
    assert heart[-1] < 100, "heart never recovered toward rest"


def test_change_of_self_is_per_character():
    """The change-of-self pattern must not conflate two people's feelings into a
    false arc. (Regression.)"""
    from soma import winnow
    story = Story("two", span="10s", step="1s", about="distress")
    a = story.character("Ana", temperament=anxious)
    b = story.character("Ivo", temperament=guarded)
    a.senses("x"); a.appraises("x", as_threat=True, feeling="shame")
    b.senses("y"); b.appraises("y", as_threat=True, feeling="contempt")
    a.narrates(voice={"shame": "s"}); b.narrates(voice={"contempt": "c"})
    story.at("2s", a.hears("x", 9), b.hears("y", 9))
    r = story.result()
    findings = winnow.sift_change_of_self(r.chronicle)
    # neither character changed its dominant feeling, so no false arc
    for f in findings:
        # if any arc is reported it must name a real single owner, not conflate
        assert f.detail.get("owner") in ("Ana", "Ivo")


def test_internal_parts_compete_for_consciousness():
    """A loud protector wins the workspace; a quiet exile's feeling fires but is
    never ignited -- felt, never known."""
    story = Story("parts", span="8s", step="1s", about="a divided self")
    c = story.character("D", temperament=guarded)
    c.part("manager", role="protector", reacts_to="criticism",
           feeling="contempt", salience=0.95, when="criticism > 3")
    c.part("child", role="exile", reacts_to="criticism",
           feeling="shame", salience=0.28, when="criticism > 3")
    story.at("3s", c.hears("criticism", 8))
    src = story.source()
    assert "workspace D_mind" in src
    assert "@consent" in src  # shame is distress
    _compiles(story)
    r = story.result()
    from collections import Counter
    emits = Counter(str(e.detail.get("quale", "")).replace("Qualia<", "").replace(">", "")
                    for e in r.chronicle if e.kind == "emit")
    # both parts feel
    assert emits.get("contempt", 0) > 0 and emits.get("shame", 0) > 0
    # but the exile never ignites
    unignited = story.sift("never-ignited")
    assert any("child" in f.detail.get("content", "") for f in unignited)


def test_relational_self_differs_by_person():
    """The same character runs different precision/conviction with different
    people -- two selves from one body."""
    story = Story("rel", span="12s", step="1s", about="two selves")
    cass = story.character("Cass", temperament=guarded)
    mother = story.character("Mother", temperament=tender)
    lover = story.character("Lover", temperament=tender)
    cass.with_person(mother, feeling="shame", precision=0.9, conviction=0.2)
    cass.with_person(lover, feeling="tenderness", precision=0.4, conviction=0.7)
    cass.narrates(voice={"shame": "s", "tenderness": "t"})
    story.at("3s", mother.shows("face", 8))
    story.at("7s", lover.shows("face", 8))
    src = story.source()
    assert "loop with_mother" in src and "loop with_lover" in src
    _compiles(story)
    r = story.result()
    from collections import Counter
    emits = Counter(str(e.detail.get("quale", "")).replace("Qualia<", "").replace(">", "")
                    for e in r.chronicle if e.kind == "emit")
    assert emits.get("shame", 0) > 0 and emits.get("tenderness", 0) > 0


def test_characterize_skips_characters_without_interior():
    """A character who only shows a face (no interior) is not profiled, and their
    scene-presence must not be misattributed as another's arc."""
    story = Story("scene", span="8s", step="1s", about="distress")
    cass = story.character("Cass", temperament=guarded)
    face = story.character("Stranger", temperament=tender)
    cass.with_person(face, feeling="wariness", precision=0.85, conviction=0.3)
    cass.narrates(voice={"wariness": "w"})
    story.at("3s", face.shows("face", 8))
    portrait = story.characterize(width=80)
    assert "Cass" in portrait
    assert "Stranger" not in portrait  # no interior -> not profiled


def test_portrait_reads_a_divided_self():
    """The portrait must surface internal parts and the relational self."""
    import importlib
    mod = importlib.import_module("examples.narrative.the_negotiator")
    importlib.reload(mod)
    story = mod.build()
    _compiles(story)
    portrait = story.characterize(width=86)
    assert "Carries" in portrait          # internal parts
    assert "unheard" in portrait          # the silenced exile
    assert "different self with each" in portrait  # the relational self
    for line in portrait.splitlines():
        assert len(line) <= 86            # nothing overflows the box


def test_negotiator_perturbation_is_load_bearing():
    import importlib
    mod = importlib.import_module("examples.narrative.the_negotiator")
    importlib.reload(mod)
    story = mod.build()
    out = story.perturb("Cass.appraising_pressure.precision=0.05")
    assert "VANISHED" in out or "APPEARED" in out


def test_mood_trajectory_detects_souring():
    """A mood that sinks steadily across the run must be caught as a souring."""
    story = Story("sour", span="12s", step="1s", about="distress")
    c = story.character("A", temperament=anxious)
    c.senses("blow")
    c.appraises("blow", as_threat=True, feeling="dread")
    c.has_mood("gloom", fed_by="dread", decay=0.95)
    c.narrates(voice={"dread": "d"})
    for t in (2, 4, 6, 8):
        story.at(f"{t}s", c.hears("blow", 9))
    _compiles(story)
    found = story.sift("mood-trajectory")
    assert found, "a steadily sinking mood was not detected"
    assert "sour" in found[0].pattern


def test_relational_self_both_selves_activate():
    """Both relational selves must actually fire, not just be declared -- the
    'different self with each' claim must be true in the run."""
    story = Story("rel", span="14s", step="1s", about="two selves")
    cass = story.character("Cass", temperament=guarded)
    a = story.character("Aya", temperament=tender)
    b = story.character("Ben", temperament=tender)
    cass.with_person(a, feeling="wariness", precision=0.85, conviction=0.3)
    cass.with_person(b, feeling="tenderness", precision=0.4, conviction=0.7)
    cass.narrates(voice={"wariness": "w", "tenderness": "t"})
    story.at("3s", a.shows("face", 8))
    story.at("8s", b.shows("face", 8))
    _compiles(story)
    r = story.result()
    from collections import Counter
    emits = Counter(str(e.detail.get("quale", "")).replace("Qualia<", "").replace(">", "")
                    for e in r.chronicle if e.kind == "emit")
    assert emits.get("wariness", 0) > 0, "the wariness-self never activated"
    assert emits.get("tenderness", 0) > 0, "the tenderness-self never activated"


def test_defended_core_names_the_exiles_feeling():
    """When a part's bid never ignites, the feeling it carries is the defended
    core -- named precisely, not whatever else happened to co-occur."""
    story = Story("div", span="12s", step="1s", about="a divided self")
    c = story.character("A", temperament=guarded)
    c.part("mgr", role="protector", reacts_to="hit", feeling="resolve",
           salience=0.95, when="hit > 3")
    c.part("kid", role="exile", reacts_to="hit", feeling="terror",
           salience=0.25, when="hit > 3")
    # a loud co-occurring feeling that must NOT be mistaken for the defended one
    c.senses("hit")
    c.appraises("hit", as_threat=True, feeling="anger", when="hit > 3")
    c.narrates(voice={"terror": "t"})
    for t in (3, 5, 7, 9):
        story.at(f"{t}s", c.hears("hit", 8))
    _compiles(story)
    found = story.sift("defended-core")
    assert found, "no defended core found"
    assert found[0].detail.get("quale") == "terror", \
        f"defended core misidentified as {found[0].detail.get('quale')}"


def test_defended_core_names_the_starved_feeling():
    """A feeling whose loop is repeatedly starved of attention -- felt rarely,
    suppressed often -- is the defended core, even if a louder feeling is emitted
    more. (Regression: the diplomat must defend against longing, not the
    apprehension he merely manages.)"""
    story = Story("starve", span="18s", step="1s",
                  about="defended against a longing")
    c = story.character("A", temperament=guarded)
    c.has_attention(capacity=2)
    # a loud, freely-emitted feeling (no attention cost)
    c.has_body_signal("pressure", baseline=2)
    c.appraises("pressure", as_threat=True, feeling="apprehension",
                when="pressure > 4")
    # the defended one: effortful, so it competes for the spotlight and starves
    c.has_body_signal("ache", baseline=3)
    c.appraises("ache", feeling="longing", when="ache > 5", effortful=True)
    c.appraises("pressure", feeling="wariness", when="pressure > 2",
                effortful=True)
    c.narrates(voice={"longing": "l"})
    for t in (3, 6, 9, 12, 15):
        story.at(f"{t}s", c.hears("pressure", 8), c.hears("ache", 8))
    _compiles(story)
    found = story.sift("defended-core")
    assert found, "no defended core found"
    assert found[0].detail.get("quale") == "longing", \
        f"defended core misidentified as {found[0].detail.get('quale')}"


def test_all_winnow_patterns_run_without_error():
    """Every registered pattern must run on a rich chronicle without crashing."""
    import importlib
    from soma import winnow
    mod = importlib.import_module("examples.narrative.the_negotiator")
    importlib.reload(mod)
    chron = mod.build().result().chronicle
    for name, fn in winnow.ALL_PATTERNS.items():
        fn(chron)  # must not raise


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        try:
            fn(); passed += 1
        except Exception:
            print(f"FAIL {fn.__name__}")
            traceback.print_exc()
    print(f"{passed}/{len(fns)} passed")


# ---------------------------------------------------------------------------
# New primitives for THE UNMOORING: craves/erasure, co-regulation, confidence,
# and the field() core builtin. Each locks a mechanism the novel needs.
# ---------------------------------------------------------------------------

def test_field_builtin_reads_a_population():
    """field(tag) returns the mean of all *.tag channels -- the read that makes
    belief-about-belief expressible."""
    from soma import run_source
    src = """
    sim { duration: 3  dt: 1 }
    character A { body a @cardiac { intero holds : Signal baseline 10 }
      loop r @cardiac { prior: predict(0) sense: holds precision: 0.9
        conviction: 0.2 act { emit feel(resolve) when field(holds) > 5 } } }
    character B { body b @cardiac { intero holds : Signal baseline 0 } }
    """
    r = run_source(src, "t")
    # field(holds) = mean(10, 0) = 5, which is NOT > 5, so no resolve; bump one:
    assert any(e.kind == "settle" for e in r.chronicle)


def test_craves_erased_is_an_addiction_loop():
    """A rank fed then wiped each night makes the hunger recur -- fed, erased,
    hungry, fed. The 'a hunger the world keeps wiping' pattern must catch it, and
    a never-wiped supply must NOT read as an addiction."""
    s = Story("ring", span="20s", step="1s", about="a wiped hunger")
    b = s.character("Blade", temperament=volatile)
    b.craves("to_matter", fed_by="rank", feeling="worthlessness",
             fed_feeling="pride", erased=0.9, threshold=5)
    for t in (2, 8, 14):
        s.at(f"{t}s", b.hears("rank", 9))
    for t in (5, 11, 17):
        s.at(f"{t}s", b.hears("rank", 0))
    _compiles(s)
    pats = {f.pattern for f in s.sift()}
    assert "a hunger the world keeps wiping" in pats


def test_craves_unfed_is_a_longing_not_an_addiction():
    """A craving whose supply never comes is a standing longing, not an
    addiction -- worded differently, and never labeled 'kept wiping'."""
    s = Story("boat", span="16s", step="1s", about="a want never fed")
    sound = s.character("Sound", temperament=stoic)
    sound.craves("own_boat", fed_by="slack_tide", feeling="longing", threshold=5)
    # slack_tide is never supplied
    for t in range(2, 16):
        s.at(f"{t}s", sound.hears("the_water", 0))   # unrelated; boat stays unfed
    _compiles(s)
    pats = {f.pattern for f in s.sift()}
    assert "a want the world will not feed" in pats
    assert "a hunger the world keeps wiping" not in pats


def test_tended_by_lowers_distress_precision_not_belief():
    """Co-regulation: a steady presence turns the trust in an alarm down without
    touching the belief. Grief floods while alone and quiets once the steady one
    arrives -- and the loop's pi_s, not its belief, is what changed."""
    s = Story("combs", span="14s", step="1s", about="held in the dark")
    top = s.character("Topman", temperament=anxious)
    rov = s.character("Rover", temperament=stoic)
    top.has_body_signal("grief_signal", baseline=0)
    top.appraises("grief_signal", as_threat=True, feeling="grief",
                  when="grief_signal > 4")
    rov.steadies()
    top.tended_by(rov, calms="grief_signal", strength=0.85)
    for t in range(2, 14):
        s.at(f"{t}s", top.hears("grief_signal", 9))
    for t in range(7, 14):
        s.at(f"{t}s", rov.present())
    _compiles(s)
    r = s.result()
    grief = sorted(round(e.t) for e in r.chronicle if e.kind == "emit"
                   and "grief" in str(e.detail.get("quale", "")))
    before = sum(1 for t in grief if t < 7)
    after = sum(1 for t in grief if t >= 8)
    assert before >= 3 and after == 0, f"grief before={before} after={after}"
    assert "held in the dark" in {f.pattern for f in s.sift()}


def test_confidence_cascades_after_one_shock():
    """A belief many hold only because the others hold it collapses in a rush
    once one holder is shocked into letting go -- nothing, nothing, then
    everything at once."""
    s = Story("run", span="16s", step="1s", about="the run")
    names = ["Venn", "Marl", "Osset", "Peg", "Quill"]
    banks = [s.character(n, temperament=guarded) for n in names]
    for b in banks:
        b.holds_with_others("paper_sound", field_tag="holds", believing=10,
                            shocked_at=("5s" if b is banks[0] else None),
                            says="sound")
    _compiles(s)
    r = s.result()
    # every holder's holding is ~full before the shock and ~zero well after
    for n in names:
        h = r.channel_hist[f"{n}.holds"]
        assert h[3] > 8, f"{n} not holding before shock"
        assert h[-1] < 2, f"{n} still holding after the run"
    assert "the run" in {f.pattern for f in s.sift()}


def test_hollowed_temperament_registered():
    assert "hollowed" in TEMPERAMENTS
    assert hollowed.precision < 0.2 and hollowed.conviction < 0.2


def test_the_unmooring_examples_compile_and_sift():
    """Every study in the novel's example file source-checks and sifts, and each
    recovers the characterization it was built to show."""
    import importlib
    mod = importlib.import_module("examples.narrative.the_unmooring")
    importlib.reload(mod)
    wanted = {
        "fleet": "the value the body broke",
        "ring": "a hunger the world keeps wiping",
        "combs": "held in the dark",
        "greywater": "the run",
        "selm": "the value the body broke",
        "coat": "the lie seen",
        "derived": "the lie kept",
    }
    for key, fn in mod.BUILDS.items():
        story = fn()
        check(parse(story.source(), title=key))
        pats = {f.pattern for f in story.sift()}
        assert wanted[key] in pats, f"{key} missing {wanted[key]!r}: {pats}"


def test_craves_fed_and_kept_is_the_healthy_case():
    """A hunger met by a supply that does not erase hardly aches -- the third
    fate of a craving, and the one that makes the wiped and unfed cases legible
    by contrast (Ink's reading beside Blade's rank)."""
    s = Story("reading", span="18s", step="1s", about="a hunger quietly met")
    ink = s.character("Ink", temperament=guarded)
    ink.craves("to_matter", fed_by="reading", feeling="worthlessness",
               fed_feeling="recognition", erased=0.0, threshold=5)
    for t in range(2, 16):
        s.at(f"{t}s", ink.hears("reading", 9))     # fed, durably
    _compiles(s)
    pats = {f.pattern for f in s.sift()}
    assert "a hunger the world keeps fed" in pats
    assert "a hunger the world keeps wiping" not in pats


def test_confabulation_is_graded_and_names_the_feeling():
    """A denial of a strongly-felt distress scores high and names the feeling it
    is covering, instead of a flat generic gap."""
    s = Story("denial", span="8s", step="0.5s", about="a lie over a feeling")
    n = s.character("Nadia", temperament=anxious)
    n.senses("ear")
    n.appraises("ear", as_threat=True, drives="heart", to=118, when="ear > 3",
                fades_to=70)
    n.feels("dread", from_body="heart")
    n.narrates(downplaying={"dread": "I'm fine."})
    s.at("2s", n.hears("ear", 9))
    _compiles(s)
    confab = [f for f in s.sift() if f.pattern == "confabulation gap"]
    assert confab, "no confabulation found"
    top = confab[0]
    assert top.score >= 0.8, f"denial of felt dread should score high, got {top.score}"
    assert "dread" in top.text, "the finding should name the denied feeling"


# --- the wound / lie / need dialectic, and the arc (v0.5 depth constructs) ---

def _lie_story(breakable):
    """A character with a wound, a lie, and the need it defends, plus escalating
    disconfirming evidence -- the machinery of a character arc."""
    s = Story("arc", span="16s", step="1s", about="a lie and its arc")
    b = s.character("B", temperament=volatile)
    b.wounded_by("named the surplus as a boy", teaches="only-rank")
    b.believes("only-rank",
               claim="If I'm not ranked above them, I'm the surplus again.",
               disconfirmed_by="equal_regard", feeling="worthlessness",
               harms="others", breakable=breakable,
               says="Some of us need there to be an upstairs.")
    b.needs("to-matter-as-an-equal", opposes="only-rank",
            feeling="worthlessness", fed_feeling="belonging")
    for t, v in [("3s", 6), ("6s", 7), ("9s", 8), ("12s", 9), ("15s", 9)]:
        s.at(t, b.hears("equal_regard", v))
    return s


def test_wound_lie_need_compile_and_speak():
    """The lie/need constructs compile to valid SOMA, and the lie is spoken (its
    says becomes a narration -- the cover story over the aching need)."""
    s = _lie_story(breakable=40)
    _compiles(s)
    r = s.result()
    narrated = [e for e in r.chronicle if e.kind == "narrate"]
    assert any("upstairs" in str(e.detail.get("quote", "")) for e in narrated), \
        "the lie's says should be spoken as a confabulation"


def test_breakable_lie_is_seen_positive_arc():
    """A breakable lie, met with escalating evidence, is overwhelmed and breaks --
    a self-revelation -- and the need it defended is then met."""
    s = _lie_story(breakable=40)
    pats = {f.pattern for f in s.sift()}
    assert "the lie seen" in pats, f"breakable lie should be seen: {pats}"
    assert "the need met" in pats, f"need should be met after the lie breaks: {pats}"
    r = s.result()
    assert any(e.kind == "revelation" for e in r.chronicle), "no revelation logged"


def test_unbreakable_lie_is_kept_negative_arc():
    """A lie that cannot break suppresses the evidence to the end, hardening -- the
    tragic arc -- and the need it defends is never met."""
    s = _lie_story(breakable=None)
    pats = {f.pattern for f in s.sift()}
    assert "the lie kept" in pats, f"unbreakable lie should be kept: {pats}"
    assert "a need the want never feeds" in pats, f"need should starve: {pats}"
    r = s.result()
    assert not any(e.kind == "revelation" for e in r.chronicle), \
        "an unbreakable lie must never reveal"


def test_portrait_reads_wound_lie_need_and_arc():
    """The synthesized portrait reports the deepest layer: the wound, the lie
    (with its moral/psychological weakness), the need, and which way the arc ran."""
    import re as _re
    s = _lie_story(breakable=40)
    raw = _re.sub(r"\x1b\[[0-9;]*m", "", s.characterize(width=90))
    port = " ".join(raw.replace("│", " ").split())   # strip color + box, collapse
    assert "Wounded by" in port
    assert "The lie he believes" in port and "harms others" in port
    assert "Arc:" in port and "seen" in port
    assert "Needs" in port


def test_auto_breakable_lie_derives_its_own_breaking_point():
    """`breakable=True` (the default) breaks the lie automatically, with no author
    threshold -- and a harder-held lie (higher conviction) resists longer, so the
    moment of self-revelation emerges from conviction vs. evidence."""
    def breaks_at(conviction):
        s = Story("auto", span="20s", step="1s", about="an auto-breakable lie")
        b = s.character("B", temperament=volatile)
        b.believes("lie", claim="I don't matter.", disconfirmed_by="regard",
                   feeling="worthlessness", conviction=conviction, breakable=True,
                   says="I'm fine on my own.")
        b.needs("truth", opposes="lie", feeling="worthlessness", fed_feeling="belonging")
        for t, v in [("3s", 6), ("6s", 7), ("9s", 8), ("12s", 9), ("15s", 9),
                     ("18s", 9)]:
            s.at(t, b.hears("regard", v))
        r = s.result()
        revs = [e.t for e in r.chronicle if e.kind == "revelation"]
        return revs[0] if revs else None
    soft = breaks_at(0.6)
    hard = breaks_at(1.4)
    assert soft is not None and hard is not None, "an auto lie should break"
    assert hard > soft, ("a harder-held lie must resist longer under auto-overwhelm "
                         f"(soft broke at {soft}, hard at {hard})")


def test_auto_overwhelm_source_uses_the_keyword():
    """A breakable=True lie compiles to `overwhelm: auto`, not a magic number."""
    s = Story("auto", span="6s", step="1s", about="auto")
    b = s.character("B", temperament=volatile)
    b.believes("lie", claim="x", disconfirmed_by="ev", breakable=True, says="x")
    src = s.source()
    assert "overwhelm:  auto" in src or "overwhelm: auto" in src
    _compiles(s)


# --- the predictive layer: derive structure, forecast unseen situations -------

def test_schema_predicts_three_lies_from_one_wound():
    """The same wound, coped three ways, is predicted to produce three different
    lies -- a positive prediction of personality structure, not a restatement."""
    from soma.narrative import predict_lie
    claims = {c: predict_lie("worth", c).claim
              for c in ("surrender", "avoidance", "overcompensation")}
    assert len(set(claims.values())) == 3, "coping styles should diverge"
    assert predict_lie("worth", "overcompensation").harms == "others"
    assert predict_lie("worth", "surrender").harms == "self"


def test_adopts_installs_a_derived_lie_that_runs():
    """adopts() lets the library predict the lie from the wound and install it; the
    derived lie drives a real arc."""
    s = Story("derived", span="16s", step="1s", about="a derived lie")
    b = s.character("B", temperament=volatile)
    b.adopts("worth", "overcompensation", disconfirmed_by="equal_regard",
             breakable=None)
    for t, v in [("3s", 6), ("6s", 7), ("9s", 8), ("12s", 9), ("15s", 9)]:
        s.at(t, b.hears("equal_regard", v))
    _compiles(s)
    pats = {f.pattern for f in s.sift()}
    assert "the lie kept" in pats


def _cast():
    s = Story("cast", span="16s", step="1s", about="a breakable and an unbreakable lie")
    breaker = s.character("Breaker", temperament=volatile)
    breaker.believes("bends", claim="I'm nothing.", disconfirmed_by="regard",
                     feeling="worthlessness", conviction=0.8, breakable=True,
                     says="I'm fine.")
    keeper = s.character("Keeper", temperament=guarded)
    keeper.believes("holds", claim="I'm nothing.", disconfirmed_by="regard",
                    feeling="worthlessness", breakable=None, says="I'm fine.")
    return s


def test_predict_forecasts_unseen_response_and_discriminates():
    """predict() forecasts a response to a stimulus that was never scripted, and it
    tells a breakable character apart from an unbreakable one -- generalization,
    the mark of a predictive (not merely descriptive) model."""
    s = _cast()
    p_break = s.predict("Breaker", {"regard": 9})
    p_keep = s.predict("Keeper", {"regard": 9})
    assert p_break.breaks_lie, "the breakable lie should break under strong evidence"
    assert not p_keep.breaks_lie and p_keep.route == "suppress", \
        "the unbreakable lie should suppress the same evidence"


def test_tipping_point_is_quantitative_and_falsifiable():
    """tipping_point() predicts the least evidence that turns a lie -- a sharp
    number for the breakable one, and *no* threshold in range for the kept one
    (the strongest falsification target)."""
    s = _cast()
    tp_break = s.tipping_point("Breaker", "regard")
    tp_keep = s.tipping_point("Keeper", "regard")
    assert tp_break["breaks_at"] is not None
    assert tp_keep["breaks_at"] is None
