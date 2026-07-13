"""
what_the_body_learns: two theories of learning, run as predictive simulations.

The reward prediction error and learned helplessness are, between them, the most
quantitatively validated predictive models of how creatures learn from
consequence. Both are prediction machines; both fall straight out of SOMA's
loop, whose error term IS a prediction error. This file runs each as a staked,
falsifiable simulation, and in each case leads with the SIGNATURE prediction --
the one a simpler account cannot make.

  I.    the dopamine curve         acquisition, extinction, and the reward
                                   prediction error shrinking to zero as the
                                   reward becomes predicted (Schultz's neurons)
  II.   spontaneous recovery       the prediction single-trace Rescorla-Wagner
                                   CANNOT make: after a rest, the conditioned
                                   response returns -- extinction was new
                                   learning over an intact trace, not erasure
  III.  the triadic design         uncontrollable adversity produces a deficit
                                   that controllable adversity does not
  IV.   the transfer asymmetry     the reformulation's sharpest claim: a GLOBAL
                                   explanatory style carries helplessness into
                                   an unrelated situation; a SPECIFIC style
                                   confines it to situations like the first

    python3 examples/narrative/what_the_body_learns.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from soma.narrative import Story, trusting, hollowed
from soma.narrative.helplessness import triadic_design


def conditioning_study():
    print("=" * 74)
    print("I & II. THE DOPAMINE CURVE, AND SPONTANEOUS RECOVERY")
    print("=" * 74)
    s = Story("pavlov", span="10s", step="1s", about="conditioning")
    rat = s.character("Bell", temperament=trusting)
    s.conditions(rat, cs="tone", us="food")
    rep = s.predict_conditioning("Bell", acquire=10, extinguish=12,
                                 rest=10, reacquire=6)
    print()
    print(rep.render())
    print()
    print("  The value climbs as the tone comes to predict food; the reward")
    print("  prediction error — the dopamine signal — is largest at the first")
    print("  unpredicted reward and falls toward zero as the prediction")
    print("  improves. Extinction drives the value down. Then a REST, with no")
    print("  tone and no food, and the response RETURNS on its own: the proof")
    print("  that extinction never erased the original — it layered a new,")
    print("  fragile 'not anymore' over a trace that outlasts it. A single")
    print("  value could not do this; two traces can. (Pavlov 1927; Bouton.)")


def helplessness_study():
    print()
    print("=" * 74)
    print("III & IV. THE TRIADIC DESIGN AND THE TRANSFER ASYMMETRY")
    print("=" * 74)

    def builder(style):
        s = Story(f"hlp_{style}", span="10s", step="1s",
                  about="learned helplessness")
        subj = s.character("Ash",
                           temperament=hollowed if style == "global" else trusting)
        s.learns_control(subj, style=style)
        return s, subj

    td = triadic_design(builder)
    print()
    print("  The full triadic design — three pretreatments x two explanatory")
    print("  styles x similar/dissimilar novel task — coded for the")
    print("  helplessness deficit:")
    print()
    print("    style      pretreatment      novel task    outcome")
    print("    " + "-" * 60)
    for (style, pre, sim), deficit in sorted(td["rows"].items()):
        simstr = "similar" if sim else "dissimilar"
        out = "DEFICIT" if deficit else "copes"
        print(f"    {style:<9s}  {pre:<15s}   {simstr:<11s}   {out}")
    print()
    print("  Read the uncontrollable rows: the deficit appears ONLY after")
    print("  uncontrollable adversity (controllable and none immunize), and")
    print("  its reach is set by explanatory style. GLOBAL ('I ruin")
    print("  everything') carries the helplessness into a wholly unrelated")
    print("  task; SPECIFIC ('I couldn't do that one thing') confines it to")
    print("  situations like the first.")
    print()
    print(f"  reformulation's full pattern reproduced: {td['all_confirmed']}")
    print(f"  transfer asymmetry (global transfers, specific does not): "
          f"{td['transfer_signature']}")
    print()
    print("  Two people, the same defeat, different futures — and the dividing")
    print("  line is not the event but the sentence each says about it. That")
    print("  is the reformulation's whole claim, and here it is mechanism:")
    print("  a global style is one control-belief shared across every task; a")
    print("  specific style keeps a separate belief per task, so a dissimilar")
    print("  task starts fresh. The scope of the belief IS the explanatory")
    print("  style. (Abramson, Seligman & Teasdale 1978; Alloy et al. 1984.)")


if __name__ == "__main__":
    conditioning_study()
    helplessness_study()
