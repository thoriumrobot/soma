"""
the_fork.py -- how a character chooses, and the whole space of their choosing.

Every earlier study predicts what a character feels or becomes. This one
predicts what they DO at a fork -- and uses the one theory of choice that gets
a deep thing right: that a person wants two incompatible things at once, to get
what they prefer AND to find out what they don't yet know, and that a character
IS the particular way they trade those off. Under active inference (Friston,
FitzGerald, Rigoli, Schwartenbeck, O'Doherty & Pezzulo 2016; Friston et al.,
"Active inference and epistemic value", 2015) a chooser minimizes EXPECTED FREE
ENERGY, which splits into exactly:

    choiceworthiness  =  how close it lands to what I prefer   (pragmatic)
                      +  curiosity × how much I'd learn         (epistemic)

Four studies, each a different face of the space of a person's choices:

  I.   EXPLORE OR EXPLOIT. The same two options -- a safe known bet and an
       uncertain, information-rich one -- put to choosers of rising curiosity.
       A character crosses from taking the sure thing to gambling on the
       unknown at a curiosity that is theirs alone. The exploration/
       exploitation dilemma, dissolved into one dial, read per person.

  II.  PREFERENCE IS A TARGET, NOT A CEILING. Active inference's quiet, humane
       correction to reward maximization: pragmatic value is CLOSENESS to what
       you prefer, so a character can decline an option that overshoots what
       they actually wanted. The person who wants 'enough' turns down 'more' --
       a choice a reward-maximizer cannot even represent, and a deeply
       characterful one.

  III. THE CHOICE IS IN THE TEMPERAMENT. A character authored for the feeling
       layers -- their trust in the senses, their grip on their beliefs --
       ALREADY implies how they choose: the open, trusting temperament explores;
       the guarded, convinced one exploits. The same person who feels a certain
       way decides a certain way, from the same dials. We read four temperaments'
       choices off nothing but their dispositions.

  IV.  THE SPACE OF A LIFE'S FORKS. One character, many forks of rising stakes
       and rising uncertainty, mapped: where they will hold and where they will
       leap. Not one prediction but the shape of a person's daring across every
       fork they might meet.

Run:  python3 examples/narrative/the_fork.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from soma.narrative import Story, anxious, stoic, tender, guarded
from soma.narrative.choice import (Option, decide, explore_exploit, temptation,
                                   curiosity_of, expected_free_energy)


def study_explore_exploit():
    print("=" * 74)
    print("I. EXPLORE OR EXPLOIT — the same fork, choosers of rising curiosity")
    print("=" * 74)
    safe = Option("the known road", reward=6, uncertainty=0.6)
    risky = Option("the unknown road", reward=5, uncertainty=3.5)
    ee = explore_exploit(safe, risky, preference=8,
                         curiosities=(0, 0.3, 0.6, 1, 2, 3))
    print(ee.render())
    print("\n  The unknown road is believed to pay LESS (5 vs 6) — a pure "
          "reward chooser\n  would never take it. But it offers more to learn, "
          "and as curiosity rises\n  the character crosses over. Exploration is "
          "not irrationality; it is a\n  different, legible term in the same "
          "calculation.\n")


def study_preference_target():
    print("=" * 74)
    print("II. PREFERENCE IS A TARGET, NOT A CEILING — declining 'more'")
    print("=" * 74)
    safe = Option("enough", reward=7, uncertainty=0.5)
    print("  A modest character (prefers 7) vs an ambitious one (prefers 9),")
    print("  offered a sure gamble of rising reward against a steady 'enough':\n")
    for pref, label in ((7, "modest (wants 7)"), (9, "ambitious (wants 9)")):
        row = []
        for rew in (6, 7, 8, 9, 10):
            gamble = Option("more", reward=rew, uncertainty=0.5)
            d = decide((pref, 1.0), [safe, gamble])
            row.append(f"{rew}:{d.p('more'):.0%}")
        print(f"    {label:<20} P(take 'more') by its reward — "
              + "  ".join(row))
    print("\n  The ambitious chooser's appetite climbs with the reward. The "
          "modest one's\n  PEAKS at 7 and then FALLS: a reward of 10 overshoots "
          "what they wanted, and\n  they decline it. 'Enough' is a real "
          "preference, and only a closeness-to-\n  target account can represent "
          "the person who turns down more.\n")


def study_temperament():
    print("=" * 74)
    print("III. THE CHOICE IS IN THE TEMPERAMENT — deciding from disposition")
    print("=" * 74)
    safe = Option("stay", reward=8, uncertainty=0.5)
    risky = Option("leave", reward=5.5, uncertainty=2.5)
    print("  The same fork — stay (known, at what they want) vs leave "
          "(uncertain, less\n  reward but more to learn) — put to four "
          "temperaments, their curiosity DERIVED\n  from the very dials that "
          "drive their feelings:\n")
    for temp in (guarded, stoic, anxious, tender):
        s = Story("t", span="4s", step="1s", about="acute distress")
        c = s.character("C", temperament=temp)
        cur = curiosity_of(c)
        d = decide(c, [safe, risky], preference=8, decisiveness=2.5,
                   sigma_pref=1.5)
        print(f"    {temp.name:<9} (curiosity {cur:>4.2f}): "
              f"P(leave) {d.p('leave'):>4.0%}  -> {d.choice}")
    print("\n  No choice was authored. The guarded, convinced temperaments hold "
          "the known\n  road; the open, trusting one leaves to find out. The "
          "way a person feels and\n  the way they choose fall out of the same "
          "two numbers — which is what it means\n  for a character to be "
          "whole.\n")


def study_life_of_forks():
    print("=" * 74)
    print("IV. THE SPACE OF A LIFE'S FORKS — one person, every fork")
    print("=" * 74)
    s = Story("t", span="4s", step="1s", about="acute distress")
    c = s.character("Wren", temperament=stoic.tuned(conviction=0.5,
                                                    precision=0.7))
    cur = curiosity_of(c)
    print(f"  Wren (curiosity {cur:.2f}) at forks of rising stakes (the safe "
          f"reward, at what\n  they want) and rising uncertainty (how unknown "
          f"the alternative is). Each cell\n  is P(Wren leaps) — the map of one "
          f"person's daring:\n")
    print("           unknown→    low(1)   med(2.5)  high(4)")
    for stake in (6, 7, 8):
        cells = []
        safe = Option("hold", reward=stake, uncertainty=0.4)
        for unc in (1.0, 2.5, 4.0):
            leap = Option("leap", reward=4, uncertainty=unc)
            d = decide((stake, cur), [safe, leap], decisiveness=2.0,
                       sigma_pref=1.5)
            cells.append(f"{d.p('leap'):>5.0%}")
        print(f"    stake {stake:>2}          " + "    ".join(cells))
    print("\n  Two axes at once, every cell informative: Wren leaps more as "
          "the\n  alternative grows uncertain (news to be had), and less as "
          "the stakes rise\n  (more forgone by leaving a good thing). The "
          "high-stakes, low-mystery corner\n  is where even a curious person "
          "holds (1%) — yet even at the highest stake,\n  enough mystery "
          "tips her (70%). This is not a single prediction but the whole\n  "
          "surface of a character's choosing — the space of forks, mapped "
          "before any\n  arrive.\n")


if __name__ == "__main__":
    study_explore_exploit()
    study_preference_target()
    study_temperament()
    study_life_of_forks()
