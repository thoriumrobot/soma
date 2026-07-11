"""
the_negotiator -- the most complete single character the library can express.

Cass runs hostage negotiations. She is, professionally, the calmest person in any
room. This simulation is built to show that the calm is a structure with a cost,
by putting every layer of the library on one person at once:

  * INTERNAL PARTS. Under pressure a loud protector ("the professional") bids for
    consciousness and wins; a quiet exile (the frightened child she once was)
    feels terror that never reaches awareness -- felt, never known.
  * THE RELATIONAL SELF. She is a different person with the man across the table
    (guarded, reading threat) than with the colleague on the radio in her ear
    (open, trusting) -- the same woman, two selves, indexed by whom she is with.
  * AMBIVALENCE. She wants the connection that would end the standoff and fears
    it in equal measure; the bond channel is pulled two ways and settles nowhere.
  * A VALUE, AND ITS BREACH. She holds "I never lie to the people I'm talking
    down" -- and breaks it every time she composes her voice into false calm.
  * CONFABULATION. The self that narrates all of this insists she is fine.

Run --character for the portrait; run the sift and the divided self is on the
page: the protector speaks, the exile is never ignited, the value is broken, the
bond is torn, and she is two people before the hour is out.

    python examples/narrative/the_negotiator.py            # the dashboard
    python examples/narrative/the_negotiator.py --character # the portrait
    python examples/narrative/the_negotiator.py --source    # the generated SOMA
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from soma.narrative import Story, guarded, tender


def build():
    story = Story("the_negotiator", span="20s", step="1s",
                  about="the cost of the calmest person in the room")

    story.scene("The call comes in", frm="0s", to="6s")
    story.scene("At the door", frm="7s", to="14s")
    story.scene("The long minute", frm="15s", to="20s")

    cass = story.character("Cass", temperament=guarded)
    # the two people she is with: the subject at the door, the colleague in her ear
    subject = story.character("Subject", temperament=tender)
    partner = story.character("Partner", temperament=tender)

    # --- the relational self: two people, from one body --------------------
    cass.with_person(subject, feeling="wariness", precision=0.85, conviction=0.3,
                     says="I hear you. I'm right here.")
    cass.with_person(partner, feeling="tenderness", precision=0.4, conviction=0.7,
                     says="Tell me you've got the back door.")

    # --- internal parts: the professional, and the child she was -----------
    cass.part("the-professional", role="protector", reacts_to="pressure",
              feeling="resolve", salience=0.95,
              says="I've done this a hundred times. Breathe. Work the problem.",
              when="pressure > 3")
    cass.part("the-child", role="exile", reacts_to="pressure",
              feeling="terror", salience=0.28, when="pressure > 3")

    # --- ambivalence: she wants the connection, and fears it ---------------
    cass.wants("rapport", toward=9, strength=0.28)
    cass.fears("rapport", toward=1, strength=0.28)

    # --- the value, and the composed voice that breaks it ------------------
    cass.has_body_signal("composed_voice", baseline=2)
    cass.appraises("pressure", as_threat=True, drives="composed_voice", to=8,
                   feeling="apprehension", when="pressure > 3", fades_to=2)
    cass.values("candor", says="I never lie to the ones I'm talking down.",
                betrayed_when="composed_voice > 6", on_channel="composed_voice")

    cass.has_mood("depletion", fed_by="apprehension", decay=0.9)
    cass.narrates(voice={
        "apprehension": "I'm fine. This is just the job.",
        "self_betrayal": "That wasn't a lie. That was the work.",
        "resolve": "Breathe. Work the problem.",
    })

    # the hour: pressure climbs, the faces come and go
    story.at("3s", cass.hears("pressure", 6), subject.shows("face", 7))
    story.at("6s", cass.hears("pressure", 8), partner.shows("face", 7))
    story.at("9s", cass.hears("pressure", 9), subject.shows("face", 8))
    story.at("12s", cass.hears("pressure", 7))
    story.at("15s", cass.hears("pressure", 9), subject.shows("face", 9))
    story.at("18s", cass.hears("pressure", 5), partner.shows("face", 6))
    return story


def predict_study():
    """Turn the portrait into forecasts. Everything below is staked before the
    run and checked against it -- the negotiator is not just described, she is
    predicted."""
    print("=" * 74)
    print("THE NEGOTIATOR, PREDICTED")
    print("=" * 74)

    # I. the tipping pressure: the least sustained pressure at which her value
    # breaks. composed_voice is driven by pressure and betrays candor above 6;
    # we sweep the pressure she faces and find the threshold.
    print("\nI. THE TIPPING PRESSURE — when the calm becomes a lie")
    from soma import run_source
    tip = None
    for p in range(1, 10):
        s = build()
        src = s.source()
        kept = [ln for ln in src.splitlines()
                if not ln.lstrip().startswith("stimulus ")]
        probe = (f"stimulus Cass.pressure {{ " +
                 "  ".join(f"at {t}s: {p}" for t in range(1, 12)) + " }")
        r = run_source("\n".join(kept + ["", probe]) + "\n",
                       title="negotiator__tip")
        betrayed = any(e.kind == "emit"
                       and "self_betrayal" in str(e.detail.get("quale", ""))
                       for e in r.chronicle)
        if betrayed and tip is None:
            tip = p
    print(f"   Cass's candor holds up to pressure {tip - 1}; at {tip}, her voice")
    print(f"   composes itself past the line and the value breaks. The calm has")
    print(f"   a precise price, and it is not infinite.")

    # II. preregistered: the exile is felt but never known
    print("\nII. THE CHILD WHO IS NEVER HEARD — a preregistered silence")
    s = build()
    audit = s.preregister()
    audit.expect_feeling("Cass", "terror")            # the exile IS felt
    audit.expect("the terror never reaches awareness (never broadcast)",
                 lambda r: (not any(e.kind == "broadcast"
                                    and "terror" in str(e.detail.get("content", "")).lower()
                                    for e in r.chronicle),
                            "no ignition of terror into the global workspace"))
    audit.expect("the professional DOES reach awareness (is broadcast)",
                 lambda r: (any(e.kind == "broadcast" for e in r.chronicle),
                            "the protector ignites"))
    print()
    print(audit.check().render())
    print("\n   Felt, never known: the terror fires all hour and never once")
    print("   ignites into consciousness, while the professional is broadcast")
    print("   again and again. That asymmetry is the exile's whole tragedy,")
    print("   and it was staked before the run.")

    # III. the breach is a SHARP transition, not a slow slide -- and what is
    # foreseeable is not the voice (which snaps) but the pressure climbing
    # toward the threshold that trips it. This is the honest early warning for
    # a threshold breach: watch the driver approach the line.
    print("\nIII. THE SHAPE OF THE BREACH — sharp, and seen coming in the pressure")
    s = build()
    src = s.source()
    kept = [ln for ln in src.splitlines()
            if not ln.lstrip().startswith("stimulus ")]
    ramp = "  ".join(f"at {t}s: {round(min(9, 0.8 * t), 1)}"
                     for t in range(1, 16))
    from soma import run_source
    r = run_source("\n".join(kept + ["", f"stimulus Cass.pressure {{ {ramp} }}"])
                   + "\n", title="negotiator__ews")
    times = r.times
    press = r.channel_hist.get("Cass.pressure", [])
    cv = r.channel_hist.get("Cass.composed_voice", [])
    betray_t = next((e.t for e in r.chronicle if e.kind == "emit"
                     and "self_betrayal" in str(e.detail.get("quale", ""))), None)
    if betray_t:
        # the voice is a step function; the pressure is the readable ramp
        p_at = [(round(t), round(p, 1)) for t, p in zip(times, press)
                if t <= betray_t]
        v_jump = [(round(t), round(v, 1)) for t, v in zip(times, cv)
                  if betray_t - 2 <= t <= betray_t + 1]
        print(f"   The composed voice does not slide toward the lie — it SNAPS:")
        print(f"   {[v for _, v in v_jump]} across the breach at {betray_t:.0f}s. The calm")
        print(f"   is intact one beat and broken the next; there is no visible")
        print(f"   wavering to catch in the voice itself.")
        print(f"   But the PRESSURE that trips it is a slow, legible climb —")
        print(f"   {[p for _, p in p_at][-6:]} — so the breach is foreseeable after all,")
        print(f"   not by watching her face but by watching the room: the")
        print(f"   threshold is fixed, and the pressure's approach to it is the")
        print(f"   early warning. (A sharp transition with a readable driver —")
        print(f"   the same structure as a fold, where the slow variable is seen")
        print(f"   coming though the jump is not.)")
    else:
        print("   Under this ramp the value holds — the pressure never reaches")
        print("   the threshold that would trip the composed voice.")


if __name__ == "__main__":
    story = build()
    if "--source" in sys.argv:
        print(story.source())
    elif "--character" in sys.argv:
        print(story.characterize(width=86))
    elif "--predict" in sys.argv:
        predict_study()
    else:
        print(story.run(width=92))
