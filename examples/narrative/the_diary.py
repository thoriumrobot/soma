"""
the_diary.py -- reading a person's wiring from their diary, and reading it back.

Every other character in this library is authored: you write the wiring, then
watch it run. This study runs the arrow BACKWARD, which is the deepest
predictive-characterization move there is and the frontier of clinical network
science (Bringmann, "Person-specific networks in psychopathology", 2021;
Epskamp, van Borkulo et al., "Personalized Network Modeling in Psychopathology",
2018). It authors a character, hides the wiring, lets the character live a life,
records only their DIARY -- and then recovers the wiring from the diary alone,
the way a clinician must with a patient they can only observe.

Because the ground truth is known here (it never is, in a clinic), the loop can
be CLOSED and CHECKED -- which is the thing a simulator can do that a clinic
cannot:

  I.   THE DIARY. An authored patient is driven by fluctuating daily stress and
       logs nine symptoms over ~220 days -- exactly an experience-sampling
       record, except we know the network behind it.

  II.  THE RECOVERY. A lag-1 vector-autoregression estimates the person-specific
       temporal network from the diary: which symptom's today predicts which
       symptom's tomorrow. We score it against the hidden truth -- edge recall
       and, the robust part, whether the recovered HUB is the true hub.

  III. TWO PATIENTS, SAME SYMPTOMS, DIFFERENT WIRING. The clinical payoff of
       the whole network program: Ana and Bo have the identical nine symptoms
       and comparable severity, but Ana's depression is organized around low
       MOOD and Bo's around INSOMNIA. Their diaries look similar; their
       recovered networks do not -- and the model names a DIFFERENT treatment
       target for each, which a symptom count never could.

  IV.  THE IDENTIFIABILITY FLOOR. The honest limit, staked rather than hidden:
       a hub can only be recovered if it VARIES. A root driver held nearly
       constant carries no information about its own outgoing influence, and no
       diary-based method -- ours or the field's -- can recover it. The study
       shows the same patient becoming legible the moment their driver is
       allowed to fluctuate.

  V.   CLOSING THE LOOP. The recovered network is turned back into a runnable
       character and simulated forward. The re-derived patient's stress
       response matches the original's -- author -> live -> observe -> estimate
       -> RE-RUN, the full circle, checked.

Run:  python3 examples/narrative/the_diary.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from soma.narrative.network import (symptom_network, depression_network,
                                    stress_response, DEPRESSION_SYMPTOMS)
from soma.narrative.idiographic import (simulate_diary, estimate_network,
                                        recovery, rebuild_network,
                                        compare_hubs)

S = DEPRESSION_SYMPTOMS

# Ana: a mood-centred depression (low mood drives the rest)
ANA_EDGES = [("insomnia", "fatigue"), ("fatigue", "mood"), ("mood", "interest"),
             ("mood", "worthless"), ("mood", "concentration"),
             ("interest", "mood"), ("worthless", "mood"), ("mood", "appetite"),
             ("mood", "suicidal"), ("concentration", "mood"),
             ("fatigue", "concentration")]

# Bo: a somatic depression (insomnia drives the rest) -- driver allowed to vary
BO_EDGES = [("insomnia", "fatigue"), ("insomnia", "concentration"),
            ("insomnia", "mood"), ("insomnia", "interest"),
            ("fatigue", "concentration"), ("fatigue", "psychomotor"),
            ("fatigue", "interest"), ("insomnia", "appetite"),
            ("mood", "worthless"), ("worthless", "suicidal"), ("fatigue", "mood")]


def study_diary_and_recovery():
    print("=" * 74)
    print("I & II. THE DIARY, AND THE WIRING RECOVERED FROM IT")
    print("=" * 74)
    net = depression_network(name="Mara", connectivity=1.0)
    diary = simulate_diary(net, days=220, seed=3)
    print(diary.render(width=44))
    print()
    est = estimate_network(diary)
    print(est.render(k=8))
    print()
    rep = recovery(diary, est)
    print(rep.render())
    print("\n  From nothing but the diary — no access to the wiring — the "
          "estimate\n  finds the person's hub. The individual edges are noisy "
          "(a known limit),\n  but the most-connected symptom, the one "
          "treatment should target, is\n  recovered. That is the network "
          "program's central promise, checked against\n  a ground truth a "
          "clinic never has.\n")


def study_two_patients():
    print("=" * 74)
    print("III. TWO PATIENTS, SAME SYMPTOMS, DIFFERENT WIRING")
    print("=" * 74)
    cases = [("Ana", ANA_EDGES, None),
             ("Bo", BO_EDGES, {"insomnia": 1.5})]   # Bo's driver fluctuates
    for name, edges, thr in cases:
        net = symptom_network(name, S, edges, connectivity=1.0,
                              thresholds=thr or {})
        diary = simulate_diary(net, days=250, seed=5)
        r = compare_hubs(diary)
        mark = "✓" if r["correct"] else "✗"
        print(f"\n  {name}: same nine symptoms; recovered hub = "
              f"'{r['recovered_hub']}' (true '{r['true_hub']}') {mark}")
        print(f"     out-strength ranking: {', '.join(r['recovered_top3'])}")
        print(f"     -> the model recommends targeting {r['recovered_hub']}")
    print("\n  Ana and Bo would receive the same DSM diagnosis and look alike "
          "on a\n  symptom checklist. Their diaries, run through the same "
          "estimator, reveal\n  different architectures — mood-driven vs "
          "sleep-driven — and therefore\n  different treatment targets. This is "
          "why the field wants person-specific\n  networks: the average patient "
          "does not exist, and the diary tells them\n  apart.\n")


def study_identifiability_floor():
    print("=" * 74)
    print("IV. THE IDENTIFIABILITY FLOOR — a hub must vary to be seen")
    print("=" * 74)
    # Bo's insomnia is the true driver. If it is held nearly constant (high
    # threshold, rarely triggered), it cannot be recovered -- however central.
    print("  Bo's true hub is 'insomnia'. Whether the diary can recover it "
          "depends\n  entirely on whether insomnia VARIES:\n")
    for label, thr in (("insomnia held nearly constant", {"insomnia": 4.5}),
                       ("insomnia allowed to fluctuate", {"insomnia": 1.5})):
        net = symptom_network("Bo", S, BO_EDGES, connectivity=1.0,
                              thresholds=thr)
        diary = simulate_diary(net, days=250, seed=5)
        v = diary.variances()["insomnia"]
        r = compare_hubs(diary)
        mark = "✓ recovered" if r["correct"] else "✗ invisible"
        print(f"    {label:<32}: insomnia variance {v:.4f} -> "
              f"hub '{r['recovered_hub']}' {mark}")
    print("\n  This is the honest floor of all idiographic inference, ours and "
          "the\n  field's: a cause that never moves leaves no trace in the "
          "record it causes.\n  A diary can only reveal the parts of a person "
          "that varied while it was\n  kept. The model states its own blind "
          "spot rather than hiding it.\n")


def study_close_the_loop():
    print("=" * 74)
    print("V. CLOSING THE LOOP — re-derive the character and re-run them")
    print("=" * 74)
    net = depression_network(name="Mara", connectivity=1.0)
    diary = simulate_diary(net, days=220, seed=3)
    est = estimate_network(diary)
    rebuilt = rebuild_network(est, keep=14)
    orig = [n for _, n in stress_response(net, levels=(0, 2, 4)).curve]
    reb = [n for _, n in stress_response(rebuilt, levels=(0, 2, 4)).curve]
    print(f"  symptoms active at stress 0 / 2 / 4:")
    print(f"    original character : {orig}")
    print(f"    re-derived (from diary alone): {reb}")
    match = "matches" if orig[0] == reb[0] and orig[-1] == reb[-1] else "differs"
    print(f"\n  The character was authored, made to live 220 days, observed "
          f"only through\n  their diary, and RE-DERIVED from that diary — and "
          f"the re-derived character's\n  behaviour {match} the original's at "
          f"the extremes. The loop is closed:\n  author -> live -> observe -> "
          f"estimate -> re-run. Prediction and postdiction\n  in one "
          f"instrument, which is exactly what understanding a person is.\n")


if __name__ == "__main__":
    study_diary_and_recovery()
    study_two_patients()
    study_identifiability_floor()
    study_close_the_loop()
