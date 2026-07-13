"""
Tests for the 0.8 prediction layers: appraisal, attachment, circumplex, and
preregistration. The organizing principle under test is use-novelty: every
forecast must be derived from theory-side inputs (an appraisal pattern, a
style table, a pair of stances) and then survive contact with a run it was
not fitted to -- including, in the cross-style tests, runs designed to
falsify the *wrong* forecast.
"""
import pytest

from soma.narrative import (Story, anxious, stoic, trusting, guarded,
                            volatile, tender,
                            predict_feeling, Stance, predict_pull,
                            complementarity, ATTACHMENT_STYLES)


# ---------------------------------------------------------------------------
# appraisal: the emotion is derived, never named by the author
# ---------------------------------------------------------------------------

class TestAppraisalTheory:
    def test_other_blame_with_power_predicts_anger(self):
        pf = predict_feeling(congruence=-0.8, agency="other",
                             certainty=0.9, coping=0.8)
        assert pf.quale == "anger"
        assert "against" in pf.tendency

    def test_other_blame_without_power_predicts_resentment(self):
        pf = predict_feeling(congruence=-0.8, agency="other",
                             certainty=0.9, coping=0.2)
        assert pf.quale == "resentment"

    def test_uncertain_other_threat_predicts_fear(self):
        pf = predict_feeling(congruence=-0.8, agency="other",
                             certainty=0.3, coping=0.5)
        assert pf.quale == "fear"

    def test_certain_uncontrollable_loss_predicts_grief(self):
        pf = predict_feeling(congruence=-0.9, agency="circumstance",
                             certainty=0.95, coping=0.1)
        assert pf.quale == "grief"

    def test_uncertain_circumstance_predicts_dread(self):
        pf = predict_feeling(congruence=-0.7, agency="circumstance",
                             certainty=0.2, coping=0.3)
        assert pf.quale == "dread"

    def test_guilt_is_about_the_act_shame_about_the_self(self):
        g = predict_feeling(congruence=-0.7, agency="self",
                            norm_compatible=False, norm_focus="act")
        s = predict_feeling(congruence=-0.7, agency="self",
                            norm_compatible=False, norm_focus="self")
        assert (g.quale, s.quale) == ("guilt", "shame")
        assert "repair" in g.tendency and "hide" in s.tendency

    def test_conducive_uncertainty_predicts_hope(self):
        assert predict_feeling(congruence=0.6, certainty=0.3).quale == "hope"

    def test_disconfirmed_fear_predicts_relief_not_joy(self):
        r = predict_feeling(congruence=0.7, certainty=0.9, was_feared=True)
        j = predict_feeling(congruence=0.7, certainty=0.9, was_feared=False)
        assert (r.quale, j.quale) == ("relief", "joy")

    def test_self_and_other_credit(self):
        assert predict_feeling(congruence=0.7, certainty=0.9,
                               agency="self").quale == "pride"
        assert predict_feeling(congruence=0.7, certainty=0.9,
                               agency="other").quale == "gratitude"

    def test_irrelevance_predicts_nothing(self):
        assert predict_feeling(congruence=-0.9, relevance=0.05) is None
        assert predict_feeling(congruence=0.05) is None

    def test_forecast_quale_actually_fires_in_the_compiled_story(self):
        """The falsifiability contract: the predicted emotion must appear in
        the Chronicle when the appraised event lands."""
        s = Story("t_appr", span="6s", step="1s")
        v = s.character("Vera", temperament=anxious)
        v.senses("verdict")
        pf = v.appraises_event("verdict", congruence=-0.9, agency="other",
                               certainty=0.9, coping=0.2,
                               when="verdict > 5", drives="heart", to=110,
                               fades_to=72)
        s.at("2s", v.hears("verdict", 9))
        r = s.result()
        emits = {str(e.detail.get("quale", "")) for e in r.chronicle
                 if e.kind == "emit"}
        assert any(pf.quale in q for q in emits)

    def test_distress_forecast_compiles_with_consent(self):
        """A predicted distress quale (grief) still passes the consent gate --
        the compiler adds @consent for it like any authored feeling."""
        s = Story("t_appr2", span="6s", step="1s")
        v = s.character("Iva", temperament=stoic)
        v.senses("news")
        pf = v.appraises_event("news", congruence=-0.9, agency="circumstance",
                               certainty=0.95, coping=0.1, when="news > 5")
        assert pf.quale == "grief"
        s.at("2s", v.hears("news", 9))
        s.result()   # would raise ConsentError if the gate were not satisfied

    def test_mapping_is_identifiable(self):
        """Construct validity, the standard the Strange Situation meets: the
        forward and inverse mappings are mutually consistent for every emotion
        -- so the forecast is a prediction, not a label."""
        from soma.narrative import check_identifiability
        v = check_identifiability()
        assert v["recovered"], v["rows"]
        assert v["n_correct"] == v["n"] == 14

    def test_inverse_inference_round_trips(self):
        """recover_appraisal(emotion) must, run forward, yield that emotion."""
        from soma.narrative import recover_appraisal, predict_feeling
        for emotion in ("anger", "grief", "shame", "relief", "gratitude",
                        "hope", "pride", "fear", "dread", "regret"):
            appr = recover_appraisal(emotion)
            assert predict_feeling(**appr).quale == emotion

    def test_explain_emotion_reads_the_appraisal_back(self):
        from soma.narrative import explain_emotion
        txt = explain_emotion("anger")
        assert "someone else caused it" in txt and "move against" in txt
        txt2 = explain_emotion("grief")
        assert "no one caused it" in txt2 and "nothing can be done" in txt2

    def test_recover_appraisal_rejects_unknown(self):
        from soma.narrative import recover_appraisal
        with pytest.raises(ValueError):
            recover_appraisal("nostalgia")


