"""
Tests for the 0.10 protocol layer: the Strange Situation (with blind
construct-validity) and the Gottman-Murray marriage model (with thin-slice
forecasting). The organizing standard: a standardized protocol earns its place
only if its classifications are RECOVERED from behavior the classifier never
labeled, and its forecasts survive runs they were staked before.
"""
import pytest

from soma.narrative import (Story, trusting, anxious, stoic, guarded, tender,
                            strange_situation, validate_instrument,
                            COUPLE_TYPES, marry, gottman_assess)


TEMPS = {"secure": trusting, "anxious": anxious,
         "avoidant": stoic, "disorganized": guarded}


def child_with(style):
    s = Story(f"ss_{style}", span="24s", step="1s",
              about="separation distress")
    child = s.character("Noa", temperament=TEMPS[style])
    child.attaches(style, to="mother")
    return s, child


def couple(type_name):
    s = Story(f"m_{type_name}", span="20s", step="1s")
    a = s.character("Ash", temperament=trusting)
    b = s.character("Bee", temperament=tender)
    marry(s, a, b, type_name)
    return s


# ---------------------------------------------------------------------------
# the Strange Situation
# ---------------------------------------------------------------------------

class TestStrangeSituation:
    def test_blind_recovery_of_all_four_styles(self):
        """The construct-validity standard: the classifier reads only the
        behavior stream, and must recover every installed style."""
        results = validate_instrument(child_with)
        assert results["recovered"], results

    def test_codes_match_the_textbook_profiles(self):
        s, c = child_with("secure")
        rep = strange_situation(s, c)
        assert all(code.seeking >= 4 for code in rep.codes)
        assert all(code.resistance <= 2 for code in rep.codes)
        assert rep.settled_after

        s, c = child_with("anxious")
        rep = strange_situation(s, c)
        # the ambivalent picture: seeks AND resists, fails to settle
        assert all(code.seeking >= 5 for code in rep.codes)
        assert all(code.resistance >= 4 for code in rep.codes)
        assert not rep.settled_after

        s, c = child_with("avoidant")
        rep = strange_situation(s, c)
        assert all(code.avoidance >= 5 for code in rep.codes)
        assert all(code.seeking <= 3 for code in rep.codes)
        # the A signature's second register: arousal over displayed calm
        assert rep.physio_over_display

        s, c = child_with("disorganized")
        rep = strange_situation(s, c)
        assert rep.disorganization

    def test_unattached_child_raises(self):
        s = Story("ss_none", span="24s", step="1s")
        c = s.character("Ines", temperament=trusting)
        c.senses("x")
        with pytest.raises(ValueError):
            strange_situation(s, c)

    def test_hand_built_child_is_classified_from_tape(self):
        """A child assembled from raw verbs -- no style bundle -- must still
        classify by its behavior; classification as discovery."""
        s = Story("ss_kit", span="24s", step="1s",
                  about="separation distress")
        kit = s.character("Kit", temperament=anxious)
        kit.senses("mother_near", baseline=8.0)
        kit.appraises("mother_near", as_threat=True, when="mother_near < 3",
                      drives="heart", to=122, fades_to=101, precision=0.97,
                      conviction=0.2, expects=8.0,
                      shows_on="protest_face", shows_value=9.0)
        kit.feels("dread", from_body="heart", threshold=95.0)
        kit.appraises("mother_near", when="mother_near * heart > 650",
                      shows_on="clings", shows_value=9.0, expects=8.0)
        kit.appraises("mother_near", when="mother_near * heart > 700",
                      shows_on="protest_face", shows_value=8.0, expects=8.0)
        kit._attachment = dict(style="?", figure="mother",
                               near="mother_near", resting=72.0,
                               arousal_to=122.0)
        rep = strange_situation(s, kit)
        assert rep.classification == "anxious"

    def test_report_renders(self):
        s, c = child_with("secure")
        out = strange_situation(s, c).render()
        assert "CLASSIFICATION" in out and "seek" in out


# ---------------------------------------------------------------------------
# the Gottman-Murray model
# ---------------------------------------------------------------------------

class TestGottman:
    def test_all_five_type_forecasts_confirm(self):
        for tname in COUPLE_TYPES:
            rep = gottman_assess(couple(tname))
            assert rep.confirmed, f"{tname}:\n{rep.render()}"

    def test_stable_and_unstable_types_separate_on_reciprocity(self):
        """Negative-affect reciprocity is the cascade's signature: near-total
        in the unstable couples, near-zero in the regulated ones."""
        recips = {t: gottman_assess(couple(t)).reciprocity
                  for t in COUPLE_TYPES}
        for t, ct in COUPLE_TYPES.items():
            if ct.stable:
                assert recips[t] <= 0.2, (t, recips)
            else:
                assert recips[t] >= 0.7, (t, recips)

    def test_thin_slice_forecasts_every_ending(self):
        """The minutes-to-years claim: the first-quarter diagnosis must call
        the full run's ending for every couple type."""
        for tname in COUPLE_TYPES:
            rep = gottman_assess(couple(tname))
            thin = next(v for v in rep.verdicts if "THIN SLICE" in v[0])
            assert thin[3], f"{tname}: thin slice missed\n{rep.render()}"

    def test_hostile_ratio_below_one_stable_ratio_at_least_one(self):
        r_val = gottman_assess(couple("validating"))
        r_hos = gottman_assess(couple("hostile"))
        assert r_val.ratio >= 1.0
        assert r_hos.ratio < 1.0

    def test_repair_fires_in_repairing_types_only(self):
        from soma import run_source
        for tname, has_repair in (("validating", True), ("hostile", False)):
            s = couple(tname)
            src = s.source()
            kept = [ln for ln in src.splitlines()
                    if not ln.lstrip().startswith("stimulus ")]
            probe = ["stimulus Ash.grievance { at 3s: 8  at 4s: 8  at 5s: 0 }"]
            r = run_source("\n".join(kept + [""] + probe))
            bids = [e for e in r.chronicle if e.kind == "emit"
                    and "reaching" in str(e.detail.get("quale", ""))]
            assert bool(bids) == has_repair, (tname, len(bids))

    def test_report_renders(self):
        out = gottman_assess(couple("volatile")).render()
        assert "GOTTMAN" in out and "ratio" in out and "THIN SLICE" in out
