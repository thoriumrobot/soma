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


if __name__ == "__main__":
    story = build()
    if "--source" in sys.argv:
        print(story.source())
    elif "--character" in sys.argv:
        print(story.characterize(width=84))
    else:
        print(story.run(width=88))