# ---------------------------------------------------------------------------
# attachment: four styles, four distinguishable separations
# ---------------------------------------------------------------------------

def _attached(style, temp):
    s = Story(f"t_att_{style}", span="12s", step="1s",
              about="separation distress")
    c = s.character("Mara", temperament=temp)
    c.attaches(style, to="Jonah")
    return s


class TestAttachment:
    def test_all_four_style_forecasts_confirm(self):
        for style, temp in (("secure", trusting), ("anxious", anxious),
                            ("avoidant", stoic), ("disorganized", guarded)):
            rep = _attached(style, temp).predict_separation("Mara")
            assert rep.confirmed, f"{style}: {rep.render()}"

    def test_styles_are_distinguishable_by_one_probe(self):
        """The same separation probe must yield DIFFERENT observable
        signatures per style -- otherwise the style table predicts nothing."""
        obs = {}
        for style, temp in (("secure", trusting), ("anxious", anxious),
                            ("avoidant", stoic), ("disorganized", guarded)):
            rep = _attached(style, temp).predict_separation("Mara")
            obs[style] = tuple(sorted(
                (k, v) for k, v in rep.detail["observed"].items()))
        assert len(set(obs.values())) == 4, obs

    def test_secure_does_not_show_the_avoidant_signature(self):
        rep = _attached("secure", trusting).predict_separation("Mara")
        assert rep.detail["observed"]["gap"] is False

    def test_avoidant_gap_rides_on_real_arousal(self):
        """The sharpest claim: narrated calm OVER a somatic spike -- both
        halves must be present, or 'repressive coping' is not what happened."""
        rep = _attached("avoidant", stoic).predict_separation("Mara")
        o = rep.detail["observed"]
        assert o["gap"] and o["arousal"]
        assert rep.detail["peak"] > rep.detail["resting"] + 15

    def test_anxious_stays_up_where_secure_settles(self):
        r_anx = _attached("anxious", anxious).predict_separation("Mara")
        r_sec = _attached("secure", trusting).predict_separation("Mara")
        assert r_anx.detail["observed"]["settles"] is False
        assert r_sec.detail["observed"]["settles"] is True

    def test_disorganized_wants_and_fears_the_same_figure(self):
        rep = _attached("disorganized", guarded).predict_separation("Mara")
        assert rep.detail["observed"]["ambivalence"] is True

    def test_override_is_recorded_as_accommodation(self):
        s = Story("t_att_ov", span="12s", step="1s",
                  about="separation distress")
        c = s.character("Mara", temperament=stoic)
        c.attaches("avoidant", to="Jonah", arousal_to=140.0)
        assert any("arousal_to" in a for a in s._accommodations)

    def test_unattached_character_raises(self):
        s = Story("t_att_none", span="6s", step="1s")
        s.character("Ines", temperament=trusting).senses("x")
        with pytest.raises(ValueError):
            s.predict_separation("Ines")


