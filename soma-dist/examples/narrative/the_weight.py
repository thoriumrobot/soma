"""
the_weight.py -- a person as a network of symptoms, and depression as a state
the network falls into.

Every earlier character in this library was built from loops an author wired by
hand. This one is different in kind: a NETWORK of symptoms, each activating its
neighbours, whose collective behaviour -- two stable states, a catastrophe
between them, a memory, a slow worsening over a life -- no single node contains.
It is the network theory of mental disorders made runnable (Cramer, van
Borkulo, Giltay, van der Maas, Kendler, Scheffer & Borsboom, "Major Depression
as a Complex Dynamic System", PLoS ONE 2016), extended with Post's kindling
hypothesis (1992) for the slow arc.

The person is nine DSM symptoms -- insomnia, fatigue, poor concentration, loss
of interest, low mood, appetite change, worthlessness, psychomotor change,
suicidal ideation -- directly connected: insomnia feeds fatigue, fatigue feeds
poor concentration and low mood, low mood feeds worthlessness, and so on. Each
symptom's activation is a logistic function of its active neighbours plus
external stress. The single most important number is not any symptom but the
CONNECTIVITY of the graph -- how strongly one symptom pulls the next.

  I.   VULNERABILITY IS CONNECTIVITY. The same stress tips a strongly connected
       person into depression where a weakly connected one shrugs it off. The
       resilient and the vulnerable person differ in no symptom and no stressor
       -- only in the coupling between their symptoms.
  II.  SPONTANEOUS NON-RECOVERY. Ramp the stressor up and back down. In the
       weakly connected person the symptoms clear when the stress does; in the
       strongly connected one the depression OUTLIVES its cause -- removing the
       stressor leaves the network holding itself down. The disorder has become
       its own cause.
  III. WELL OR DEPRESSED, RARELY BETWEEN. Sampled across the transition band,
       the strongly connected person settles at an extreme far more often than
       in the middle -- the cusp catastrophe's bimodality. Same stress
       distribution, more depression, because of the shape of the landscape.
  IV.  KINDLING — THE SLOW ARC. Post's hypothesis, and the honest debt from the
       panic study: each episode lowers the threshold for the next. Over a life
       the stressor required to trigger an episode falls, until episodes arrive
       AUTONOMOUSLY, with no stressor at all. The first heartbreak takes a
       divorce; the tenth takes a rainy Tuesday.
  V.   WHAT TO TREAT. The network-theory question no symptom-count can answer:
       which single symptom, held off, most collapses the rest? The answer is
       the most-connected node, not the most severe one -- and the model names
       it.

Run:  python3 examples/narrative/the_weight.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from soma.narrative.network import (depression_network, stress_response,
                                    hysteresis_loop, equilibrium_modes,
                                    kindling, target_symptom)

RESILIENT = 0.45
VULNERABLE = 1.4


def study_connectivity():
    print("=" * 74)
    print("I. VULNERABILITY IS CONNECTIVITY — the same stress, two people")
    print("=" * 74)
    for label, conn in (("resilient", RESILIENT), ("vulnerable", VULNERABLE)):
        sr = stress_response(depression_network(name=label.capitalize(),
                                                connectivity=conn))
        print(sr.render())
        print()
    print("  Neither person has a symptom the other lacks, and both face the "
          "same\n  stressors. The vulnerable one tips into depression at a "
          "lower stress\n  purely because their symptoms are more tightly "
          "coupled — one bad night's\n  sleep pulls the rest down. Vulnerability "
          "is in the wiring, not the parts.\n")


def study_hysteresis():
    print("=" * 74)
    print("II. SPONTANEOUS NON-RECOVERY — when the depression outlives its cause")
    print("=" * 74)
    for label, conn in (("resilient", RESILIENT), ("vulnerable", VULNERABLE),
                        ("severe", 3.2)):
        h = hysteresis_loop(depression_network(name=label.capitalize(),
                                               connectivity=conn))
        print(h.render())
        print()
    print("  Three regimes, one wiring dial. Both the resilient and the "
          "vulnerable\n  network are HYSTERETIC — the depression outlives its "
          "cause, releasing only\n  below the stress that triggered it — but "
          "lowering the stress far enough\n  does lift it, and the vulnerable "
          "one both triggers sooner and releases\n  lower. At severe "
          "connectivity the loop never closes: at ZERO stress the\n  network "
          "holds itself down — worthlessness feeds low mood feeds poor sleep\n"
          "  feeds fatigue, a cycle that no longer needs the world. THAT is "
          "spontaneous\n  non-recovery, and it is the model's account of why "
          "a depression can\n  persist after the loss that started it is long "
          "past.\n")


def study_modes():
    print("=" * 74)
    print("III. WELL OR DEPRESSED, RARELY BETWEEN — the cusp catastrophe")
    print("=" * 74)
    for label, conn in (("resilient", RESILIENT), ("vulnerable", VULNERABLE)):
        em = equilibrium_modes(depression_network(name=label.capitalize(),
                                                  connectivity=conn),
                               samples=60, seed=1)
        print(em.render())
        print()
    print("  Identical stress distributions; the difference is the shape of "
          "the\n  landscape. The vulnerable person ends depressed far more "
          "often — not\n  because they meet more stress, but because their "
          "landscape has a deep\n  depressed basin and a narrow well one.\n")


def study_kindling():
    print("=" * 74)
    print("IV. KINDLING — the slow arc, across a life")
    print("=" * 74)
    k = kindling(depression_network(name="A_life", connectivity=1.05),
                 episodes=9, sensitization=0.45)
    print(k.render())
    print("\n  This is the arc a single run cannot show: the trigger required "
          "for an\n  episode falls with every episode, until the illness "
          "recurs on its own.\n  The kindling is a permanent lowering of the "
          "threshold — the first episode\n  takes a real blow; by the last, a "
          "rainy Tuesday will do. It is also the\n  slow arc the panic study "
          "named and could not yet model: a disorder that\n  learns to happen "
          "more easily.\n")


def study_target():
    print("=" * 74)
    print("V. WHAT TO TREAT — the most-connected symptom, not the worst one")
    print("=" * 74)
    net = depression_network(name="Patient", connectivity=1.15)
    t = target_symptom(net, stress=3.0)
    deg = net.degree()
    print(f"  With every symptom active ({t['baseline']}/9), disabling each "
          f"symptom in turn\n  leaves this many others still active:\n")
    for s in sorted(t["per_symptom"], key=t["per_symptom"].get):
        mark = "  <- best target" if s == t["best_target"] else ""
        print(f"    without {s:<14}: {t['per_symptom'][s]}/9 remain "
              f"(in-degree {deg[s]}){mark}")
    print(f"\n  The model names '{t['best_target']}' — the most-connected node "
          f"— as the symptom\n  whose removal most collapses the rest. Network "
          f"theory's practical claim:\n  treat the hub, not the loudest "
          f"symptom.\n")


if __name__ == "__main__":
    study_connectivity()
    study_hysteresis()
    study_modes()
    study_kindling()
    study_target()
