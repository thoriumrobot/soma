"""
the_diplomat -- a study of a man who cannot afford to be known.

Rader is a negotiator. His whole professional self is a composed face; his whole
private self is a wanting he has spent thirty years not showing. This simulation
is built to be *read as a person*, not watched as events: run it and then call
`.characterize()` for the portrait the body's record supports.

What the simulation encodes, and what the reading should recover:
  * he WANTS to be known and FEARS it in equal measure -- ambivalence on the
    same channel, so he arrives nowhere
  * he VALUES honesty ("I would never lie to her") and breaks it every time he
    composes his face under pressure -- the gap that is his character
  * his psyche is organized to DEFEND against one feeling: longing. Every time
    it rises he suppresses it (his attention is spent elsewhere on purpose)
  * over the evening he CHANGES: he begins perceiving (taking her in) and ends
    acting (imposing his practiced calm) -- a small, measured arc

    python examples/narrative/the_diplomat.py              # the dashboard
    python examples/narrative/the_diplomat.py --character  # the PORTRAIT
    python examples/narrative/the_diplomat.py --source     # the generated SOMA
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from soma.narrative import Story, guarded


def build():
    story = Story("the_diplomat", span="18s", step="1s",
                  about="a man defended against his own longing")

    story.scene("The table", frm="0s", to="6s")
    story.scene("What she asks", frm="7s", to="12s")
    story.scene("The practiced calm", frm="13s", to="18s")

    rader = story.character("Rader", temperament=guarded)

    # the central ambivalence: he wants to be known, and fears it, at once
    rader.wants("being_known", toward=9, strength=0.28)
    rader.fears("being_known", toward=1, strength=0.28)

    # the tell: when pressed, his composure rises -- and that IS the lie, because
    # he values honesty. shows_on lets the composure register; the value watches.
    rader.has_body_signal("composure", baseline=2)
    rader.senses("her_question")
    rader.appraises("her_question", as_threat=True, drives="composure", to=8,
                    feeling="apprehension", when="her_question > 4")
    rader.values("honesty", says="I would never lie to her.",
                 betrayed_when="composure > 6", on_channel="composure")

    # the defended feeling: longing keeps rising, and he keeps spending his
    # attention elsewhere so it never reaches him. Effortful + starvation is the
    # mechanism of a man too busy holding himself together to feel what he wants.
    rader.has_attention(capacity=2)
    rader.has_body_signal("ache", baseline=3)
    rader.appraises("ache", feeling="longing", when="ache > 5", effortful=True)
    rader.appraises("her_question", feeling="wariness", effortful=True,
                    when="her_question > 2")

    rader.narrates(voice={
        "apprehension": "It's a fair question. I'll answer it in a moment.",
        "self_betrayal": "That isn't who I am. I don't do that.",
        "longing": "I'm fine. This is exactly where I want to be.",
    })

    # the evening: she asks, gently but persistently, and the ache rises under it
    story.at("3s", rader.hears("her_question", 6), rader.hears("ache", 6))
    story.at("7s", rader.hears("her_question", 8), rader.hears("ache", 7))
    story.at("10s", rader.hears("ache", 8))
    story.at("13s", rader.hears("her_question", 9), rader.hears("ache", 9))
    story.at("16s", rader.hears("her_question", 5), rader.hears("ache", 8))
    return story


def predict_study():
    """Rader, predicted: the least pressure that makes his honesty a lie, and a
    preregistered account of the longing he defends against -- felt, downplayed,
    and never allowed to change what he does."""
    from soma import run_source
    print("=" * 74)
    print("THE DIPLOMAT, PREDICTED")
    print("=" * 74)

    # I. the tipping question: how hard must she press before his composure
    # crosses the line and his honesty becomes a performance.
    print("\nI. THE TIPPING QUESTION — how close before the honest man lies")
    tip = None
    for q in range(1, 10):
        s = build()
        src = s.source()
        kept = [ln for ln in src.splitlines()
                if not ln.lstrip().startswith("stimulus ")]
        # single-character story: the channel is bare, not "Rader.<channel>"
        chan = ("her_question" if len(s.characters) == 1
                else "Rader.her_question")
        probe = (f"stimulus {chan} {{ " +
                 "  ".join(f"at {t}s: {q}" for t in range(2, 12)) + " }")
        r = run_source("\n".join(kept + ["", probe]) + "\n", title="dip__tip")
        betrayed = any(e.kind == "emit"
                       and "self_betrayal" in str(e.detail.get("quale", ""))
                       for e in r.chronicle)
        if betrayed and tip is None:
            tip = q
    print(f"   His honesty holds while she stays under {tip}; at {tip}, his")
    print(f"   composure crosses the line and the man who would never lie to her")
    print(f"   is lying with his face. The line is exact, and it is not where he")
    print(f"   thinks it is.")

    # II. preregistered: the longing is felt, downplayed, and inert -- it never
    # changes what he does (defended by design).
    print("\nII. THE DEFENDED LONGING — a preregistered suppression")
    s = build()
    audit = s.preregister()
    audit.expect_feeling("Rader", "longing")           # it IS felt
    audit.expect_gap("Rader", at_least=0.4)            # and narrated away
    audit.expect("the longing never wins arbitration (he never acts on it)",
                 lambda r: (sum(1 for e in r.chronicle
                                if e.kind == "settle"
                                and e.who.startswith("Rader.")
                                and "longing" in e.who
                                and e.detail.get("route") == "perceive") == 0,
                            "longing is felt but never routed to action"))
    print()
    print(audit.check().render())
    print("\n   The longing rises all evening and is felt every time; he names it")
    print("   away ('exactly where I want to be') and never once lets it move")
    print("   him. That is not the absence of feeling — it is the whole labor of")
    print("   a defense, and the record shows the cost the face conceals.")


if __name__ == "__main__":
    story = build()
    if "--source" in sys.argv:
        print(story.source())
    elif "--character" in sys.argv:
        print(story.characterize(width=84))
    elif "--predict" in sys.argv:
        predict_study()
    else:
        print(story.run(width=88))