# ---------------------------------------------------------------------------
# circumplex: the space between two characters
# ---------------------------------------------------------------------------

class TestCircumplex:
    def test_pull_is_correspondence_on_warmth_reciprocity_on_dominance(self):
        p = predict_pull(Stance(dominance=0.8, warmth=0.5))
        assert p.stance.warmth == pytest.approx(0.5)
        assert p.stance.dominance == pytest.approx(-0.8)

    def test_pull_declares_its_confidence_asymmetry(self):
        p = predict_pull(Stance(dominance=0.5, warmth=0.5))
        assert "robust" in p.warmth_basis
        assert "weaker" in p.dominance_basis

    def test_octants(self):
        assert Stance(0.0, 1.0).octant() == "warm-agreeable"
        assert Stance(1.0, 0.0).octant() == "assured-dominant"
        assert Stance(0.0, -1.0).octant() == "coldhearted"
        assert Stance(-1.0, 0.0).octant() == "unassured-submissive"

    def test_complementarity_index(self):
        # perfectly complementary: same warmth, opposite dominance
        c = complementarity(Stance(0.6, 0.5), Stance(-0.6, 0.5))
        assert c["overall"] == 1.0
        # dominance collision lowers it
        c2 = complementarity(Stance(0.8, 0.5), Stance(0.8, 0.5))
        assert c2["dominance"] < 0.4

    def _dyad(self, sa, sb, ta, tb, title):
        s = Story(title, span="12s", step="1s")
        a = s.character("A", temperament=ta).stance(**sa)
        b = s.character("B", temperament=tb).stance(**sb)
        s.meet(a, b)
        return s, a, b

    def test_warm_complementary_dyad_settles(self):
        s, a, b = self._dyad(dict(dominance=0.4, warmth=0.7),
                             dict(dominance=-0.4, warmth=0.6),
                             trusting, tender, "t_dy_warm")
        rep = s.predict_dyad(a, b)
        assert rep.trajectory_forecast == "settles" and rep.confirmed

    def test_hostile_correspondence_strains_and_sustains(self):
        """Structurally complementary (cold matches cold) yet affectively
        corrosive -- the branch that separates complementarity from comfort."""
        s, a, b = self._dyad(dict(dominance=0.6, warmth=-0.6),
                             dict(dominance=0.5, warmth=-0.5),
                             guarded, volatile, "t_dy_cold")
        rep = s.predict_dyad(a, b)
        assert rep.trajectory_forecast == "strains" and rep.confirmed

    def test_the_looser_held_self_gives_ground(self):
        """The accommodation forecast is mechanism, not label: susceptibility
        to the pull is (1 - conviction), the same dial as every prior."""
        s, a, b = self._dyad(dict(dominance=0.6, warmth=-0.6),
                             dict(dominance=0.5, warmth=-0.5),
                             guarded, volatile, "t_dy_ground")
        rep = s.predict_dyad(a, b)
        claim = next(v for v in rep.verdicts if "gives ground" in v[0])
        assert claim[3], rep.render()


# ---------------------------------------------------------------------------
# preregistration: prediction separated from postdiction, mechanically
# ---------------------------------------------------------------------------

def _nadia_story():
    s = Story("t_prereg", span="8s", step="0.5s", about="acute distress")
    n = s.character("Nadia", temperament=anxious)
    n.senses("ear")
    n.appraises("ear", as_threat=True, drives="heart", to=118,
                when="ear > 3", fades_to=70)
    n.feels("dread", from_body="heart")
    n.narrates(downplaying={"dread": "I'm fine."})
    s.at("2s", n.hears("ear", 9))
    return s


