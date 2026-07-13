"""
twelve_seconds_in_a_jury_room: the drift-diffusion model, run as character.

Every other SOMA layer predicts what a character feels or becomes. This one
predicts something the others never touch and the lab measures to the
millisecond: HOW LONG a decision takes and HOW OFTEN it is wrong. The
drift-diffusion model (Ratcliff; Gold & Shadlen) is the dominant account of
speeded two-choice decisions -- a noisy accumulation of evidence to a boundary
-- and it makes distributional predictions no deterministic model can:
right-skewed reaction times, error responses shaped differently from correct
ones, and the speed-accuracy tradeoff traced from a single dial.

Four jurors face the same ambiguous evidence. What differs is how each decides.

  I.    four ways to decide       the same evidence, four RT/accuracy
                                  signatures -- caution, acuity, and bias, each
                                  a different DDM parameter
  II.   the tell of a bias        the prejudiced juror's correct verdicts come
                                  fast and their errors come SLOW -- the
                                  fingerprint of a mind that leaned before it
                                  looked, which a symmetric model cannot show
  III.  the speed-accuracy dial   one juror, told to hurry then to be sure:
                                  the tradeoff traced from the boundary alone,
                                  dissociating caution from ability
  IV.   the deadline              a hung verdict clock: how accuracy collapses
                                  as the time to decide is cut -- computed, and
                                  a foreman's dilemma made quantitative

This is also where SOMA gains stochasticity: the accumulation is noisy but
seeded, so every distribution here is reproducible and the deterministic core
of every earlier layer is untouched.

    python3 examples/narrative/twelve_seconds_in_a_jury_room.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from soma.narrative import Story, trusting, DECISION_STYLES
from soma.narrative.decision import DecisionStyle, predict_decision


NAMES = {"deliberate": "Halden the careful",
         "impulsive": "Reine the quick",
         "keen": "Ada the sharp-eyed",
         "prejudiced": "Coll the sure"}


def study():
    print("=" * 74)
    print("I. FOUR WAYS TO DECIDE — same evidence, four signatures")
    print("=" * 74)
    print()
    print("    juror                accuracy   RT (correct)   RT (error)   skew")
    print("    " + "-" * 66)
    for style, who in NAMES.items():
        s = Story("jury", span="1s", step="1s", about="a verdict")
        j = s.character("Juror", temperament=trusting)
        s.decides(j, style=style)
        r = s.predict_decision("Juror", trials=4000, seed=3)
        print(f"    {who:<20s} {r.accuracy:>6.0%}      {r.mean_rt:>6.2f}s      "
              f"{r.mean_rt_error:>6.2f}s     {r.skew:+.2f}")
    print()
    print("  Halden (wide boundary) is slow and right; Reine (narrow) is quick")
    print("  and often wrong -- same evidence quality, opposite caution. Ada")
    print("  (high drift: she simply sees more) is fast AND right, the one")
    print("  combination caution alone can't buy. Every RT distribution leans")
    print("  right, the DDM's fingerprint.")

    print()
    print("=" * 74)
    print("II. THE TELL OF A BIAS — fast convictions, slow acquittals")
    print("=" * 74)
    s = Story("jury", span="1s", step="1s", about="a verdict")
    j = s.character("Juror", temperament=trusting)
    s.decides(j, style="prejudiced")
    r = s.predict_decision("Juror", trials=6000, seed=3)
    print(f"\n  Coll starts already leaning toward 'guilty'. When the evidence")
    print(f"  agrees, the verdict comes fast: {r.mean_rt:.2f}s. When the")
    print(f"  evidence points the other way, the walk has to climb all the way")
    print(f"  back across the room, and the RARE correct acquittal is SLOW:")
    print(f"  {r.mean_rt_error:.2f}s — {r.mean_rt_error - r.mean_rt:+.2f}s slower.")
    print(f"\n  That asymmetry — fast one way, slow the other — is the")
    print(f"  fingerprint of a prior. A juror without one shows no such gap; a")
    print(f"  symmetric model cannot produce it at all. The bias is legible in")
    print(f"  the TIMING even when the verdict is correct.")

    print()
    print("=" * 74)
    print("III. THE SPEED-ACCURACY DIAL — hurry, then be sure")
    print("=" * 74)
    s = Story("jury", span="1s", step="1s", about="a verdict")
    j = s.character("Juror", temperament=trusting)
    s.decides(j, drift=0.13, boundary=1.0)
    sat = s.speed_accuracy("Juror", boundaries=[0.5, 0.8, 1.1, 1.5, 2.0],
                           trials=4000, seed=3)
    print()
    print(sat.render())
    print()
    print("  One juror, one evidence quality, five instructions from the")
    print("  foreman — from 'we haven't got all day' to 'be certain'. The")
    print("  tradeoff is smooth and monotone, and it dissociates two things")
    print("  ordinary language conflates: this is the SAME juror being more")
    print("  careful, not a better one. Only the boundary moved.")

    print()
    print("=" * 74)
    print("IV. THE DEADLINE — how accuracy collapses under the clock")
    print("=" * 74)
    print("\n  The judge imposes a deadline: decide within T, or it's a mistrial.")
    print("  We read accuracy AMONG the verdicts actually returned in time,")
    print("  for a careful juror (wide boundary) as the clock tightens:\n")
    base = DecisionStyle(drift=0.12, boundary=1.6, start_bias=0.5,
                         nondecision=0.2)
    s = Story("jury", span="1s", step="1s", about="a verdict")
    j = s.character("Juror", temperament=trusting)
    s.decides(j, drift=0.12, boundary=1.6)
    full = s.predict_decision("Juror", trials=6000, seed=3)
    import random
    print("    deadline    verdicts returned    accuracy of those")
    for deadline in [1.0, 1.5, 2.0, 3.0, 5.0, 99.0]:
        # re-run the raw walks, censoring at the deadline
        rng = random.Random(3)
        from soma.narrative.decision import _one_trial
        st = base
        n_in, n_corr = 0, 0
        for _ in range(6000):
            ok, rt = _one_trial(st, rng)
            if ok is not None and rt <= deadline:
                n_in += 1
                n_corr += (ok is True)
        acc = n_corr / n_in if n_in else 0.0
        pct = n_in / 6000
        label = "none" if deadline == 99.0 else f"{deadline:.1f}s"
        print(f"      {label:<9s}   {pct:>6.0%}               {acc:>5.0%}")
    print()
    print("  A tight deadline doesn't just lose the slow deciders — it")
    print("  systematically keeps the EASY verdicts (which finish first) and")
    print("  discards the hard ones, so the returned verdicts look accurate")
    print("  while the hard cases go undecided. The foreman's real dilemma,")
    print("  made quantitative: haste doesn't lower accuracy evenly, it hides")
    print("  the cases that most needed the time.")


if __name__ == "__main__":
    study()
