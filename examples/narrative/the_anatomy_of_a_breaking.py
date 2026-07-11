"""
the_anatomy_of_a_breaking: every study instrument turned on one man.

Halvor kept the harbor ledger for thirty-one years, and believes the only
reason anyone is kept is that they are needed. His granddaughter keeps
visiting anyway -- no errand, no use for him at all -- and that useless,
persistent regard is the evidence his belief cannot metabolize.

The story is small on purpose. The point of this file is the STUDY: five
instruments, each answering a different question about the same predictive
characterization, each checked against real runs:

  I.    the run itself         what actually happens
  II.   sensitivity            which dial writes this ending (Sobol indices)
  III.  discrimination         which scene would separate two readings of him
  IV.   early warning          is the break legible before it happens
  V.    minimal intervention   what smallest change would have prevented it
  VI.   preregistration        the study's own conclusions, staked and checked

    python3 examples/narrative/the_anatomy_of_a_breaking.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from soma.narrative import Story, stoic


LIE = "the_lie_kept_means_needed"


def build(regard="rising"):
    s = Story("the_anatomy_of_a_breaking", span="20s", step="1s",
              about="a defended belief, slowly overwhelmed by regard")
    halvor = s.character("Halvor", temperament=stoic)
    halvor.senses("her_visits")
    halvor.believes("kept_means_needed",
                    claim="the only reason anyone is kept is that they are needed",
                    disconfirmed_by="her_visits", breakable=True,
                    conviction=0.88)
    halvor.learns(0.02)
    # the regard agitates the body it contradicts: visits he cannot account
    # for drive the heart, and grief is read off the heart a beat later
    halvor.appraises("her_visits", drives="heart", to=95,
                     when="her_visits > 5", fades_to=72)
    halvor.feels("grief", from_body="heart", threshold=80)
    halvor.narrates(downplaying={"grief": "It's just the cold in this office."})
    # her visits: useless regard. "rising": steady and a little warmer each
    # year (the life that breaks him). "faint": dutiful and thin -- reads at
    # almost exactly what the lie predicts, so nothing accumulates (the life
    # in which the belief is never tested hard enough to fail).
    for t in range(2, 18):
        v = (round(min(9, 3 + 0.4 * (t - 2)), 1) if regard == "rising"
             else 2.2)
        s.at(f"{t}s", halvor.hears("her_visits", v))
    return s


def study():
    print("=" * 74)
    print("I. THE RUN — what actually happens")
    print("=" * 74)
    s = build()
    r = s.result()
    revs = [e for e in r.chronicle if e.kind == "revelation"]
    print(f"\n  Halvor's lie {'BREAKS at %ds' % revs[0].t if revs else 'holds'} "
          f"under sixteen beats of useless regard.\n")

    print("=" * 74)
    print("II. SENSITIVITY — which dial writes this ending")
    print("=" * 74)
    rep = build().sensitivity(
        params={f"{LIE}.conviction": (0.4, 0.99),
                f"{LIE}.learn": (0.0, 0.15),
                f"{LIE}.precision": (0.2, 0.9)},
        outcome_name="break_time", character="Halvor", n_base=32, seed=7)
    print()
    print(rep.render())
    print()
    print("  (The heavy interaction is not noise; it is a recovered mechanism. "
          "SOMA's\n  auto-break threshold is 6*conviction/precision — a ratio, "
          "so neither dial\n  acts alone by construction. The study, given "
          "only runs, found the ratio.)")
    print()

    print("=" * 74)
    print("III. DISCRIMINATION — the scene that separates two readings")
    print("=" * 74)
    print("\n  Reading A: armor — held hard (conviction .97) and deaf to the")
    print("  evidence (precision .2): he can only suppress, until overwhelmed.")
    print("  Reading B: habit — held loosely (conviction .6), evidence trusted")
    print("  (precision .8): the senses outrank the prior, so he simply updates.")
    rep = build().discriminate(
        "Halvor",
        version_a={f"{LIE}.conviction": 0.97, f"{LIE}.precision": 0.2},
        version_b={f"{LIE}.conviction": 0.6, f"{LIE}.precision": 0.8},
        probes={"her_visits": [2, 4, 6, 9]},
        outcome_name="break_time")
    print()
    print(rep.render())
    print()
    print("  ('never' here does not mean armored: reading B never BREAKS because")
    print("  it never suppresses — the evidence wins arbitration and he changes")
    print("  his mind without a shattering. The same scene separates a man who")
    print("  breaks from a man who quietly revises.)")
    print()

    print("=" * 74)
    print("IV. EARLY WARNING — is the break legible before it happens?")
    print("=" * 74)
    print()
    print(build().predict_break_onset("Halvor", window=5).render())
    print()
    print("  ...and the same instrument on the life where her regard stays "
          "faint\n  (reads at what the lie predicts; nothing accumulates):")
    print()
    print(build(regard="faint").predict_break_onset("Halvor", window=5).render())
    print()

    print("=" * 74)
    print("V. MINIMAL INTERVENTION — what would have prevented it")
    print("=" * 74)
    rep = build().minimal_intervention(
        target=("break", 0.0),
        dials={f"{LIE}.conviction": (0.88, 3.0),
               f"{LIE}.precision": (0.05, 0.35),
               f"{LIE}.learn": (0.0, 0.02)},
        character="Halvor")
    print()
    print(rep.render())
    print()

    print("=" * 74)
    print("VI. PREREGISTRATION — the study's conclusions, staked and checked")
    print("=" * 74)
    s = build()
    audit = s.preregister()
    audit.expect_break("Halvor")
    audit.expect_feeling("Halvor", "grief")
    audit.expect_gap("Halvor", at_least=0.4)   # he downplays while it builds
    print()
    print(audit.check().render())


if __name__ == "__main__":
    study()
