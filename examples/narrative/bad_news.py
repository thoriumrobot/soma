"""
bad_news, in the narrative library.

The smallest complete person: a woman takes a phone call. Before she knows she is
afraid, her body is already afraid -- the heart goes first, the dread follows,
and the story she tells herself ("I'm fine, I just need to write this down")
arrives last of all, narrating a calm that isn't there.

Compare with ../bad_news.soma: this is ~10 lines of intent instead of ~40 lines
of loops and dials, and produces the same simulation. Run the sift and the body
tells on the narrator.

    python examples/narrative/bad_news.py          # the dashboard
    python examples/narrative/bad_news.py --source  # the generated SOMA
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from soma.narrative import Story, anxious


def build():
    story = Story("bad_news", span="8s", step="0.5s",
                  about="simulates acute distress")
    nadia = story.character("Nadia", temperament=anxious)

    # she hears; the words drive her heart -- but only once they land (the guard),
    # so the body's spike is an event in time, not a constant.
    nadia.senses("ear")
    nadia.appraises("ear", as_threat=True, drives="heart", to=118,
                    when="ear > 3", fades_to=70)
    # the feeling is read off the body: dread is what a racing heart means. It
    # follows the heart rather than arriving with the news -- the body knew first.
    nadia.feels("dread", from_body="heart")
    # and the self narrates a composure the body is busy contradicting.
    nadia.narrates(downplaying={
        "dread": "I'm fine. I just need to write this down."})

    # a quiet moment, then the sentence lands, then quiet she cannot return to
    story.at("2s", nadia.hears("ear", 9))
    story.at("5s", nadia.hears("ear", 2))
    return story


if __name__ == "__main__":
    story = build()
    if "--source" in sys.argv:
        print(story.source())
    else:
        print(story.run(width=88))
