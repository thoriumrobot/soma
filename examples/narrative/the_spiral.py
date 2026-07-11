"""
the_spiral: Clark's cognitive model of panic, as interoceptive inference.

Clark (1986): a panic attack is a positive feedback loop -- a bodily sensation
is catastrophically appraised as danger, the appraisal produces arousal, the
arousal produces more sensation, which confirms the appraisal. The modern
predictive-processing reading (Paulus; Seth) makes it an inference pathology: a
prior that bodily signals mean catastrophe, held with enough weight that the
body's ordinary noise becomes its own evidence.

In SOMA the circle is two verbs: a flutter drives the heart a little, and a
catastrophizing appraisal READS the heart and DRIVES the heart -- the loop
senses the very channel it raises. Everything else is prediction:

  I.    the circle vs. the shrug     same flutter, two priors: one spirals to
                                     an attack, one carries it uninterpreted
  II.   the tipping flutter          the smallest palpitation that panics --
                                     a sharp threshold, found by sweep
  III.  hysteresis                   the attack OUTLIVES its trigger: the
                                     flutter ends and the spiral self-sustains
                                     (bistability), until regulation arrives
  IV.   the exposure margin          interoceptive exposure = raising the
                                     sensation the body can carry without
                                     interpretation; the minimal tolerance
                                     that prevents the attack, computed

Every study here is hand-composed from the insight substrate (run_with +
outcome + series): no new module was needed. The substrate is the API.

    python3 examples/narrative/the_spiral.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from soma.narrative import Story, anxious, run_with, outcome, series


ATTACK = 115.0     # sustained heart above this = a panic attack, by definition


def build(*, alarm_at=88.0, flutter=6.0, flutter_beats=(3, 4),
          reassurance_at=None):
    """One person, one flutter, and a prior about what flutters mean.

    alarm_at: the heart level at which the catastrophizing appraisal engages --
              the body's tolerance for its own noise. 999 = no catastrophizing.
    flutter:  the trigger's strength.
    reassurance_at: optionally, a beat at which regulation arrives (a hand on
              the shoulder, a breath count) -- a down-driver on the same heart.
    """
    s = Story("the_spiral", span="18s", step="1s",
              about="a panic spiral and its breaking")
    p = s.character("Wren", temperament=anxious)
    p.senses("flutter")
    # the sensation: a flutter nudges the heart up -- ordinary, transient
    p.appraises("flutter", when="flutter > 3", drives="heart", to=92,
                fades_to=72, expects=0.0)
    # the circle: the appraisal that READS the heart and RAISES it. This one
    # loop is Clark's model: sensation -> catastrophic appraisal -> arousal ->
    # more sensation. Above `alarm_at`, the body's state is its own evidence.
    p.appraises("heart", as_threat=True, when=f"heart > {alarm_at}",
                drives="heart", to=132, fades_to=72,
                feeling="terror", expects=72.0)
    if reassurance_at is not None:
        p.senses("reassurance")
        p.appraises("reassurance", when="reassurance > 5",
                    drives="heart", to=68, fades_to=72, expects=0.0)
    for b in flutter_beats:
        s.at(f"{b}s", p.hears("flutter", flutter))
    if reassurance_at is not None:
        s.at(f"{reassurance_at}s", p.hears("reassurance", 8))
        s.at(f"{reassurance_at+1}s", p.hears("reassurance", 8))
    return s


def attacked(story):
    r = run_with(story)
    h = series(r, "heart", character="Wren")
    sustained = sum(1 for v in h if v >= ATTACK)
    return sustained >= 3, r


def study():
    print("=" * 74)
    print("I. THE CIRCLE VS. THE SHRUG — same flutter, two priors")
    print("=" * 74)
    got, r1 = attacked(build(alarm_at=88.0))
    h1 = [round(v) for v in series(r1, "heart", character="Wren")]
    terror = outcome(r1, "feel", character="Wren", quale="terror")
    print(f"\n  the catastrophizer (alarm at 88): heart {h1}")
    print(f"    -> ATTACK: {got}; terror fired {terror:.0f} times")
    got2, r2 = attacked(build(alarm_at=999.0))
    h2 = [round(v) for v in series(r2, "heart", character="Wren")]
    print(f"  the shrug (no catastrophic prior): heart {h2}")
    print(f"    -> attack: {got2}; the same flutter, carried uninterpreted\n")

    print("=" * 74)
    print("II. THE TIPPING FLUTTER — the smallest palpitation that panics")
    print("=" * 74)
    print()
    tip = None
    for f in [1, 2, 3, 4, 5, 6, 7, 8]:
        got, _ = attacked(build(alarm_at=88.0, flutter=float(f)))
        print(f"    flutter {f}: {'ATTACK' if got else 'passes'}")
        if got and tip is None:
            tip = f
    print(f"\n  the threshold is SHARP: below flutter {tip} nothing happens at "
          f"all; at {tip}, the")
    print("  full attack. Panic's all-or-nothing character is the signature of "
          "a system")
    print("  with two attractors and a separatrix between them, not of a dial.\n")

    print("=" * 74)
    print("III. HYSTERESIS — the attack outlives its trigger")
    print("=" * 74)
    got, r = attacked(build(alarm_at=88.0, flutter_beats=(3, 4)))
    h = series(r, "heart", character="Wren")
    t = r.times
    after_trigger = [round(v) for v, tt in zip(h, t) if tt >= 6]
    print(f"\n  the flutter ends at 5s. The heart, after: {after_trigger}")
    print("  The spiral is SELF-SUSTAINING: heart above the alarm keeps the")
    print("  appraisal firing, which keeps the heart above the alarm. Two")
    print("  stable states — rest and attack — and the flutter only chose")
    print("  between them. The way back is not the way in:")
    got_r, rr = attacked(build(alarm_at=88.0, reassurance_at=9))
    hr = [round(v) for v in series(rr, "heart", character="Wren")]
    print(f"\n  with regulation arriving at 9s: heart {hr}")
    print("  Removing the trigger did nothing; only a DOWN-driver — the")
    print("  regulation the spiral itself cannot supply — exits the attack")
    print("  state. (Cramer & Borsboom's hysteresis in symptom networks: the")
    print("  path out requires more than undoing the path in.)\n")

    print("=" * 74)
    print("IV. THE EXPOSURE MARGIN — the tolerance that prevents the attack")
    print("=" * 74)
    print()
    print("  Interoceptive exposure works by habituation: the sensation level")
    print("  the body can carry WITHOUT engaging the catastrophic appraisal")
    print("  rises. Sweeping that tolerance against the same flutter:")
    print()
    margin = None
    for alarm in [86, 88, 90, 92, 94, 96, 98]:
        got, _ = attacked(build(alarm_at=float(alarm)))
        print(f"    tolerance {alarm}: {'ATTACK' if got else 'no attack'}")
        if not got and margin is None:
            margin = alarm
    print(f"\n  THE MARGIN: tolerance {margin} is enough — the flutter peaks at "
          f"92, so the")
    print("  therapy has a computable target: teach the body to carry 92")
    print("  uninterpreted, and this trigger cannot reach the circle at all.")
    print("  The prediction is quantitative and falsifiable per-person: the")
    print("  margin is the flutter's peak, not a universal number.")


if __name__ == "__main__":
    study()
