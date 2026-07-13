"""
the_vicious_cycle.py -- a disorder as an attractor of the person.

The deepest character simulations in the formal-psychopathology literature do
not model a mood; they model a PERSON as a system of interlocking feedback
loops and show that the illness is a self-sustaining *state* the system falls
into -- an attractor -- from which small nudges cannot return it. Two are
staged here, both built entirely from SOMA's ordinary verbs, both read with
the 0.17 intrapersonal instruments.

  PART ONE — PANIC (Robinaugh et al., "Advancing the Network Theory of Mental
  Disorders: A Computational Model of Panic Disorder", 2019/2024). The theory's
  engine is a VICIOUS CYCLE: bodily arousal is read as evidence of catastrophe
  (the "arousal schema" — a precision on the body-as-danger), the resulting
  perceived threat drives arousal higher, and the loop can run away into a
  panic attack. Escape behavior dampens it; a homeostatic ceiling bounds it.
  In SOMA this is three appraisals wired mouth-to-tail, and the arousal schema
  is literally the precision on the misinterpretation loop.

    I.    THE ATTACK        traces at low / high arousal schema: the same
                            stressor pulse is shrugged off by one person and
                            ignites a self-sustaining attack in the other.
    II.   THE TWO STATES    the state portrait of arousal x perceived threat:
                            a calm attractor and a panic attractor, and the
                            panic basin's share of the plane IS the person's
                            vulnerability.
    III.  THE TRAP          hysteresis: the stressor that TRIGGERS the attack
                            is not the one that RELEASES it. Once lit, the
                            attack sustains itself far below its own trigger —
                            the clinical fact that you cannot reassure someone
                            out of a panic at the level that started it.
    IV.   BURNOUT           the affine body: a finite metabolic budget makes a
                            runaway attack terminate ITSELF — exhaustion, not
                            insight, ends it. (Enforced by the interpreter's
                            affine guarantee: an action the body cannot fund
                            does not happen.)
    V.    TWO THERAPIES     therapy as a change to the landscape (bifurcation):
                            REAPPRAISAL lowers the arousal schema (raises the
                            misinterpretation threshold); EXPOSURE + response
                            prevention restores the escape/safety loop. Each is
                            a dial; the study finds the dose at which the panic
                            attractor CEASES TO EXIST.
    VI.   THE SPACE OF DAYS ensemble futures: across nearby worlds (schema and
                            stressor jittered), P(a day ends in an attack), and
                            the PIVOTAL factor — is this person's fate set by
                            their schema, or by how hard the day pushes?

  PART TWO — THE POET (Rinaldi, "Laura and Petrarch: An Intriguing Case of
  Cyclical Love Dynamics", SIAM J. Appl. Math, 1998). Some characters do not
  settle at all: their stable state is an OSCILLATION. Petrarch's twenty-year
  cycle between ecstasy and despair is a limit cycle driven by a slow
  inspiration variable. Here a poet's ardour and his inspiration are wired so
  that high ardour feeds inspiration, inspiration (slowly) cools ardour, and
  the rest state is neither ecstasy nor despair but the CYCLE between them —
  which the state portrait detects as a cyclic attractor, with an amplitude
  and a period, not a point.

Run:  python3 examples/narrative/the_vicious_cycle.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from soma.narrative import Story, anxious, tender
from soma.narrative.insight import run_with, outcome
from soma.narrative.phase import state_portrait, hysteresis
from soma.narrative.futures import futures, pivotal, by_outcome


# ---------------------------------------------------------------------------
# PART ONE — the panic system
# ---------------------------------------------------------------------------

def panic_person(schema=0.6, escape=True, budget=None, span="70s"):
    """Robinaugh's panic network in SOMA verbs.

    `schema` in [0,1] is the AROUSAL SCHEMA: how readily bodily arousal is read
    as catastrophe. It sets the misinterpretation guard (high schema = a low
    bar for the body to be read as danger). `escape` installs the dampening
    safety loop. `budget` gives the body a finite metabolic reserve, so a
    runaway attack can exhaust itself.
    """
    guard = round(85 - 50 * schema)     # arousal schema -> misinterpretation bar
    s = Story("panic", span=span, step="1s", about="acute distress")
    p = s.character("Noa", temperament=anxious)
    if budget is not None:
        p.has_budget(budget)
    p.senses("stressor", baseline=0.0)

    # a stressful event raises the body
    p.appraises("stressor", as_threat=True, when="stressor > 4",
                drives="arousal", to=70, fades_to=20, expects=0.0,
                precision=0.9, conviction=0.2)

    # THE MISINTERPRETATION: bodily arousal read as catastrophe -> threat.
    # the schema is the guard: how high arousal must climb to be misread.
    p.appraises("arousal", as_threat=True, when=f"arousal > {guard}",
                feeling="dread", drives="perceived_threat", to=90, fades_to=5,
                expects=20.0, precision=0.9, conviction=0.3)

    if escape:
        # ESCAPE / SAFETY, declared BETWEEN the misinterpretation and the
        # terror loop, so within each frame it intercepts the alarm before it
        # feeds back to the body: flee / sit / breathe, collapsing the
        # catastrophic reading. (Note it never registers in the feeling
        # record: its own act erases its trigger before the emit re-checks —
        # safety behavior as something habitual and unfelt.)
        p.appraises("perceived_threat", when="perceived_threat > 80",
                    feeling="flees", drives="perceived_threat", to=5,
                    expects=5.0, precision=0.95, conviction=0.2)

    # THE RETURN ARC: perceived threat drives arousal higher (the vicious
    # cycle closes). Its drive is gated on the metabolic budget (spend_first),
    # so an attack the body can no longer fund starves.
    p.appraises("perceived_threat", as_threat=True, when="perceived_threat > 50",
                feeling="terror", drives="arousal", to=95, fades_to=20,
                expects=5.0, precision=0.9, conviction=0.3, spend_first=True)
    return s


def stressor_pulse(s, t0=5, n=3, v=8):
    c = s.characters[0]
    for i in range(n):
        s.at(f"{t0+i}s", c.hears("stressor", v))
    s.at(f"{t0+n}s", c.hears("stressor", 0))
    return s


def _arousal_trace(s, width=30):
    r = run_with(stressor_pulse(s))
    ar = r.channel_hist.get("arousal", [])
    return " ".join(f"{v:>2.0f}" for v in ar[:width])


def part_one():
    print("#" * 74)
    print("# PART ONE — PANIC: the disorder as an attractor of the person")
    print("#" * 74)

    print("\n" + "=" * 74)
    print("I. THE ATTACK — the same stressor, two people")
    print("=" * 74)
    print("  A pulse of stress at t=5–7 (identical for both). Arousal over the "
          "next 30s:")
    print(f"\n  low schema (0.2):  {_arousal_trace(panic_person(schema=0.2))}")
    print(f"  high schema (0.8): {_arousal_trace(panic_person(schema=0.8))}")
    print("\n  The low-schema person's arousal rises and settles. The "
          "high-schema person's")
    print("  body crosses its own misinterpretation bar, and the cycle takes "
          "over: the")
    print("  stressor is long gone, but arousal stays pinned high. The attack "
          "is now")
    print("  self-supplying — a state, not a response.")

    print("\n" + "=" * 74)
    print("II. THE TWO STATES — arousal × perceived threat, as a landscape")
    print("=" * 74)
    port = state_portrait(panic_person(schema=0.85, escape=False),
                          "Noa", ("arousal", "perceived_threat"),
                          grid=5, lo=0, hi=100, beats=26,
                          high_label="panic", low_label="calm",
                          healthy_is="low")
    print(port.render())
    print(f"\n  The panic basin holds {1 - port.healthy_share:.0%} of the "
          f"plane. That number is")
    print("  the person's vulnerability, drawn as a region: the fraction of "
          "inner states")
    print("  from which they fall into an attack rather than back to calm.")

    print("\n" + "=" * 74)
    print("III. THE TRAP — the trigger is not the release (hysteresis)")
    print("=" * 74)
    h = hysteresis(panic_person(schema=0.85, escape=False), "Noa",
                   "stressor", "arousal",
                   levels=[0, 2, 4, 5, 6, 7, 8, 9], dwell=5)
    print(h.render())
    print("\n  This is the clinical fact made mechanical: you cannot reassure "
          "someone out")
    print("  of a panic at the stressor level that started it. The attack has "
          "its own")
    print("  memory — dynamical, not stored — and it lives below its own "
          "trigger.")

    print("\n" + "=" * 74)
    print("IV. BURNOUT — a finite body ends the attack it cannot fund")
    print("=" * 74)
    s = stressor_pulse(panic_person(schema=0.85, escape=False, budget=120))
    r = run_with(s)
    ar = r.channel_hist.get("arousal", [])
    insolvent = [e.t for e in r.chronicle if e.kind == "budget"]
    print(f"  arousal: {' '.join(f'{v:>2.0f}' for v in ar[:34])}")
    print(f"  the body's reserve runs dry at t={insolvent[0]:.0f}s; from there "
          f"terror can no")
    print("  longer fund its drive on the body, and the attack decays on its "
          "own. What")
    print("  ends it is exhaustion, not insight — the affine body, enforced at "
          "the act.")

    print("\n" + "=" * 74)
    print("V. TWO THERAPIES — each dissolves the attractor, differently")
    print("=" * 74)
    print("  REAPPRAISAL (raising the bar at which the body is read as danger):")
    for schema in (0.85, 0.6, 0.4, 0.2):
        port = state_portrait(panic_person(schema=schema, escape=False),
                              "Noa", ("arousal", "perceived_threat"),
                              grid=5, lo=0, hi=100, beats=24,
                              high_label="panic", low_label="calm",
                              healthy_is="low")
        panic_share = 1 - port.healthy_share
        bar = "█" * round(panic_share * 20)
        gone = "  <- panic attractor GONE" if panic_share == 0 else ""
        print(f"    schema {schema:.2f}: panic basin {panic_share:>4.0%} "
              f"{bar}{gone}")
    print("\n  THE SEDUCTION OF SAFETY — why escape behavior is learned:")
    for esc in (False, True):
        port = state_portrait(panic_person(schema=0.85, escape=esc),
                              "Noa", ("arousal", "perceived_threat"),
                              grid=5, lo=0, hi=100, beats=24,
                              high_label="panic", low_label="calm",
                              healthy_is="low")
        panic_share = 1 - port.healthy_share
        label = "with escape/safety" if esc else "no safety behavior"
        print(f"    {label:<22}: panic basin {panic_share:>4.0%} "
              + "█" * round(panic_share * 20))
    print("\n  Reappraisal is the therapy: it shrinks the panic basin by moving "
          "the")
    print("  threshold at which the body is misread, until the attractor "
          "ceases to")
    print("  exist — a bifurcation. The escape row shows something different "
          "and more")
    print("  uncomfortable: safety behavior ABOLISHES the acute attack, which "
          "is exactly")
    print("  why it is so powerfully reinforced — and why, per the theory, it "
          "quietly")
    print("  maintains the schema by preventing its disconfirmation (a slow "
          "arc this")
    print("  study does not model). The acute benefit and the chronic cost "
          "are the")
    print("  same loop.")

    print("\n" + "=" * 74)
    print("VI. THE SPACE OF DAYS — is the fate the schema, or the day?")
    print("=" * 74)

    def attack_classifier(result):
        ar = result.channel_hist.get("arousal", [])
        tail = ar[-10:] if len(ar) >= 10 else ar
        peaked = max(ar) >= 85 if ar else False
        stuck = (sum(tail) / len(tail)) >= 60 if tail else False
        return "attack" if (peaked and stuck) else "settles"

    def build_day(schema, push):
        s = panic_person(schema=schema, escape=False)
        c = s.characters[0]
        for i in range(3):
            s.at(f"{5+i}s", c.hears("stressor", push))
        s.at("8s", c.hears("stressor", 0))
        return s

    # sweep by drawing schema and push per replicate, building the day inside
    import random
    rng = random.Random(11)
    runs = []
    for _ in range(40):
        schema = round(rng.uniform(0.2, 0.9), 3)
        push = round(rng.uniform(5.0, 9.0), 3)
        r = run_with(build_day(schema, push))
        runs.append({"schema": schema, "push": push,
                     "ending": attack_classifier(r)})
    n = len(runs)
    p_attack = sum(1 for r in runs if r["ending"] == "attack") / n
    # pivotal: Cohen's d of each factor between attack and settle worlds
    import math

    def d(factor):
        xs = [r[factor] for r in runs if r["ending"] == "attack"]
        ys = [r[factor] for r in runs if r["ending"] != "attack"]
        if not xs or not ys:
            return 0.0
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        vx = sum((x - mx) ** 2 for x in xs) / max(1, len(xs) - 1)
        vy = sum((y - my) ** 2 for y in ys) / max(1, len(ys) - 1)
        sp = math.sqrt(((len(xs) - 1) * vx + (len(ys) - 1) * vy)
                       / max(1, n - 2)) or 1e-9
        return (mx - my) / sp

    print(f"  across {n} nearby days: P(attack) = {p_attack:.0%}")
    print(f"  pivotal factor — schema: d={d('schema'):+.2f}   "
          f"push (how hard the day): d={d('push'):+.2f}")
    print("\n  The schema separates the attack-days from the calm ones far more "
          "than the")
    print("  day's severity does: this person's panic is carried in how they "
          "read their")
    print("  body, not in how hard the world pushes. Two people, same week — "
          "different")
    print("  illnesses.")


# ---------------------------------------------------------------------------
# PART TWO — the poet's limit cycle
# ---------------------------------------------------------------------------

def poet():
    """Rinaldi's slow-fast love cycle in SOMA verbs. Ardour (fast) and
    inspiration (slow) are wired so that ardour feeds inspiration and
    inspiration cools ardour with a lag — a negative feedback with delay,
    whose stable state is neither ecstasy nor despair but the OSCILLATION
    between them."""
    s = Story("the_poet", span="80s", step="1s", about="the erosion of intimacy")
    p = s.character("Petrarch", temperament=tender)
    # the crucial tuning of a relaxation oscillator: the RESTING ardour (60)
    # sits ABOVE the rapture line (55), so every recovery from a crash
    # re-crosses the trigger and the cycle re-arms itself, forever.
    p.has_body_signal("ardour", baseline=60)
    p.has_body_signal("inspiration", baseline=25)
    # the muse feeds on longing (the fast up-arc)
    p.appraises("ardour", when="ardour > 55", feeling="rapture",
                drives="inspiration", to=90, fades_to=25, expects=60.0,
                precision=0.6, conviction=0.2)
    # the poem written, the longing spent (the crash); ardour rests high
    p.appraises("inspiration", as_threat=True, when="inspiration > 70",
                feeling="despair", drives="ardour", to=15, fades_to=60,
                expects=25.0, precision=0.6, conviction=0.2)
    return s


def part_two():
    print("\n\n" + "#" * 74)
    print("# PART TWO — THE POET: a stable state that is an oscillation")
    print("#" * 74)
    s = poet()
    # nudge the cycle into motion
    s.at("3s", s.characters[0].hears("ardour", 75))
    r = run_with(s)
    ard = r.channel_hist.get("ardour", [])
    print("\n  Petrarch's ardour over 40 beats (nudged once, at t=3):")
    print(f"  {' '.join(f'{v:>2.0f}' for v in ard[:40])}")
    print("\n" + "=" * 74)
    print("THE CYCLE AS THE ATTRACTOR — ardour × inspiration")
    print("=" * 74)
    port = state_portrait(poet(), "Petrarch", ("ardour", "inspiration"),
                          grid=5, lo=10, hi=90, beats=48,
                          high_label="ecstasy", low_label="despair",
                          healthy_is=None, osc_tol=12)
    print(port.render())
    cyclic = [at for at in port.attractors if at.cyclic]
    if cyclic:
        c = cyclic[0]
        print(f"\n  The rest state is a CYCLE, not a point: ardour swings "
              f"±{c.amplitude/2:.0f}")
        print(f"  with a period of ~{c.period:.0f} beats. Petrarch does not "
              f"settle into love or")
        print("  out of it — the oscillation between ecstasy and despair IS his "
              "steady")
        print("  state, exactly as Jones read it in the Canzoniere and Rinaldi "
              "modeled it.")
    else:
        print("\n  (No cyclic attractor detected at this resolution.)")


if __name__ == "__main__":
    part_one()
    part_two()
