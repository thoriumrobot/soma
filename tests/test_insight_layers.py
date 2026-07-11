"""
Tests for the 0.9 study layer: insight substrate, sensitivity, discrimination,
early warning, and counterfactual minimal intervention. The organizing claim
under test: these instruments extract insight *about* predictive
characterizations -- which dial writes the ending, which scene separates two
readings, whether a break is legible before it happens, and what margin the
ending turns on -- and each answer is checked against actual runs, never
asserted from the description.
"""
import pytest

from soma.narrative import (Story, stoic, tender, anxious, trusting,
                            run_with, outcome, series)
from soma.narrative.insight import debt_series, error_series


LIE = "the_lie_only_the_needed_matter"


def kept_man():
    """A breakable-lie character: the shared fixture of the study layer."""
    s = Story("the_kept_man", span="16s", step="1s",
              about="a defended belief and its breaking")
    ink = s.character("Ink", temperament=stoic)
    ink.senses("kept_for_nothing")
    ink.believes("only_the_needed_matter", claim="only the needed matter",
                 disconfirmed_by="kept_for_nothing", breakable=True)
    ink.feels("grief", from_body="heart", threshold=80)
    for t in range(2, 14):
        s.at(f"{t}s", ink.hears("kept_for_nothing", 8))
    return s


def slow_burn(conviction=0.9, breakable=True, learn=0.03):
    """A gradually-overwhelmed belief, for the early-warning studies."""
    s = Story("slow", span="26s", step="1s", about="slowly overwhelmed")
    c = s.character("Vane", temperament=tender)
    c.senses("the_evidence")
    c.believes("i_did_not_matter", claim="I did not matter",
               disconfirmed_by="the_evidence", breakable=breakable,
               conviction=conviction)
    c.learns(learn)
    for t in range(2, 24):
        s.at(f"{t}s", c.hears("the_evidence", round(min(9, 2 + 0.3 * (t - 2)), 1)))
    return s


# ---------------------------------------------------------------------------
# the substrate: run_with + the outcome vocabulary
# ---------------------------------------------------------------------------

class TestInsightSubstrate:
    def test_run_with_no_overrides_matches_plain_run(self):
        s = kept_man()
        r1 = run_with(s)
        r2 = s.result()
        assert (outcome(r1, "break_time", character="Ink")
                == outcome(r2, "break_time", character="Ink"))

    def test_overrides_are_applied_and_recorded(self):
        s = kept_man()
        r = run_with(s, {f"{LIE}.conviction": 0.4})
        assert any("conviction" in a for a in r._overrides_applied)

    def test_overrides_change_the_outcome(self):
        s = kept_man()
        t_default = outcome(run_with(s), "break_time", character="Ink")
        t_loose = outcome(run_with(s, {f"{LIE}.conviction": 0.55}),
                          "break_time", character="Ink")
        assert t_default != t_loose

    def test_outcome_vocabulary(self):
        s = kept_man()
        r = run_with(s)
        assert outcome(r, "break", character="Ink") == 1.0
        assert outcome(r, "break_time", character="Ink") < float("inf")
        assert outcome(r, "peak", character="Ink", channel="heart") > 0
        assert outcome(r, "feel", character="Ink", quale="grief") >= 0
        with pytest.raises(ValueError):
            outcome(r, "no_such_outcome")

    def test_break_time_is_inf_when_the_lie_holds(self):
        s = slow_burn(conviction=0.97, breakable=None)
        r = run_with(s)
        assert outcome(r, "break_time", character="Vane") == float("inf")

    def test_debt_series_reads_the_accumulator(self):
        r = run_with(slow_burn())
        ts, ds = debt_series(r, character="Vane")
        assert len(ds) > 10
        # the debt accumulates toward the break: its max well above its start
        assert max(ds) > ds[0] + 1.0

    def test_error_series_reads_settles(self):
        r = run_with(slow_burn())
        ts, es = error_series(r, character="Vane")
        assert len(es) > 10 and all(e >= 0 for e in es)


# ---------------------------------------------------------------------------
# sensitivity: which dial writes the ending
# ---------------------------------------------------------------------------

