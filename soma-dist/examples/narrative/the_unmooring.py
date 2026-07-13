"""
THE UNMOORING -- the characters of the novel, modeled in soma.narrative.

This is the library's answer to a working novelist's real problem: not "what
happens" but "who is this person, mechanically, so that the plot's choices land
as character and not as authorial convenience." Each study below builds one of
the book's people (or one of its social machines) out of loops, and the sift
recovers the characterization the prose spent chapters earning.

Four of the studies lean on primitives added for this book:

  * craves(...)          -- a hunger fed by a supply the world can withdraw or
                            wipe. Blade's rank, erased by the tide-clean each
                            night; Ink's same hunger, fed instead by reading,
                            which does not erase. The one difference between the
                            spare who takes the ladder and the spare who does not.
  * tended_by(...)       -- co-regulation. Rover's biscuit in the Combs: a steady
                            presence that turns down the trust in an alarm without
                            touching the belief. The book's whole thesis about how
                            one person frees another -- not argument, presence.
  * holds_with_others()  -- confidence as belief about other people's belief. The
                            doctrine on the perches, the run on war-paper at
                            Greywater: a thing everyone holds only because everyone
                            is seen to hold it, and its cascade when one lets go.
  * hollowed             -- the subtracted self: the keeper of names worn to her
                            rounds, the captain in the mist who cannot tell shown
                            from so.

Run any study:
    python the_unmooring.py [fleet|ring|combs|greywater|selm] [--source|--character|--prose|--sift]
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from soma.narrative import (Story, guarded, stoic, volatile, tender, anxious,
                            hollowed)


# ---------------------------------------------------------------------------
# THE FLEET -- Ink and Sound, the dyad at the center of the book
# ---------------------------------------------------------------------------
def build():
    """Ink and his sister Sound: the spare who reads, and the diver who reads
    the water. The two protagonists, each with a full interior.

    Ink carries 'a small starved animal that has never stopped asking whether I
    mattered' -- a hunger the book names outright. The Mender fed it with reading;
    Blade will feed the same hunger with the ring's rank. Here it is fed by
    reading, which (unlike rank) does not erase, so it quiets and stays quiet:
    the whole difference between the spare who stays and the spare who leaves.
    Ink also holds one hard value -- never wield unchecked discretion -- and the
    'reasonable warm voice that loves me' tempts him to break it at the founding.

    Sound reads the weight under the surface and refuses to be 'a saint -- a tool
    with candles on it.' She wants one thing, small: a boat nobody's life hangs
    on, out on a slack tide for no reason. The world will not let her have it; it
    wants her hands. So the want goes unfed, the way Ink's hunger would have gone
    unfed without a book."""
    s = Story("the_fleet", span="18s", step="1s",
              about="the spare who reads, and the diver who reads the water")

    ink = s.character("Ink", temperament=guarded)
    sound = s.character("Sound", temperament=stoic)

    # Ink's hunger, fed by reading -- and, crucially, NOT erased. It quiets.
    ink.craves("to_matter", fed_by="reading", feeling="worthlessness",
               fed_feeling="recognition", erased=0.0, threshold=5,
               says="Do I matter, or am I the one the family could afford to lose?")
    # the one value he will not break -- and the warm voice that tempts him to.
    ink.values("checked_hands", says="Never a kind hand unchecked over anyone.",
               betrayed_when="discretion > 6", on_channel="discretion")
    ink.part("the-reasonable-voice", role="tempter", reacts_to="discretion",
             feeling="longing", salience=0.8,
             says="You know how it works better than any of them. Take the pen.",
             when="discretion > 6")
    ink.with_person(sound, feeling="tenderness", precision=0.9, conviction=0.2)
    ink.narrates(voice={
        "worthlessness": "I read too much and dove too little. The spare.",
        "recognition": "Show me the rope.",
        "self_betrayal": "That isn't who I am. That isn't who I am.",
    })
    # the wound under the hunger, the lie it taught, and the need the story is
    # really about. The spare learned that he mattered only while he was needed --
    # so the pen, the indispensable hand, is the want the lie generates. The
    # evidence against it is every moment he is kept for nothing (fed, named,
    # loved without holding anything over anyone). It is breakable: at the founding
    # the weight of it overwhelms the lie and he refuses the pen -- the self-
    # revelation, and the whole difference between him and Blade and the Provost.
    ink.wounded_by("the spare -- read too much, dove too little, the one the "
                   "family could afford to lose", teaches="only-the-needed-matter")
    ink.believes("only-the-needed-matter",
                 claim="I matter only while I am the indispensable hand -- the "
                       "one who holds the pen.",
                 disconfirmed_by="kept_for_nothing", feeling="worthlessness",
                 harms="others", conviction=0.95, breakable=True,
                 says="Who could be trusted with the pen more than the man who "
                      "was in the hole?")
    ink.needs("to-be-kept-for-nothing", opposes="only-the-needed-matter",
              feeling="worthlessness", fed_feeling="recognition")

    # Sound reads the weight under things, and checks her own reading (updates).
    sound.has_body_signal("the_water", baseline=0)
    sound.appraises("the_water", feeling="foreboding", updates=True,
                    when="the_water > 4")
    # the one thing she wants, and never gets: a boat that is hers, for nothing.
    # A craving whose supply (an idle slack tide) never comes -- so it aches, and
    # is never fed, because the world wants her hands, not her rest.
    sound.craves("own_boat", fed_by="slack_tide", feeling="longing",
                 erased=0.0, threshold=5,
                 says="A boat. Small. Six boards and a sail. Qu wa'. For nothing.")
    sound.with_person(ink, feeling="tenderness", precision=0.85, conviction=0.3)
    sound.narrates(voice={
        "foreboding": "Don't make it a lesson yet. Let it be heavy for a night.",
        "longing": "A boat. Small. Six boards and a sail. Qu wa'. For nothing.",
    })

    # the voyage. Ink reads (the hunger fed) until the founding, when the pen is
    # in reach and discretion rises -- the value tested, the warm voice bidding.
    for t in [2, 4, 6, 8]:
        s.at(f"{t}s", ink.hears("reading", 9))         # the Mender's book, the record
    for t in [11, 13, 15]:
        s.at(f"{t}s", ink.hears("discretion", 9))      # the founding: the pen in reach
    # kept for nothing: fed, named, loved without holding anything over anyone --
    # faint at first, strongest at the founding, where it finally breaks the lie.
    for t, v in [("2s", 4), ("5s", 5), ("8s", 6), ("11s", 8), ("14s", 9), ("16s", 9)]:
        s.at(t, ink.hears("kept_for_nothing", v))
    # Sound reads hard water the whole way; her want is never supplied.
    for t in [3, 6, 9, 12, 15]:
        s.at(f"{t}s", sound.hears("the_water", 8))
    return s


# ---------------------------------------------------------------------------
# THE RING -- Blade, the spare who takes the ladder (craves + erasure)
# ---------------------------------------------------------------------------
def build_ring():
    """Blade in the Blood. He is 'genuinely, gloriously good' -- quick, brave past
    sense, first over any rail -- and the Articles he swore give him no way to be
    *more* than the bilge-boy. The ring does: it supplies a rank. But the
    tide-clean wipes the fighting-floor every night, so the rank he won at dawn is
    gone by the next tide and he must win it again -- the ring 'sells the feeling
    of a rank and erases the rank while you sleep.'

    He is not a fool or a traitor; he is a divided man. A loud protector -- the
    one who is first through the smoke -- and, under it, the same small starved
    animal Ink carries, the one that has never stopped asking whether he mattered,
    which the injury-scale refused to feed and the ring finally does. He signed
    the Articles and meant it ('if the fleet's ever aground I'll be first in the
    water') and the same week began straining against them. The sift should
    recover all of it: the wiped hunger, the brave self that speaks and the
    starved self that never gets heard, the arc from pride to worthlessness, and
    the fair share he swore and could not live inside."""
    s = Story("blade_in_the_blood", span="22s", step="1s",
              about="a hunger the ring feeds and the tide erases")
    blade = s.character("Blade", temperament=volatile)

    # the wiped hunger -- fed by the ring's rank, erased nightly by the tide-clean
    blade.craves("to_matter", fed_by="rank", feeling="worthlessness",
                 fed_feeling="pride", erased=0.9, threshold=5,
                 says="I'm first through the smoke. What do I get that the bilge-boy doesn't?")

    # the divided self: the brave first-over-the-rail protector is loud; the
    # spare animal that only wants to matter is quiet, and never gets heard.
    blade.part("first-over-the-rail", role="protector", reacts_to="rank",
               feeling="pride", salience=0.9, when="rank > 3",
               says="Wet first, every time. You all saw that.")
    blade.part("the-spare-animal", role="exile", reacts_to="the_scale",
               feeling="worthlessness", salience=0.2, when="the_scale > 3",
               says="Same share. Same vote. As if I were the boy pumping bilge.")

    # the value he swore and strains: a fair share, no upstairs -- and the ache
    # of needing one crosses its own line whenever the scale is put to him.
    blade.values("the_fair_share", says="I signed it and I meant it. First in the water, always.",
                 betrayed_when="the_scale > 5", on_channel="the_scale")

    blade.narrates(voice={
        "worthlessness": "Some of us need there to be an upstairs.",
        "pride": "You built a home with no upstairs. I can't live in it.",
        "self_betrayal": "I signed it and I meant it. And I can't stay.",
    })

    # Under the wiped hunger sits the wound that installed it, the lie it taught,
    # and the need the lie will not let him reach. The fleet treats him as an
    # equal -- the fair share, the equal vote -- which is exactly the evidence his
    # lie must suppress, because if the equal share is enough, he is not surplus,
    # and he cannot believe that. He is not breakable here: met with the evidence,
    # he doubles down and takes the ladder. The tragic arc, and the fleet loses him.
    blade.wounded_by("the injury-scale that priced him in advance, and gave him "
                     "no way to be worth more than the boy pumping bilge",
                     teaches="only-rank-makes-me-real")
    blade.believes("only-rank-makes-me-real",
                   claim="If I'm not ranked above them, I'm the surplus again.",
                   disconfirmed_by="equal_regard", feeling="worthlessness",
                   harms="others", breakable=None,
                   says="Some of us need there to be an upstairs.")
    blade.needs("to-matter-as-an-equal", opposes="only-rank-makes-me-real",
                feeling="worthlessness", fed_feeling="belonging")

    # he wins at dawn (rank supplied), the tide wipes it; and across it all the
    # fair-share scale keeps being held up to him, and keeps not being enough.
    for t in [2, 9, 16]:                 # the crowd's grade, at dawn
        s.at(f"{t}s", blade.hears("rank", 9))
    for t in [5, 12, 19]:                # the tide-clean, by nightfall
        s.at(f"{t}s", blade.hears("rank", 0))
    for t in [4, 8, 11, 15, 18]:         # the Articles' fair scale, put to him
        s.at(f"{t}s", blade.hears("the_scale", 8))
    # the fleet's equal regard, offered again and again -- the evidence the lie
    # must suppress. He never lets it in; it only hardens the belief.
    for t in [3, 7, 10, 13, 17, 20]:
        s.at(f"{t}s", blade.hears("equal_regard", 8))
    return s


# ---------------------------------------------------------------------------
# THE COMBS -- Topman, brought back by Rover, not argued back (tended_by)
# ---------------------------------------------------------------------------
def build_combs():
    """Topman lost his wife and both children in the crush at the Maw and held
    the fleet's course steady from aloft while it happened. His grief floods. The
    Hive offers 'an end to carrying it,' and Ink -- who believes if you make a
    person see the machine they will walk out of it -- argues, and it is exactly
    wrong: 'you cannot argue a person out of the one place their dead have stopped
    dying.' Rover does the other thing. He fills a kit-bag with biscuit, sits down
    in the golden hush, and is a true thing from the true world within reach until
    the true world has a thread in it again.

    So: Topman's grief is not argued away (the belief is never touched); it is
    that, once Rover is present and steady, the trust placed in the alarm falls
    and it stops flooding. Presence, not persuasion -- the book's whole thesis,
    and the recovery-watch the fleet built out of it: no one alone in the dark."""
    s = Story("the_combs", span="16s", step="1s",
              about="grief quieted by a steady presence, not an argument")
    topman = s.character("Topman", temperament=anxious)
    rover = s.character("Rover", temperament=stoic)

    topman.has_body_signal("the_children", baseline=0)
    topman.appraises("the_children", as_threat=True, feeling="grief",
                     when="the_children > 4")
    rover.steadies()                                   # present when he sits down
    topman.tended_by(rover, calms="the_children", strength=0.85)
    topman.narrates(voice={"grief": "In here, the children stopped drowning."})
    rover.narrates(voice={"calm": "Your boat leaked, though."})

    # the grief is there the whole time; Rover comes and sits on the third day.
    for t in range(2, 16):
        s.at(f"{t}s", topman.hears("the_children", 9))
    for t in range(8, 16):
        s.at(f"{t}s", rover.present())
    return s


# ---------------------------------------------------------------------------
# GREYWATER -- the run: confidence as belief about others' belief
# ---------------------------------------------------------------------------
def build_greywater():
    """The climax's engine. War-paper is 'sound' because every house is seen to
    treat it as sound -- confidence, in the book's exact sense: belief about other
    people's belief. Truth alone cannot move it ('everyone knew the house was
    rotten... each was waiting to see what the others would do'). What moves it is
    one man, Venn, willing to be first at counting in public.

    So the run here is not sprung by an outside shock -- it is sprung by a
    character. Venn actually reads the paper (an appraisal that checks, and
    updates), and when the arithmetic comes up rotten his own reading -- not the
    crowd's -- tips him out of the belief. The other four never read the paper at
    all; they read each other, and hold until they see Venn go. He does not do it
    for anyone; he does it because he can count, and because he is the one man in
    the hall willing to be first at counting out loud. Then confidence, which
    stood six days against the truth, cannot stand one hour against the sight of
    one man acting on it: nothing, nothing, then everything at once."""
    s = Story("greywater", span="20s", step="1s",
              about="confidence, and the one man willing to count first")
    names = ["Venn", "Marl", "Osset", "Perrit", "Quill"]
    banks = [s.character(n, temperament=guarded) for n in names]
    for b in banks:
        b.holds_with_others(
            "paper_is_sound", field_tag="holds", believing=10,
            says="Sound as the day is long. Everyone says so.")

    # Venn alone reads the actual paper, and checks it (updates). When the rot is
    # plain, his reading drives his own doubt -- and that, not any outside shock,
    # is what unmoors the whole hall. He is the first mover because he counts.
    venn = banks[0]
    venn.has_body_signal("the_paper", baseline=0)
    venn.appraises("the_paper", feeling="foreboding", updates=True,
                   when="the_paper > 5",
                   drives="paper_is_sound_doubt", to=1)
    venn.narrates(voice={
        "foreboding": "They sell to both sides. So some day they are on the other side of me too.",
    })

    # Quill is the tragedy of the hall. He reads the very same rot -- he KNOWS --
    # and holds anyway, because knowing is not the thing that moves a market:
    # belief about other people's belief is. He does not drive his own doubt; his
    # grip only breaks when he sees Venn's break, on the field, with the rest.
    quill = banks[-1]
    quill.has_body_signal("the_paper", baseline=0)
    quill.appraises("the_paper", feeling="foreboding", when="the_paper > 5")
    quill.narrates(voice={
        "foreboding": "I know. I can read. And I am so tired. Sound as the day is long.",
    })
    # both men have the rot in front of them the whole time; one counts it, one
    # only reads it and waits.
    for t in [4, 6, 8, 10]:
        s.at(f"{t}s", venn.hears("the_paper", 8))
    for t in [4, 6, 8, 10, 12, 14]:
        s.at(f"{t}s", quill.hears("the_paper", 8))
    return s


# ---------------------------------------------------------------------------
# SELM -- the Provost: the clerk who checked, and then stopped (value + fork)
# ---------------------------------------------------------------------------
def build_selm():
    """Enner Selm, senior clerk of the copper desk, later Provost of the whole
    Ledger. Thirty years ago he checked the house's holiest arithmetic against
    the truth, found it rotten, and wrote the true figure in the margin three
    times -- and then never again. 'The initialing goes on for years. But the
    checking stops.' He is Ink at the same fork, gone the other way: the young
    clerk who saw is a part of him that once reached awareness and never ignites
    again, and the value he holds -- accuracy, the true sum -- he now breaks with
    every filing, in the seize-and-keep form.

    The sift should recover both: a value broken, and, defended against, the
    feeling carried by the part that no longer gets heard -- the honesty he sat
    with a knife-eraser one night and could not quite cut out."""
    s = Story("the_provost", span="16s", step="1s",
              about="the clerk who checked the arithmetic, and then stopped")
    selm = s.character("Selm", temperament=guarded)
    # the value he holds and breaks: the true figure, filed false under pressure
    selm.values("the_true_sum", says="I would audit the tide if it came in a minute short.",
                betrayed_when="pressure > 5", on_channel="pressure")
    # the young clerk who saw -- a part that bids and, drowned by the house, never
    # ignites again. Its feeling (honesty-as-grief) is what he defends against.
    selm.part("the-young-clerk", role="exile", reacts_to="the_margin",
              feeling="grief", salience=0.2, when="the_margin > 3",
              says="Somebody checked this once. It was me.")
    selm.part("the-house", role="protector", reacts_to="pressure",
              feeling="resolve", salience=0.95, when="pressure > 3",
              says="The prisons are lawful. The seal says so.")
    selm.narrates(voice={
        "self_betrayal": "The doctrine is a roof. A roof need not be true.",
        "grief": "I sat with a knife-eraser one night. I couldn't.",
    })
    # the wound, the lie, the need. Selm is Ink at the same fork gone the other
    # way: the lie 'a roof need not be true' let him rule a machine that
    # disappears people (a moral weakness). The evidence against it is his own
    # young hand in the margin -- the true sums he once wrote and made himself
    # stop writing. He is breakable, but only just, and only late: the margin has
    # to be held up to him in person before the weight finally overwhelms it, and
    # even then what breaks is a pencil-stroke, not a life. The self-revelation
    # that comes too late to undo anything, which is its own kind of tragedy.
    selm.wounded_by("the night with the knife-eraser -- he checked the house's "
                    "holiest arithmetic three times, found it rotten, and then "
                    "made himself stop", teaches="the-roof-need-not-be-true")
    selm.believes("the-roof-need-not-be-true",
                  claim="The doctrine is a roof, and a roof need not be true to "
                        "keep the weather off the beams.",
                  disconfirmed_by="the_margin", feeling="grief", harms="others",
                  conviction=1.5, breakable=True,
                  says="The prisons are lawful. The seal says so.")
    selm.needs("to-write-the-true-sum-again", opposes="the-roof-need-not-be-true",
               feeling="grief", fed_feeling="honesty")
    for t in [3, 6, 9, 12, 15]:
        s.at(f"{t}s", selm.hears("pressure", 8))       # the house leaning on him
    # the old true sums, resurfacing -- faint at first, then held up to him in
    # person at the parley (the last, largest), which is what finally breaks it.
    for t, v in [("4s", 6), ("8s", 7), ("11s", 8), ("14s", 9), ("16s", 9)]:
        s.at(t, selm.hears("the_margin", v))
    return s


# ---------------------------------------------------------------------------
# THE COAT -- a Rafter in the Ledger's coat; the fourth carrier of the hunger
# ---------------------------------------------------------------------------
def build_coat():
    """The Coat carries the same to-matter hunger as Ink and Blade, but his
    supply is the house's coat-and-number -- the one thing that stops him being
    'surplus', the word his whole struck-off people were declared. Unlike Blade's
    rank (wiped nightly by the tide-clean), the coat is a *steady* supply -- until
    the house collapses and puts him ashore, 'a number in a collar it no longer
    needed', and withdraws it all at once. Then, at the Eel Cage gate, he feeds
    the hunger himself: eleven days holding a door, unpaid, ungraded, by his own
    choice -- the same want, met at last by an act the house cannot own.

    Under the coat is the Rafter who curses in the warm deck-tongue when he nearly
    drowns -- an exile that never gets heard while the house's man wears the forms.
    The sift should show one hunger fed by two very different supplies: the house's
    (withdrawable) and his own (his to keep)."""
    s = Story("the_coat", span="20s", step="1s",
              about="a hunger fed by the house's coat, then by his own hands")
    coat = s.character("Coat", temperament=guarded)

    # one hunger, fed_by 'belonging' -- driven first by the house's coat, later by
    # the gate he chooses to hold. Not erased nightly (a steady supply, not a ring).
    coat.craves("to_matter", fed_by="belonging", feeling="surplus",
                fed_feeling="placed", erased=0.1, threshold=5,
                says="It's a good coat. It's warm.")

    # the house's man wears the forms and gets a voice; the Rafter under the coat
    # is the exile -- heard only as a curse in the warm tongue when he is drowning.
    coat.part("the-houses-man", role="protector", reacts_to="belonging",
              feeling="placed", salience=0.85, when="belonging > 3",
              says="The coat's got a number in the collar. That's what the house calls me.")
    coat.part("the-rafter", role="exile", reacts_to="his_own",
              feeling="self_betrayal", salience=0.2, when="his_own > 3",
              says="I cursed in the deck-tongue the moment I thought I'd drown.")

    coat.narrates(voice={
        "surplus": "You people never ask what it costs to give one back.",
        "placed": "It's a good coat. It's warm.",
        "self_betrayal": "The house calls me a number, and I answered to it.",
    })

    # the wound, the lie, the need. His people were declared the surplus; the lie
    # he took to survive it is 'I am the house's number' -- the coat makes him not-
    # surplus, so long as he wears it. The evidence against it is every unbought,
    # ungraded act of his own that matters (the eleven days at the gate). It is
    # breakable: once the coat is gone and he stands anyway, the lie is seen -- he
    # matters as himself, which the number never made him. The positive arc, the
    # mirror of Blade's.
    coat.wounded_by("one of a people the perches named the surplus, the reason "
                    "the hard year was hard", teaches="i-am-the-houses-number")
    coat.believes("i-am-the-houses-number",
                  claim="I am the number in the collar; the coat is what stops me "
                        "being surplus.",
                  disconfirmed_by="his_own_act", feeling="self_betrayal",
                  harms="self", conviction=0.85, breakable=True,
                  says="The coat's got a number in the collar. That's what the "
                       "house calls me.")
    coat.needs("to-matter-as-himself", opposes="i-am-the-houses-number",
               feeling="self_betrayal", fed_feeling="placed")

    # phase 1: the coat feeds 'belonging' steadily (he is placed, not surplus)
    for t in [1, 3, 5]:
        s.at(f"{t}s", coat.hears("belonging", 8))
    # all along, hunting his own presses the exile (never heard over the forms)
    for t in [2, 4, 6, 9, 12]:
        s.at(f"{t}s", coat.hears("his_own", 7))
    # phase 2: the collapse -- the house withdraws the coat, all at once
    for t in [8, 10, 12, 14]:
        s.at(f"{t}s", coat.hears("belonging", 0))
    # phase 3: the gate -- ungraded acts of his own, mounting until they break the
    # lie that he is only the house's number (the eleven days holding the door).
    for t, v in [("15s", 7), ("16s", 8), ("17s", 8), ("18s", 9), ("20s", 9)]:
        s.at(t, coat.hears("his_own_act", v))
    for t in [16, 18, 20]:
        s.at(f"{t}s", coat.hears("belonging", 8))
    return s


def build_derived():
    """Blade, but with his lie *predicted* rather than written. Instead of stating
    the belief, we give the library only the wound (an unmet need for worth) and
    how he copes with it (overcompensation), and let the schema engine forecast the
    lie, the want, and its grip. The prediction reproduces the tragic arc -- which
    is the point: the personality structure was derivable from the wound, not
    something we had to assert."""
    from soma.narrative import guarded as _g
    s = Story("blade_derived", span="22s", step="1s",
              about="a lie derived from the wound, not specified")
    b = s.character("Blade", temperament=volatile)
    b.wounded_by("the injury-scale that priced him in advance",
                 teaches="overcompensation_worth")
    # the library predicts the lie from (unmet need, coping style):
    b.adopts("worth", "overcompensation", disconfirmed_by="equal_regard",
             breakable=None)                       # held as a grandiose denial
    for t, v in [("3s", 6), ("7s", 7), ("11s", 8), ("15s", 9), ("19s", 9)]:
        s.at(t, b.hears("equal_regard", v))
    return s


def predictions():
    """Positive predictions on the cast: forecasts of how each principal would meet
    a situation the author never scripted, plus the tipping point of each lie. None
    of this is read from the timeline; it is generated by running the same model on
    unseen input -- and it is falsifiable, which is the whole point."""
    out = []
    checks = [
        ("Blade suppresses even full equal regard (the tragic prediction)",
         build_ring(), "Blade", {"equal_regard": 9}),
        ("Ink, shown he is kept for nothing, breaks",
         build(), "Ink", {"kept_for_nothing": 9}),
        ("The Coat, given an act that is his own, breaks",
         build_coat(), "Coat", {"his_own_act": 9}),
        ("The Provost, shown his own true sums, breaks -- but later",
         build_selm(), "Selm", {"the_margin": 9}),
    ]
    for label, story, who, stim in checks:
        out.append("• " + label + "\n  " +
                   str(story.predict(who, stim)).replace("\n", "\n  "))
    # tipping points: the least evidence that turns each lie (a sharp claim)
    tps = [("Ink", build(), "kept_for_nothing"), ("Coat", build_coat(), "his_own_act"),
           ("Selm", build_selm(), "the_margin"), ("Blade", build_ring(), "equal_regard")]
    out.append("\nTipping points (least sustained evidence that breaks the lie):")
    for who, story, ch in tps:
        tp = story.tipping_point(who, ch)
        at = tp["breaks_at"]
        out.append(f"  {who:6} on '{ch}': "
                   + (f"breaks at >= {at}" if at is not None
                      else f"never, in {tp['in_range']} -- the lie is kept"))
    return "\n".join(out)


BUILDS = {
    "fleet": build, "ring": build_ring, "combs": build_combs,
    "greywater": build_greywater, "selm": build_selm, "coat": build_coat,
    "derived": build_derived,
}


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    if args and args[0] == "predictions":
        print(predictions())
        sys.exit(0)
    which = "fleet"
    if args and args[0] in BUILDS:
        which = args.pop(0)
    story = BUILDS[which]()
    flag = args[0] if args else "--run"
    if flag == "--source":
        print(story.source())
    elif flag == "--character":
        print(story.characterize(width=78))
    elif flag == "--prose":
        print(story.prose())
    elif flag == "--sift":
        for f in story.sift():
            print(f"[{f.pattern}] {f.text}")
    else:
        print(story.run(width=92))
