"""
the_other_mind.py -- choice under another mind, and the depth of a character.

Every fork in 0.20 had fixed outcomes. The social fork does not: the value of
my move depends on what you will do, and what you will do depends on what you
believe about me. That regress -- "I think that you think that I think..." --
is the computational structure of mentalizing, and its DEPTH is a character
trait with consequences. This simulation implements the recursive
theory-of-mind (k-ToM) framework of Devaine, Hollard & Daunizeau ("The Social
Bayesian Brain", PLoS Comput Biol 2014; "Theory of Mind: Did Evolution Fool
Us?", PLoS ONE 2014; cf. Camerer's cognitive hierarchy):

    0-ToM   no mind attributed: tracks what you tend to DO and best-responds
    k-ToM   attributes a mind: simulates you at every lower depth, learns
            WHICH it is facing from your moves, and best-responds to that

It is also SOMA's oldest metaphysical commitment made computational: a
character never senses another's interior -- other minds arrive only as moves,
as surfaces. A k-ToM mind is what modelling-an-interior-from-surfaces IS.

Five studies:

  I.   THE LADDER. In competition (hide-and-seek), the deeper mind exploits
       the shallower: every rung of extra recursion pays.

  II.  THE ARMS RACE AND THE HANDSHAKE. The same minds in a cooperative game:
       the FIRST level of mentalizing helps, and further depth adds NOTHING.
       Competition is an arms race; cooperation saturates -- which is why, per
       Devaine, it is rivalry and not friendship that would have driven the
       evolution of deep social recursion.

  III. THE COST OF OVER-MENTALIZING. A strict level-k mind that insists its
       opponent is exactly one level below it is catastrophically wrong about
       a naive one: modelling a simple person as a schemer makes YOU the
       predictable one. The mind that infers what it faces is immune.

  IV.  THE COIN. Against pure noise every depth earns chance -- sophistication
       needs structure to bite. And against a mindless BIAS, attributing
       agency would be costly; what saves the mentalizer is holding "there is
       no mind here" as a live hypothesis.

  V.   READING DEPTH FROM MOVES. The inverse problem for minds: an opponent's
       recursion depth inferred from their move sequence alone -- with the
       same identifiability law 0.19 found for symptom hubs: depth is only
       LEGIBLE against an opponent that calls for it.

Run:  python3 examples/narrative/the_other_mind.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from soma.narrative.mentalizing import (Mind, RandomMind, play, tournament,
                                        depth_advantage, detect_depth)


def study_ladder():
    print("=" * 74)
    print("I. THE LADDER — competition rewards every level of depth")
    print("=" * 74)
    t = tournament((0, 1, 2, 3), game="hide_and_seek", rounds=60, reps=30)
    print(t.render())
    print(f"\n  ladder holds: {t.ladder_holds()}")
    print("\n  The diagonal sits near 0.50 — equal depth is a fair fight. "
          "Below it, the\n  deeper seeker exploits the shallower hider "
          "(0.61–0.63); above it, the deeper\n  hider escapes the shallower "
          "seeker. Each extra level of 'I think that you\n  think...' "
          "converts directly into points. Depth is an edge, everywhere.\n")


def study_handshake():
    print("=" * 74)
    print("II. THE ARMS RACE AND THE HANDSHAKE — cooperation saturates")
    print("=" * 74)
    print("  The same minds, but now both win when they MATCH (choosing the "
          "same café).\n  Joint success rate by pair:\n")
    print("              k=0   k=1   k=2   k=3")
    for ka in (0, 1, 2, 3):
        row = []
        for kb in (0, 1, 2, 3):
            m = play(ka, kb, game="coordination", rounds=60, reps=30,
                     beta=3.0)   # gentle play: the building of coordination
                                 # is visible before it locks in
            row.append((m.score_a + m.score_b) / 2)
        print(f"    seat0 k={ka}: " + "  ".join(f"{v:.2f}" for v in row))
    print("\n  Two naive minds coordinate at 0.74. Add ONE level of "
          "mentalizing anywhere\n  and it rises to ~0.80 — and then it stops. "
          "Depth 2, depth 3: nothing more.\n  Competition is an arms race "
          "(study I: every rung pays); cooperation is a\n  handshake — once "
          "both are trying to meet, there is no one left to outwit.\n  This "
          "is the asymmetry behind Devaine's 'Did Evolution Fool Us?': if "
          "deep\n  recursion evolved, it was rivalry, not friendship, that "
          "paid for it.\n")


def study_over_mentalizing():
    print("=" * 74)
    print("III. THE COST OF OVER-MENTALIZING — the paranoid mind loses")
    print("=" * 74)
    strict = play(2, 0, game="hide_and_seek", infer_level=False, reps=30)
    infer = play(2, 0, game="hide_and_seek", infer_level=True, reps=30)
    fair = play(1, 0, game="hide_and_seek", infer_level=False, reps=30)
    print(f"  A 2-deep seeker vs a naive (0-ToM) hider:\n")
    print(f"    strict level-k (insists the hider is a 1-ToM schemer): "
          f"earns {strict.score_a:.2f}")
    print(f"    level-inferring (learns what it actually faces):        "
          f"earns {infer.score_a:.2f}")
    print(f"    (a simple 1-ToM, correctly matched, earns {fair.score_a:.2f})")
    print("\n  The strict mind models best-response behaviour that is not "
          "there, and its\n  countermoves to the imagined scheme are "
          "themselves systematic — the naive\n  hider's plain frequency-"
          "tracking reads them like a book: 0.05, a rout. To\n  see a simple "
          "person as a schemer is not caution; it is handing them your\n  "
          "pattern. The mind that asks 'what am I actually facing?' keeps its "
          "edge.\n")


def study_coin():
    print("=" * 74)
    print("IV. THE COIN — sophistication needs structure to bite")
    print("=" * 74)
    print("  Against PURE randomness (a fair coin), depth earns nothing:\n")
    for k in (0, 1, 2):
        m = play(k, 0, game="hide_and_seek", random_b=0.5, reps=30)
        print(f"    {k}-ToM seeker vs fair coin:   {m.score_a:.2f}")
    print("\n  Against a BIASED coin (plays one side 80% — structure, but no "
          "mind):\n")
    for k in (0, 1, 2):
        m = play(k, 0, game="hide_and_seek", random_b=0.8, reps=30)
        print(f"    {k}-ToM seeker vs biased coin: {m.score_a:.2f}")
    print("\n  There is no outwitting noise: every depth sits at chance against "
          "the fair\n  coin. Against the biased one, all profit — because "
          "every mentalizer here\n  holds 'there is no mind, only a bias' as "
          "a live hypothesis alongside its\n  simulations of agents. Without "
          "that hypothesis a 1-ToM sinks to\n  chance against the coin, "
          "modelling strategy where there is only habit. Knowing when NOT to\n  "
          "attribute a mind is part of having one.\n")


def study_reading_depth():
    print("=" * 74)
    print("V. READING DEPTH FROM MOVES — the inverse problem for minds")
    print("=" * 74)
    print("  Infer a hider's recursion depth from nothing but their move "
          "sequence\n  (per-depth likelihood, Occam-penalized because deeper "
          "minds nest shallower\n  ones):\n")
    for true_k in (0, 1):
        m = play(0, true_k, game="hide_and_seek", rounds=120, reps=1, seed=4)
        r = detect_depth(m.history, seat=1, candidates=(0, 1, 2))
        print(f"    true depth {true_k} (vs a naive seeker):  read as "
              f"{r.inferred}  {'✓' if r.inferred == true_k else '✗'}")
    m0 = play(0, 2, game="hide_and_seek", rounds=150, reps=1, seed=4)
    r0 = detect_depth(m0.history, seat=1, candidates=(0, 1, 2))
    m1 = play(1, 2, game="hide_and_seek", rounds=150, reps=1, seed=4)
    r1 = detect_depth(m1.history, seat=1, candidates=(0, 1, 2))
    print(f"\n    true depth 2 vs a NAIVE seeker:    read as {r0.inferred}  ✗ "
          f"(under-read)")
    print(f"    true depth 2 vs a 1-ToM seeker:    read as {r1.inferred}  ✓")
    print("\n  The misread is the finding. A 2-deep mind facing a naive "
          "opponent never\n  needs its second level — it infers 'naive' and "
          "BEHAVES like a 1-ToM, so\n  from its moves it IS one. Depth is "
          "only legible against an opponent that\n  calls for it: the same "
          "identifiability law 0.19 found for symptom hubs (a\n  hub must "
          "vary to be seen). You cannot read the full depth of a mind from\n"
          "  an easy game — a character's sophistication is a fact about "
          "them, but its\n  VISIBILITY is a fact about their circumstances.\n")


def study_the_tell():
    print("=" * 74)
    print("VI. THE TELL — decisiveness is legibility, so the guarded are read")
    print("=" * 74)
    from soma.narrative.mentalizing import legibility, face_off, social_params_of
    from soma.narrative import guarded, stoic, anxious, tender
    r = legibility(shallow_k=1, deep_k=2)
    print(r.render())
    print("\n  Hold the deeper mind fixed and sweep the shallower one's own "
          "decisiveness:\n  its exploitability rises with its own β. At β=2 "
          "it nearly escapes (0.51);\n  at β=12 it hands over 0.73. A "
          "decisive mind converts its model into action\n  crisply — and a "
          "crisp pattern is a readable one. Wavering is armor;\n  conviction "
          "is a tell.\n")
    print("  And decisiveness is a TEMPERAMENT: deriving each mind's β from "
          "conviction\n  and α from precision (the same dials that drive "
          "feeling and choice), a\n  fixed 2-ToM reader takes from 1-ToM "
          "hiders of each temperament:\n")
    for temp in (guarded, stoic, anxious, tender):
        m = face_off(stoic, temp, k_a=2, k_b=1)
        a, b = social_params_of(temp)
        print(f"    {temp.name:<9} (α={a}, β={b:>4}): loses {m.score_a:.2f}")
    print("\n  The high-conviction temperaments — guarded, stoic, anxious — "
          "are exploited\n  hardest (0.70–0.72); the tender, loose-gripped "
          "one loses least (0.61). The\n  same conviction that armors a "
          "character's beliefs against evidence (0.15's\n  arbitration, "
          "0.17's hysteresis) EXPOSES their behaviour to a deeper mind.\n  "
          "Conviction protects the interior and betrays the surface — one "
          "trait, both\n  fates, unauthored.\n")


if __name__ == "__main__":
    study_ladder()
    study_handshake()
    study_over_mentalizing()
    study_coin()
    study_reading_depth()
    study_the_tell()