class TestPreregistration:
    def test_confirmed_and_falsified_are_both_reported(self):
        s = _nadia_story()
        audit = s.preregister()
        audit.expect_feeling("Nadia", "dread", by="4s")
        audit.expect_gap("Nadia", at_least=0.4)
        audit.expect_peak("Nadia", "heart", at_least=110)
        audit.expect_feeling("Nadia", "joy")           # should fail
        rep = audit.check()
        assert rep.confirmed == 3 and rep.falsified == 1
        assert not rep.all_confirmed
        assert "FALSIFIED" in rep.render()

    def test_claims_after_check_are_postdictions_and_refused(self):
        audit = _nadia_story().preregister()
        audit.expect_feeling("Nadia", "dread")
        audit.check()
        with pytest.raises(RuntimeError):
            audit.expect_feeling("Nadia", "grief")

    def test_negative_claims(self):
        audit = _nadia_story().preregister()
        audit.expect_feeling("Nadia", "grief", present=False)
        rep = audit.check()
        assert rep.all_confirmed

    def test_break_and_no_break(self):
        s = Story("t_prereg_lie", span="14s", step="1s",
                  about="a defended belief")
        ink = s.character("Ink", temperament=stoic)
        ink.senses("kept_for_nothing")
        ink.believes("only_the_needed_matter",
                     claim="only the needed matter",
                     disconfirmed_by="kept_for_nothing", breakable=True)
        for t in range(2, 12):
            s.at(f"{t}s", ink.hears("kept_for_nothing", 8))
        audit = s.preregister()
        audit.expect_break("Ink")
        rep = audit.check()
        assert rep.all_confirmed, rep.render()

        s2 = Story("t_prereg_kept", span="14s", step="1s",
                   about="a defended belief")
        blade = s2.character("Blade", temperament=stoic)
        blade.senses("equal_regard")
        blade.believes("rank_or_surplus", claim="rank or surplus",
                       disconfirmed_by="equal_regard", breakable=None)
        for t in range(2, 12):
            s2.at(f"{t}s", blade.hears("equal_regard", 8))
        audit2 = s2.preregister()
        audit2.expect_no_break("Blade")
        assert audit2.check().all_confirmed

    def test_mood_direction(self):
        s = Story("t_prereg_mood", span="12s", step="1s")
        a = s.character("A", temperament=guarded).stance(dominance=0.5,
                                                         warmth=-0.6)
        b = s.character("B", temperament=volatile).stance(dominance=0.5,
                                                          warmth=-0.5)
        s.meet(a, b)
        s.at("1s", a.shows("manner", 2.9))
        s.at("1s", b.shows("manner", 3.2))
        audit = s.preregister()
        audit.expect_mood("A", "rapport", "falls")
        rep = audit.check()
        assert rep.all_confirmed, rep.render()

    def test_multi_character_gap_matches_the_self_narrator(self):
        """Regression: in a multi-character story the narrator is logged as
        'self_<Name>', so expect_gap must match that convention -- not just the
        '<Name>.' loop prefix. Before the fix this silently falsified every
        multi-character gap claim."""
        s = Story("t_multi_gap", span="10s", step="1s",
                  about="a composed face")
        a = s.character("Cleo", temperament=guarded)
        b = s.character("Immy", temperament=tender)
        a.senses("the_number")
        a.has_body_signal("composure", baseline=2)
        a.appraises("the_number", as_threat=True, drives="composure", to=8,
                    feeling="apprehension", when="the_number > 5", fades_to=2)
        a.values("fairness", says="I never cared about the money.",
                 betrayed_when="composure > 6", on_channel="composure")
        a.narrates(voice={"self_betrayal": "I'm not angry. Why would I be?"})
        b.senses("x")
        for t in range(3, 9):
            s.at(f"{t}s", a.hears("the_number", 9))
        audit = s.preregister()
        audit.expect_gap("Cleo", at_least=0.4)
        rep = audit.check()
        assert rep.all_confirmed, rep.render()
        s = Story("t_prereg_acc", span="10s", step="1s",
                  about="a defended belief")
        c = s.character("Coat", temperament=stoic)
        c.senses("his_own_act")
        c.adopts("worth", "surrender", disconfirmed_by="his_own_act",
                 conviction=0.5)     # hand-set: an accommodation
        audit = s.preregister()
        audit.expect_feeling("Coat", "worthlessness", present=False)
        rep = audit.check()
        assert rep.accommodations and "overridden" in rep.render()

    def test_custom_claim(self):
        audit = _nadia_story().preregister()
        audit.expect("the run produces at least 20 events",
                     lambda r: (len(list(r.chronicle)) >= 20,
                                f"{len(list(r.chronicle))} events"))
        assert audit.check().all_confirmed
