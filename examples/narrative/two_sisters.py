"""
two_sisters -- the same event, two characters, and the gap between who they are.

Cleo and Immy are sisters at the reading of a will. The same words land in the
room; each makes something different of them, because each is a different person
-- and the simulation is built so that the CHARACTERIZE reading recovers the
difference the plot never states.

  * Cleo is guarded and values fairness; when the money is unequal she composes
    herself (the tell) and betrays her own stated evenhandedness -- resentment
    wearing the face of grace.
  * Immy is tender and wants closeness with her sister while fearing she is owed
    nothing; ambivalence on the same bond. She feels, openly, what Cleo manages.
  * They read each other's faces (a coupling), so Cleo's composure becomes a
    thing Immy must interpret -- and misreads, because a composed face is a lie.

The point the two-hander makes: character is relational. Run --character to see
the two portraits side by side; the reading of each only makes sense against the
other.

    python examples/narrative/two_sisters.py              # the dashboard
    python examples/narrative/two_sisters.py --character  # both portraits
    python examples/narrative/two_sisters.py --source     # the generated SOMA
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from soma.narrative import Story, guarded, tender


def build():
    story = Story("two_sisters", span="14s", step="1s",
                  about="two sisters, one will, and the selves they cannot hide")

    story.scene("The lawyer reads", frm="0s", to="5s")
    story.scene("The number lands", frm="6s", to="10s")
    story.scene("Afterward, in the car", frm="11s", to="14s")

    # --- Cleo: composed, fair in word, resentful in body -------------------
    cleo = story.character("Cleo", temperament=guarded)
    cleo.has_body_signal("composure", baseline=2)
    cleo.senses("the_number")
    cleo.appraises("the_number", as_threat=True, drives="composure", to=8,
                   feeling="apprehension", shows_on="face", shows_value=8,
                   fades_to=2, when="the_number > 5")
    cleo.values("fairness", says="I don't care about the money. I never did.",
                betrayed_when="composure > 6", on_channel="composure")
    cleo.has_mood("resentment", fed_by="apprehension", decay=0.9)
    cleo.narrates(voice={
        "apprehension": "It's fine. It's what she wanted.",
        "self_betrayal": "I'm not angry. Why would I be angry?",
    })

    # --- Immy: open, and torn about what she is owed -----------------------
    immy = story.character("Immy", temperament=tender)
    immy.wants("closeness", toward=9, strength=0.3)
    immy.fears("closeness", toward=2, strength=0.3)
    immy.reads(cleo, "face", gain=0.5, lag="1s")
    immy.appraises("cleo_face", as_threat=True, feeling="unease",
                   when="cleo_face > 3")
    immy.has_mood("hurt", fed_by="unease", decay=0.85)
    immy.narrates(voice={
        "unease": "Is she angry with me? I can't tell. I can never tell.",
    })

    # the number is read out, unequal, and it lands
    story.at("6s", cleo.hears("the_number", 9))
    story.at("8s", cleo.hears("the_number", 7))
    story.at("11s", cleo.hears("the_number", 6))
    return story


if __name__ == "__main__":
    story = build()
    if "--source" in sys.argv:
        print(story.source())
    elif "--character" in sys.argv:
        print(story.characterize(width=84))
    else:
        print(story.run(width=90))
