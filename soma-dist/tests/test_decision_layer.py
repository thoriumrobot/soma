"""
Tests for the 0.12 decision layer: the drift-diffusion model of speeded
two-choice decisions. The standard under test is the DDM's signature, which no
deterministic or single-number account can reproduce: right-skewed RT
distributions, the boundary/drift dissociation, biased-start error asymmetry,
and above all the speed-accuracy tradeoff traced from the boundary alone -- all
reproducible in the seed, with the deterministic core left untouched.
"""
import pytest

from soma.narrative import Story, trusting, stoic, DECISION_STYLES


def thinker(**kw):
    s = Story("decide", span="1s", step="1s", about="a decision")
    j = s.character("Juror", temperament=trusting)
    s.decides(j, **kw)
    return s


class TestDecision:
    def test_seed_is_reproducible(self):
        s = thinker(style="keen")
        a = s.predict_decision("Juror", trials=800, seed=7)
        b = s.predict_decision("Juror", trials=800, seed=7)
        assert a.accuracy == b.accuracy and a.mean_rt == b.mean_rt

    def test_different_seeds_differ(self):
        s = thinker(style="keen")
        a = s.predict_decision("Juror", trials=800, seed=1)
        b = s.predict_decision("Juror", trials=800, seed=2)
        assert a.mean_rt != b.mean_rt

    def test_rt_distribution_is_right_skewed(self):
        """The DDM's signature RT shape -- a long right tail."""
        rep = thinker(style="keen").predict_decision("Juror", trials=3000,
                                                     seed=0)
        assert rep.skew > 0.3

    def test_high_drift_is_fast_and_accurate(self):
        keen = thinker(style="keen").predict_decision("Juror", trials=3000,
                                                      seed=0)
        muddled = thinker(style="muddled").predict_decision("Juror",
                                                            trials=3000, seed=0)
        # higher drift (better evidence) -> both more accurate AND faster
        assert keen.accuracy > muddled.accuracy
        assert keen.mean_rt < muddled.mean_rt

    def test_boundary_sets_caution_not_ability(self):
        """Impulsive and deliberate share a drift; only the boundary differs.
        The deliberate one is more accurate and slower -- pure caution."""
        imp = thinker(style="impulsive").predict_decision("Juror", trials=3000,
                                                          seed=0)
        dlb = thinker(style="deliberate").predict_decision("Juror", trials=3000,
                                                          seed=0)
        assert dlb.accuracy > imp.accuracy
        assert dlb.mean_rt > imp.mean_rt

    def test_start_bias_makes_errors_slow(self):
        """A prior lean toward the correct bound produces fast correct
        responses but SLOW errors -- the classic biased-start asymmetry, which
        a symmetric model cannot show."""
        rep = thinker(style="prejudiced").predict_decision("Juror",
                                                           trials=4000, seed=0)
        assert rep.mean_rt_error > rep.mean_rt + 0.3

    def test_unbiased_errors_match_corrects(self):
        """Control: with no start bias, error and correct RTs are close --
        confirming the asymmetry above comes from the bias, not the machinery."""
        rep = thinker(drift=0.12, boundary=1.0, start_bias=0.5) \
            .predict_decision("Juror", trials=4000, seed=0)
        assert abs(rep.mean_rt_error - rep.mean_rt) < 0.3

    def test_speed_accuracy_tradeoff(self):
        """The DDM's most famous prediction: sweeping the boundary alone traces
        a monotone tradeoff -- wider is more accurate AND slower, together."""
        s = thinker(drift=0.13, boundary=1.0)
        sat = s.speed_accuracy("Juror", boundaries=[0.5, 1.0, 1.5, 2.0],
                               trials=3000, seed=0)
        assert sat.confirmed, sat.render()
        # and the endpoints really do span a meaningful range
        accs = [acc for _, acc, _ in sat.rows]
        assert accs[-1] - accs[0] > 0.1

    def test_all_named_styles_run(self):
        for style in DECISION_STYLES:
            rep = thinker(style=style).predict_decision("Juror", trials=500,
                                                        seed=0)
            assert 0.0 <= rep.accuracy <= 1.0 and rep.mean_rt > 0

    def test_non_subject_raises(self):
        s = Story("x", span="1s", step="1s")
        s.character("Nobody", temperament=trusting)
        with pytest.raises(ValueError):
            s.predict_decision("Nobody")

    def test_report_renders(self):
        out = thinker(style="deliberate").predict_decision("Juror", trials=500,
                                                          seed=0).render()
        assert "DECISION" in out and "accuracy" in out and "quantiles" in out


class TestDeterminismPreserved:
    def test_base_runs_still_deterministic(self):
        """The decision layer's noise must not leak into the deterministic
        core: an ordinary belief story reproduces exactly."""
        def build():
            s = Story("d", span="8s", step="1s", about="a belief")
            c = s.character("Ink", temperament=stoic)
            c.senses("e")
            c.believes("b", claim="b", disconfirmed_by="e", breakable=True)
            for t in range(2, 6):
                s.at(f"{t}s", c.hears("e", 8))
            return s
        a = build().result()
        b = build().result()
        ra = [e.t for e in a.chronicle if e.kind == "revelation"]
        rb = [e.t for e in b.chronicle if e.kind == "revelation"]
        assert ra == rb