class TestSensitivity:
    def test_conviction_outranks_an_inert_dial(self):
        """In the kept-man setup, break_time moves with conviction; overwhelm
        is inert because the lie uses `overwhelm: auto` (the dial exists but
        the run never consults it). The ranking must recover that."""
        s = kept_man()
        rep = s.sensitivity(
            params={f"{LIE}.conviction": (0.3, 0.99),
                    f"{LIE}.overwhelm": (2.0, 20.0)},
            outcome_name="break_time", character="Ink", n_base=16, seed=3)
        ranked = rep.ranked()
        assert ranked[0][0].endswith("conviction")
        assert rep.total_order[f"{LIE}.conviction"] > 0.3
        assert rep.total_order[f"{LIE}.overwhelm"] < 0.1

    def test_constant_outcome_reports_no_variance(self):
        s = kept_man()
        # 'break' is 1.0 across this whole conviction range -- constant outcome
        rep = s.sensitivity(params={f"{LIE}.conviction": (0.5, 0.6)},
                            outcome_name="break", character="Ink",
                            n_base=8, seed=0)
        assert all(v == 0.0 for v in rep.total_order.values())
        assert "constant" in " ".join(rep.notes) or rep.base_variance < 1e-9

    def test_report_renders(self):
        s = kept_man()
        rep = s.sensitivity(params={f"{LIE}.conviction": (0.3, 0.99)},
                            outcome_name="break_time", character="Ink",
                            n_base=8, seed=1)
        out = rep.render()
        assert "SENSITIVITY" in out and "conviction" in out


# ---------------------------------------------------------------------------
# discrimination: the scene that separates two readings
# ---------------------------------------------------------------------------

class TestDiscrimination:
    def _story(self):
        s = Story("the_coat", span="14s", step="1s",
                  about="a defended belief")
        c = s.character("Coat", temperament=stoic)
        c.senses("equal_regard")
        c.senses("open_contempt")
        c.believes("rank_or_surplus",
                   claim="if I am not ranked above them I am the surplus",
                   disconfirmed_by="equal_regard", breakable=True)
        c.appraises("open_contempt", as_threat=True, drives="heart",
                    to=105, fades_to=72, when="open_contempt > 4")
        return s

    def test_finds_the_separating_probe(self):
        s = self._story()
        L = "the_lie_rank_or_surplus"
        rep = s.discriminate("Coat",
                             version_a={f"{L}.conviction": 0.92},
                             version_b={f"{L}.conviction": 0.45},
                             probes={"equal_regard": [3, 6, 9],
                                     "open_contempt": [6]},
                             outcome_name="break_time")
        # the separating channel is the lie's evidence, not the threat channel
        assert rep.best[0].startswith("equal_regard")
        assert rep.best[3] > 0.2
        # contempt cannot separate readings of the *lie*: divergence 0 there
        contempt = [r for r in rep.rows if r[0].startswith("open_contempt")]
        assert all(r[3] == 0.0 for r in contempt)

    def test_qualitative_divergence_is_maximal(self):
        """When one reading breaks and the other never does, the divergence is
        1.0 -- the sharpest separation there is."""
        s = self._story()
        L = "the_lie_rank_or_surplus"
        rep = s.discriminate("Coat",
                             version_a={f"{L}.conviction": 0.99,
                                        f"{L}.learn": 0.0},
                             version_b={f"{L}.conviction": 0.3},
                             probes={"equal_regard": [4]},
                             outcome_name="break_time")
        ya, yb = rep.best[1], rep.best[2]
        if (ya == float("inf")) != (yb == float("inf")):
            assert rep.best[3] == 1.0

    def test_identical_readings_cannot_be_separated(self):
        s = self._story()
        L = "the_lie_rank_or_surplus"
        rep = s.discriminate("Coat",
                             version_a={f"{L}.conviction": 0.7},
                             version_b={f"{L}.conviction": 0.7},
                             probes={"equal_regard": [3, 6, 9]},
                             outcome_name="break_time")
        assert all(r[3] == 0.0 for r in rep.rows)
        assert "same person" in rep.render()


# ---------------------------------------------------------------------------
# early warning: the break legible before it happens
# ---------------------------------------------------------------------------

