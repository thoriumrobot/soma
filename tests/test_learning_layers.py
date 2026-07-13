"""
Tests for the 0.11 learning layer: reward prediction error / conditioning
(Rescorla-Wagner + dual-trace spontaneous recovery) and reformulated learned
helplessness (the triadic design and its attributional transfer prediction).

The standard under test: each model's SIGNATURE prediction -- the one a simpler
account cannot make -- must hold. For conditioning that is spontaneous recovery
(single-trace RW cannot produce it); for helplessness it is the global/specific
transfer asymmetry (undimensional helplessness cannot produce it).
"""
import pytest

from soma.narrative import (Story, trusting, hollowed, stoic,
                            predict_conditioning, triadic_design)


# ---------------------------------------------------------------------------
# conditioning / reward prediction error
# ---------------------------------------------------------------------------

def subject(cs="tone", us="food"):
    s = Story("cond", span="10s", step="1s", about="conditioning")
    rat = s.character("Rat", temperament=trusting)
    s.conditions(rat, cs=cs, us=us)
    return s


class TestConditioning:
    def test_acquisition_climbs_to_the_reward(self):
        rep = subject().predict_conditioning("Rat", acquire=8, extinguish=6, rest=4)
        assert rep.acquired_peak >= 5.0

    def test_rpe_shrinks_as_reward_becomes_predicted(self):
        """Dopamine's signature: large RPE to an unpredicted reward, falling
        toward zero once the reward is predicted."""
        rep = subject().predict_conditioning("Rat", acquire=8, extinguish=6, rest=4)
        # peak RPE is early; late-acquisition RPE is small
        assert max(rep.rpe) > 3.0
        v = next(x for x in rep.verdicts if "RPE shrinks" in x[0])
        assert v[3], rep.render()

    def test_extinction_lowers_the_value(self):
        rep = subject().predict_conditioning("Rat", acquire=8, extinguish=10, rest=2)
        assert rep.extinguished_to < rep.acquired_peak - 1.0

    def test_spontaneous_recovery_is_the_signature(self):
        """The prediction single-trace Rescorla-Wagner cannot make: after a
        rest, the conditioned value returns."""
        rep = subject().predict_conditioning("Rat", acquire=10, extinguish=12, rest=8)
        assert rep.spontaneous_recovery
        assert rep.recovered_to > rep.extinguished_to + 0.5

    def test_recovery_grows_with_rest(self):
        """Control: spontaneous recovery is a property of the rest interval --
        more rest, more return of the conditioned value. This rules out
        recovery as a fixed artifact of the extinction phase."""
        short = subject().predict_conditioning("Rat", acquire=10,
                                               extinguish=12, rest=2)
        long = subject().predict_conditioning("Rat", acquire=10,
                                              extinguish=12, rest=10)
        assert long.recovered_to > short.recovered_to + 1.0

    def test_savings_on_reacquisition(self):
        rep = subject().predict_conditioning("Rat", acquire=8, extinguish=8, rest=6,
                                             reacquire=5)
        v = next(x for x in rep.verdicts if "savings" in x[0])
        assert v[3], rep.render()

    def test_all_predictions_confirm(self):
        rep = subject().predict_conditioning("Rat", acquire=10, extinguish=12, rest=8,
                                             reacquire=6)
        assert rep.confirmed, rep.render()

    def test_non_subject_raises(self):
        s = Story("x", span="6s", step="1s")
        s.character("NotASubject", temperament=trusting).senses("z")
        with pytest.raises(ValueError):
            s.predict_conditioning("NotASubject")

    def test_report_renders(self):
        out = subject().predict_conditioning("Rat", acquire=8, extinguish=6,
                                             rest=6).render()
        assert "CONDITIONING" in out and "RECOVERY" in out


# ---------------------------------------------------------------------------
# learned helplessness
# ---------------------------------------------------------------------------

def hp_builder(style):
    s = Story(f"hlp_{style}", span="10s", step="1s",
              about="learned helplessness")
    subj = s.character("Dog",
                       temperament=hollowed if style == "global" else trusting)
    s.learns_control(subj, style=style)
    return s, subj


class TestHelplessness:
    def test_uncontrollable_produces_a_deficit(self):
        s, d = hp_builder("global")
        rep = s.predict_helplessness("Dog", pretreatment="uncontrollable",
                                     novel_task_similar=True)
        assert rep.deficit and rep.confirmed

    def test_controllable_pretreatment_immunizes(self):
        """The triadic design's control group: controllable aversive events do
        NOT produce the deficit."""
        s, d = hp_builder("global")
        rep = s.predict_helplessness("Dog", pretreatment="controllable",
                                     novel_task_similar=False)
        assert not rep.deficit and rep.confirmed

    def test_no_pretreatment_no_deficit(self):
        s, d = hp_builder("global")
        rep = s.predict_helplessness("Dog", pretreatment="none")
        assert not rep.deficit and rep.confirmed

    def test_global_style_transfers_to_dissimilar_task(self):
        s, d = hp_builder("global")
        rep = s.predict_helplessness("Dog", pretreatment="uncontrollable",
                                     novel_task_similar=False)
        assert rep.transfers   # "I can't do anything right"

    def test_specific_style_does_not_transfer_to_dissimilar_task(self):
        """The reformulation's sharpest claim: a specific explanatory style
        confines the deficit to situations like the original."""
        s, d = hp_builder("specific")
        rep = s.predict_helplessness("Dog", pretreatment="uncontrollable",
                                     novel_task_similar=False)
        assert not rep.transfers
        # but it DOES show up in a similar situation
        s2, d2 = hp_builder("specific")
        rep2 = s2.predict_helplessness("Dog", pretreatment="uncontrollable",
                                       novel_task_similar=True)
        assert rep2.deficit

    def test_full_triadic_pattern(self):
        td = triadic_design(hp_builder)
        assert td["all_confirmed"]
        assert td["transfer_signature"]

    def test_non_subject_raises(self):
        s = Story("x", span="6s", step="1s")
        s.character("Nobody", temperament=trusting).senses("z")
        with pytest.raises(ValueError):
            s.predict_helplessness("Nobody")

    def test_report_renders(self):
        s, d = hp_builder("specific")
        out = s.predict_helplessness("Dog", pretreatment="uncontrollable",
                                     novel_task_similar=False).render()
        assert "HELPLESSNESS" in out and "explanatory style" in out