class TestEarlyWarning:
    def test_breaking_character_is_forecast_from_pre_transition_data(self):
        rep = slow_burn().predict_break_onset("Vane", window=5)
        assert rep.forecast == "break coming"
        assert rep.broke and rep.correct

    def test_held_character_is_forecast_stable(self):
        rep = slow_burn(conviction=0.97, breakable=None) \
            .predict_break_onset("Vane", window=5)
        assert rep.forecast == "stable"
        assert not rep.broke and rep.correct

    def test_forecast_uses_only_pre_transition_samples(self):
        rep = slow_burn().predict_break_onset("Vane", window=5)
        # every sample the indicators saw came strictly before the break
        assert rep.detail["n_pre"] <= rep.break_time + 1

    def test_too_short_prelude_is_ambiguous_not_guessed(self):
        s = Story("fast", span="8s", step="1s", about="a fast break")
        c = s.character("Snap", temperament=tender)
        c.senses("evidence")
        c.believes("nothing_lasts", claim="nothing lasts",
                   disconfirmed_by="evidence", breakable=True,
                   conviction=0.5)
        for t in range(1, 4):
            s.at(f"{t}s", c.hears("evidence", 9))
        rep = s.predict_break_onset("Snap", window=5)
        assert rep.forecast == "ambiguous"
        assert not rep.correct   # ambiguity never counts as a hit

    def test_render_reports_both_indicator_families(self):
        out = slow_burn().predict_break_onset("Vane", window=5).render()
        assert "variance" in out and "autocorr" in out
        # with the debt signal, the report shows the accumulator vs its bound
        assert "bound" in out

    def test_quantitative_crossing_forecast_is_close(self):
        """The strongest claim of the instrument: from pre-transition data
        alone, the predicted crossing time should land near the actual break."""
        rep = slow_burn().predict_break_onset("Vane", window=5)
        t_pred = rep.detail.get("predicted_break_time")
        assert t_pred is not None
        assert abs(t_pred - rep.break_time) <= 4.0, (t_pred, rep.break_time)

    def test_slow_climb_below_bound_is_forecast_stable(self):
        """A debt that climbs but cannot reach the bound before the horizon
        must be forecast stable -- the fix for range-normalized false alarms."""
        s = Story("faint", span="20s", step="1s", about="a faint regard")
        c = s.character("Halv", temperament=stoic)
        c.senses("visits")
        c.believes("kept_means_needed", claim="kept means needed",
                   disconfirmed_by="visits", breakable=True, conviction=0.88)
        for t in range(2, 18):
            s.at(f"{t}s", c.hears("visits", 2.3))
        rep = s.predict_break_onset("Halv", window=5)
        assert rep.forecast == "stable" and rep.correct


# ---------------------------------------------------------------------------
# counterfactual: the margin the ending turns on
# ---------------------------------------------------------------------------

class TestCounterfactual:
    def test_finds_the_dial_that_prevents_the_break(self):
        s = kept_man()
        rep = s.minimal_intervention(
            target=("break", 0.0),
            dials={f"{LIE}.conviction": (0.85, 3.0)},
            character="Ink")
        assert not rep.already_met
        assert rep.minimal is not None
        assert rep.minimal.outcome_after == 0.0
        # and the counterfactual value really is past the baseline
        assert rep.minimal.counterfactual > rep.minimal.baseline

    def test_minimal_means_smallest_normalized_displacement(self):
        s = kept_man()
        rep = s.minimal_intervention(
            target=("break", 0.0),
            dials={f"{LIE}.conviction": (0.85, 3.0),
                   f"{LIE}.learn": (0.0, 1.0)},
            character="Ink")
        if len(rep.interventions) > 1:
            rels = [iv.rel_distance for iv in rep.interventions]
            assert rels == sorted(rels)

    def test_already_met_target_is_reported_not_searched(self):
        s = kept_man()
        rep = s.minimal_intervention(
            target=("break", 1.0),          # it already breaks
            dials={f"{LIE}.conviction": (0.3, 0.99)},
            character="Ink")
        assert rep.already_met and rep.minimal is None
        assert "already meets" in rep.render()

    def test_robust_ending_reports_no_flip_as_insight(self):
        """If no dial in range flips the ending, the report must say so --
        over-determination is a finding, not a failure."""
        s = kept_man()
        rep = s.minimal_intervention(
            target=("break", 0.0),
            dials={f"{LIE}.learn": (0.02, 0.05)},   # far too weak a lever
            character="Ink")
        assert rep.minimal is None and not rep.already_met
        assert "robust" in rep.render()

    def test_break_by_deadline_target(self):
        s = slow_burn()   # breaks at 14s by default
        rep = s.minimal_intervention(
            target=("break_time", 8.0),     # make it break by 8s
            dials={"the_lie_i_did_not_matter.conviction": (0.2, 0.9)},
            character="Vane")
        if rep.minimal:
            assert rep.minimal.outcome_after <= 8.0
