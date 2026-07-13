"""
Library-mode playground examples: short Python programs that drive the
soma.narrative high-level library, including the predictive-characterization
and insight layers. Each is a (key, label, blurb, code) entry. These run in the
browser via web_bridge.run_python -- the same API as the command line.

Kept as one file so build_html can bundle them without directory walking.
"""

EXAMPLES = []


def _ex(key, label, blurb, code):
    EXAMPLES.append(dict(key=key, label=label, blurb=blurb,
                         code=code.strip("\n") + "\n"))


# --------------------------------------------------------------------------
_ex("lib/hello", "hello · a character", "build a character, run the loop",
r"""
# The high-level library: describe a person in feelings and beliefs, and it
# compiles to SOMA and runs. Press Run.
from soma.narrative import Story, tender

story = Story("hello", span="8s", step="1s", about="a first delight")
c = story.character("Wen", temperament=tender)
c.senses("her_face")
c.appraises("her_face", feeling="delight", when="her_face > 3")

story.at("2s", c.hears("her_face", 7))
print(story.run(width=76))
""")

# --------------------------------------------------------------------------
_ex("lib/see_the_soma", "see the SOMA it compiles to", "library -> generated SOMA source",
r"""
# Anything you build with the library is ordinary SOMA underneath. Print
# .source() to see exactly what it compiled to -- then copy it into SOMA mode.
from soma.narrative import Story, stoic

story = Story("kept", span="14s", step="1s", about="a defended belief")
ink = story.character("Ink", temperament=stoic)
ink.senses("kept_for_nothing")
ink.believes("only_needed",
             claim="the only reason anyone is kept is that they are needed",
             disconfirmed_by="kept_for_nothing", breakable=True)
for t in range(2, 12):
    story.at(f"{t}s", ink.hears("kept_for_nothing", 8))

print(story.source())
""")

# --------------------------------------------------------------------------
_ex("lib/handwritten_soma", "run hand-written SOMA", "write SOMA text, run it through the library",
r"""
# You can also write SOMA source by hand and run it through the library on the
# same page -- both directions work.
from soma import run_source

soma_src = '''
sim { duration: 6s  dt: 1s }
body B @cardiac { intero heart : BPM baseline 70 }
stimulus heart { at 2s: 120 }
loop noticing @cardiac {
  prior:      predict(70)
  sense:      heart
  precision:  0.9
  conviction: 0.3
  act { emit feel(surprise) }
}
'''
r = run_source(soma_src, title="handwritten")
for e in r.chronicle:
    if e.kind == "emit":
        q = str(e.detail.get("quale")).replace("Qualia<", "").rstrip(">")
        print(f"{e.t:>4}s  felt {q}")
""")

# --------------------------------------------------------------------------
_ex("lib/predict_break", "predict · the tipping point", "forecast a break before it happens",
r"""
# Two positive predictions about a belief that slowly gives way. First the
# THRESHOLD -- the least pressure that breaks it; then EARLY WARNING -- reading
# only the pre-transition dynamics to forecast the break before it happens.
from soma.narrative import Story, tender

def build():
    s = Story("overwhelmed", span="26s", step="1s", about="slowly overwhelmed")
    c = s.character("Vane", temperament=tender)
    c.senses("the_evidence")
    c.believes("i_did_not_matter", claim="I did not matter",
               disconfirmed_by="the_evidence", breakable=True, conviction=0.9)
    c.learns(0.03)
    # the evidence rises gradually, so the break builds rather than slamming in
    for t in range(2, 24):
        s.at(f"{t}s", c.hears("the_evidence", round(min(9, 2 + 0.3 * (t - 2)), 1)))
    return s

print("tipping point:", build().tipping_point("Vane", "the_evidence"))
print()
print(build().predict_break_onset("Vane", window=5).render())
""")

# --------------------------------------------------------------------------
_ex("lib/appraisal", "appraisal · predict the feeling", "derive the emotion from the appraisal",
r"""
# Appraisal theory: give only the appraisal (was it bad, who caused it, how
# certain, could anything be done) and the library PREDICTS the discrete
# emotion and its action tendency -- the author never names it.
from soma.narrative import predict_feeling, check_identifiability, explain_emotion

for (cong, agency, coping, note) in [
    (-0.8, "other", 0.8, "wronged, with power"),
    (-0.8, "other", 0.2, "wronged, powerless"),
    (-0.9, "circumstance", 0.1, "a certain, uncontrollable loss"),
]:
    pf = predict_feeling(congruence=cong, agency=agency, certainty=0.9, coping=coping)
    print(f"{note:32s} -> {pf.quale}  ({pf.tendency.split('--')[0].strip()})")

print()
v = check_identifiability()
print(f"construct validity: all {v['n']} emotions recover ({v['recovered']})")
print()
print(explain_emotion("grief"))
""")

# --------------------------------------------------------------------------
_ex("lib/attachment", "attachment · a separation", "install a style, forecast the separation",
r"""
# Install an attachment style; the library stakes a style-specific forecast
# BEFORE the run, then checks it. Here are the two most telling styles in full.
from soma.narrative import Story, anxious, stoic

for style, temp in [("avoidant", stoic), ("anxious", anxious)]:
    s = Story(f"sep_{style}", span="12s", step="1s", about="separation distress")
    c = s.character("Mara", temperament=temp)
    c.attaches(style, to="Jonah")
    print(s.predict_separation("Mara").render())
    print()
""")

# --------------------------------------------------------------------------
_ex("lib/strange_situation", "the Strange Situation", "blind classification from behavior",
r"""
# Ainsworth's protocol, run whole: the coder reads only the behavior stream and
# must recover the installed style. Construct validity as parameter recovery.
from soma.narrative import Story, trusting, anxious, stoic, guarded
from soma.narrative import strange_situation, validate_instrument

TEMPS = {"secure": trusting, "anxious": anxious,
         "avoidant": stoic, "disorganized": guarded}

def build(style):
    s = Story(f"ss_{style}", span="24s", step="1s", about="separation distress")
    child = s.character("Noa", temperament=TEMPS[style])
    child.attaches(style, to="mother")
    return s, child

# show one coded tape in full:
s, c = build("avoidant")
print(strange_situation(s, c).render())
print()
# then the blind recovery of all four:
r = validate_instrument(build)
for style in TEMPS:
    print(f"  installed {style:<13s} -> classified {r[style]}")
print(f"\\ninstrument valid: {r['recovered']}")
""")

# --------------------------------------------------------------------------
_ex("lib/gottman", "the Gottman marriage model", "thin-slice divorce prediction",
r"""
# The mathematics of marriage: five couple types, one contentious conversation,
# and the famous thin-slice forecast -- the ending called from the first quarter.
from soma.narrative import Story, trusting, tender, COUPLE_TYPES, marry, gottman_assess

for tname in COUPLE_TYPES:
    s = Story(f"m_{tname}", span="20s", step="1s")
    a = s.character("Ash", temperament=trusting)
    b = s.character("Bee", temperament=tender)
    marry(s, a, b, tname)
    rep = gottman_assess(s)
    ok = "OK " if rep.confirmed else "!! "
    print(f"{ok}{tname:>16s}: ratio {rep.ratio:6.2f}:1  "
          f"reciprocity {rep.reciprocity:4.0%}  thin-slice: {rep.thin_forecast}")
""")

# --------------------------------------------------------------------------
_ex("lib/conditioning", "conditioning · spontaneous recovery", "the reward prediction error, with recovery",
r"""
# The reward prediction error, run as learning. The signature prediction plain
# Rescorla-Wagner cannot make: after extinction and a REST, the response returns.
from soma.narrative import Story, trusting

s = Story("pavlov", span="10s", step="1s", about="conditioning")
rat = s.character("Bell", temperament=trusting)
s.conditions(rat, cs="tone", us="food")
rep = s.predict_conditioning("Bell", acquire=10, extinguish=12, rest=10, reacquire=6)
print(rep.render())
""")

# --------------------------------------------------------------------------
_ex("lib/helplessness", "learned helplessness", "the transfer asymmetry",
r"""
# Reformulated learned helplessness: the deficit transfers to an unrelated task
# only for a GLOBAL explanatory style, not a specific one. The full triadic
# design, checked.
from soma.narrative import Story, trusting, hollowed, triadic_design

def build(style):
    s = Story(f"hlp_{style}", span="10s", step="1s", about="learned helplessness")
    subj = s.character("Dog", temperament=hollowed if style == "global" else trusting)
    s.learns_control(subj, style=style)
    return s, subj

td = triadic_design(build)
print("style      pretreatment      novel task    outcome")
print("-" * 56)
for (style, pre, sim), deficit in sorted(td["rows"].items()):
    simstr = "similar" if sim else "dissimilar"
    print(f"{style:<9s}  {pre:<15s}   {simstr:<11s}   "
          f"{'DEFICIT' if deficit else 'copes'}")
print(f"\\ntransfer asymmetry holds: {td['transfer_signature']}")
""")

# --------------------------------------------------------------------------
_ex("lib/decision", "drift-diffusion decisions", "reaction time and the speed-accuracy tradeoff",
r"""
# How long a choice takes, and how often it is wrong. The drift-diffusion model:
# four decision temperaments, then the speed-accuracy tradeoff from one dial.
from soma.narrative import Story, trusting, DECISION_STYLES

s = Story("court", span="1s", step="1s", about="a verdict")
j = s.character("Juror", temperament=trusting)

print("juror style   accuracy   RT correct   RT error   skew")
for style in DECISION_STYLES:
    s.decides(j, style=style)
    r = s.predict_decision("Juror", trials=3000, seed=1)
    print(f"{style:<12s}  {r.accuracy:>6.0%}     {r.mean_rt:>6.2f}s    "
          f"{r.mean_rt_error:>6.2f}s   {r.skew:+.2f}")

print()
s.decides(j, drift=0.13, boundary=1.0)
print(s.speed_accuracy("Juror", boundaries=[0.6, 1.0, 1.5, 2.0],
                       trials=3000, seed=2).render())
""")

# --------------------------------------------------------------------------
_ex("lib/sensitivity", "insight · which dial writes the ending", "variance-based sensitivity",
r"""
# An insight ABOUT a prediction: variance-based (Sobol) sensitivity -- which
# parameter actually writes the outcome, alone or through interaction.
from soma.narrative import Story, stoic

s = Story("kept", span="16s", step="1s", about="a defended belief")
ink = s.character("Ink", temperament=stoic)
ink.senses("kept_for_nothing")
ink.believes("only_needed", claim="only the needed matter",
             disconfirmed_by="kept_for_nothing", breakable=True)
for t in range(2, 14):
    s.at(f"{t}s", ink.hears("kept_for_nothing", 8))

L = "the_lie_only_needed"
rep = s.sensitivity(
    params={f"{L}.conviction": (0.3, 0.99),
            f"{L}.learn": (0.0, 0.3),
            f"{L}.precision": (0.2, 0.9)},
    outcome_name="break_time", character="Ink", n_base=24, seed=7)
print(rep.render())
""")

# --------------------------------------------------------------------------
_ex("lib/counterfactual", "insight · the smallest change", "the margin the ending turns on",
r"""
# The counterfactual: the smallest single-dial change that flips the ending --
# the margin the whole story turned on.
from soma.narrative import Story, stoic

s = Story("kept", span="16s", step="1s", about="a defended belief")
ink = s.character("Ink", temperament=stoic)
ink.senses("kept_for_nothing")
ink.believes("only_needed", claim="only the needed matter",
             disconfirmed_by="kept_for_nothing", breakable=True)
for t in range(2, 14):
    s.at(f"{t}s", ink.hears("kept_for_nothing", 8))

L = "the_lie_only_needed"
rep = s.minimal_intervention(
    target=("break", 0.0),                       # what would PREVENT the break?
    dials={f"{L}.conviction": (0.85, 3.0),
           f"{L}.precision": (0.05, 0.35)},
    character="Ink")
print(rep.render())
""")

# --------------------------------------------------------------------------
_ex("lib/preregister", "insight · preregister a forecast", "stake claims before the run",
r"""
# Preregistration: stake claims BEFORE the run, check them after. Adding a claim
# after checking is a postdiction and is refused -- the line between prediction
# and hindsight, enforced.
from soma.narrative import Story, anxious

s = Story("acute", span="8s", step="0.5s", about="acute distress")
n = s.character("Nadia", temperament=anxious)
n.senses("ear")
n.appraises("ear", as_threat=True, drives="heart", to=118, when="ear > 3", fades_to=70)
n.feels("dread", from_body="heart")
n.narrates(downplaying={"dread": "I'm fine."})
s.at("2s", n.hears("ear", 9))

audit = s.preregister()
audit.expect_feeling("Nadia", "dread", by="4s")
audit.expect_gap("Nadia", at_least=0.4)          # says calm over a racing heart
audit.expect_peak("Nadia", "heart", at_least=110)
audit.expect_feeling("Nadia", "joy")             # deliberately wrong
print(audit.check().render())
""")


# The order the playground rail should present these in: it matches the flow of
# TUTORIAL_PREDICTIVE.md — basics first, then appraisal and the preregistration
# method, then the simulations simple-to-complex, then the post-hoc insight tools.
# --------------------------------------------------------------------------
# CAPSTONE STUDIES: full command-line examples from examples/narrative/,
# bundled unmodified except for the standalone sys.path shim (unneeded here,
# soma is already importable) and the __main__ guard (replaced with a direct
# call, since the browser bridge execs with __name__ != "__main__"). Each
# composes several prediction/insight tools into one worked study -- richer
# and longer than the single-concept examples above.

# --- the predictive-characterization layers (0.15-0.22) -----------------

_ex("lib/pc_signature", "0.15 · the behavioral signature", "trait-identical, profile-different — and the situation that tells them apart",
r"""
# 0.15 -- the behavioral SIGNATURE: two people can be trait-IDENTICAL and
# still be nobody's twins. Character is the if-THEN profile across situations
# (Mischel & Shoda's CAPS), and it is computable -- including the one
# situation you would stage to tell two people apart.
from soma.narrative import (Story, guarded, signature, similarity,
                            diagnostic_situation)

story = Story("wediko", span="8s", step="1s", about="acute distress")
ren = story.character("Ren", temperament=guarded)
ren.senses("judgment"); ren.senses("warmth")
ren.appraises("judgment", as_threat=True, feeling="fear",
              precision=0.3, conviction=0.9)
ren.appraises("warmth", feeling="comfort",
              precision=0.9, conviction=0.2, updates=True)

sol = story.character("Sol", temperament=guarded)      # the SAME temperament
sol.senses("judgment"); sol.senses("warmth")
sol.appraises("judgment", feeling="fear",
              precision=0.9, conviction=0.2, updates=True)
sol.appraises("warmth", as_threat=True, feeling="wariness",
              precision=0.3, conviction=0.9)

battery = {"a judging eye": {"judgment": 8},
           "an open warmth": {"warmth": 8}}
sr, ss = signature(story, ren, battery), signature(story, sol, battery)
print(sr.render()); print()
print(ss.render()); print()
print(f"profile similarity: {similarity(sr, ss):.2f} "
      f"(mean levels equal: {sr.mean_level() == ss.mean_level()})")
d = diagnostic_situation(story, ren, sol, battery)
print(f"stage THIS to tell them apart: '{d['situation']}' "
      f"(separation {d['separation']})")
""")

_ex("lib/pc_portrait", "0.17 · the intrapersonal landscape", "calm and panic as attractors; reappraisal as a bifurcation",
r"""
# 0.17 -- the INTRAPERSONAL LANDSCAPE: a panic-prone psyche has TWO stable
# states, calm and attack, and the AROUSAL SCHEMA (how readily the body is
# read as catastrophe) decides how much of the plane drains into the bad one
# (Robinaugh et al.'s panic model). Reappraisal is a bifurcation.
from soma.narrative import Story, anxious, state_portrait

def panic_person(schema):
    guard = round(85 - 50 * schema)   # high schema = a low bar for misreading
    s = Story("panic", span="70s", step="1s", about="acute distress")
    p = s.character("Noa", temperament=anxious)
    p.senses("stressor", baseline=0.0)
    p.appraises("stressor", as_threat=True, when="stressor > 4",
                drives="arousal", to=70, fades_to=20, expects=0.0,
                precision=0.9, conviction=0.2)
    p.appraises("arousal", as_threat=True, when=f"arousal > {guard}",
                feeling="dread", drives="perceived_threat", to=90, fades_to=5,
                expects=20.0, precision=0.9, conviction=0.3)
    p.appraises("perceived_threat", as_threat=True, when="perceived_threat > 50",
                feeling="terror", drives="arousal", to=95, fades_to=20,
                expects=5.0, precision=0.9, conviction=0.3)
    return s

port = state_portrait(panic_person(schema=0.85), "Noa",
                      ("arousal", "perceived_threat"), grid=5, lo=0, hi=100,
                      beats=24, high_label="panic", low_label="calm",
                      healthy_is="low")
print(port.render())
print()
print("REAPPRAISAL (raising the bar at which the body is read as danger):")
for schema in (0.85, 0.6, 0.4, 0.2):
    port = state_portrait(panic_person(schema), "Noa",
                          ("arousal", "perceived_threat"), grid=5, lo=0,
                          hi=100, beats=24, high_label="panic",
                          low_label="calm", healthy_is="low")
    panic = 1 - port.healthy_share
    gone = "  <- panic attractor GONE" if panic == 0 else ""
    print(f"  schema {schema:.2f}: panic basin {panic:>4.0%} "
          + "█" * round(panic * 20) + gone)
""")

_ex("lib/pc_network", "0.18 · a person as a network", "nine symptoms that feed each other; vulnerability is connectivity",
r"""
# 0.18 -- a person AS A NETWORK: depression as nine symptoms that feed each
# other (Cramer et al.). Vulnerability is CONNECTIVITY: the same stressors,
# a different wiring strength, a different fate.
from soma.narrative import depression_network, stress_response

from soma.narrative import hysteresis_loop

for label, conn in (("resilient (conn 0.45)", 0.45),
                    ("vulnerable (conn 1.40)", 1.40)):
    net = depression_network(connectivity=conn)
    r = stress_response(net, levels=(0, 1, 2, 2.5, 3))
    print(label)
    print(r.render())
    print()
print("The vulnerable wiring tips at a stress the resilient one shrugs off. "
      "And\nonce tipped, does lifting the stress lift the person? Sweep it "
      "back down:\n")
for label, conn in (("vulnerable", 1.4), ("severe", 3.2)):
    h = hysteresis_loop(depression_network(name=label, connectivity=conn))
    print(h.render())
    print()
print("The vulnerable network's depression OUTLIVES its cause (it releases "
      "only\nwell below its trigger); the severe one never lets go -- at "
      "zero stress it\nholds itself down. Spontaneous non-recovery, "
      "generated.")
""")

_ex("lib/pc_diary", "0.19 · the diary (inverse problem)", "estimate a person's wiring from their diary; pick the treatment target",
r"""
# 0.19 -- the INVERSE PROBLEM: Ana and Bo report the same nine symptoms and
# would get the same diagnosis. Simulate each person's daily diary, estimate
# their PERSONAL network from the diary alone (lag-1 VAR, Bringmann/Epskamp),
# and find different treatment targets. The average patient does not exist.
from soma.narrative import (symptom_network, DEPRESSION_SYMPTOMS,
                            simulate_diary, compare_hubs)

S = DEPRESSION_SYMPTOMS
ANA = [("insomnia","fatigue"), ("fatigue","mood"), ("mood","interest"),
       ("mood","worthless"), ("mood","concentration"), ("interest","mood"),
       ("worthless","mood"), ("mood","appetite"), ("mood","suicidal"),
       ("concentration","mood"), ("fatigue","concentration")]   # mood-centred
BO  = [("insomnia","fatigue"), ("insomnia","concentration"),
       ("insomnia","mood"), ("insomnia","interest"),
       ("fatigue","concentration"), ("fatigue","psychomotor"),
       ("fatigue","interest"), ("insomnia","appetite"),
       ("mood","worthless"), ("worthless","suicidal"),
       ("fatigue","mood")]                                       # sleep-driven

for name, edges, thr in (("Ana", ANA, None), ("Bo", BO, {"insomnia": 1.5})):
    net = symptom_network(name, S, edges, connectivity=1.0,
                          thresholds=thr or {})
    diary = simulate_diary(net, days=250, seed=5)
    r = compare_hubs(diary)
    mark = "OK" if r["correct"] else "MISS"
    print(f"{name}: recovered hub = '{r['recovered_hub']}' "
          f"(true '{r['true_hub']}') {mark}")
    print(f"   -> the model recommends targeting {r['recovered_hub']}")
print()
print("Same checklist, different wiring, different target -- and the diary "
      "alone\nis enough to tell them apart.")
""")

_ex("lib/pc_choice", "0.20 · choice (expected free energy)", "explore vs exploit from one dial; the temperament decides",
r"""
# 0.20 -- CHOICE under expected free energy: a chooser wants two things at
# once, what they prefer AND what they'd learn (Friston et al.). Curiosity
# trades them -- and curiosity is a temperament.
from soma.narrative import (Option, decide, explore_exploit, curiosity_of,
                            Story, guarded, stoic, anxious, tender)

safe  = Option("the known road",   reward=6, uncertainty=0.6)
risky = Option("the unknown road", reward=5, uncertainty=3.5)
print(explore_exploit(safe, risky, preference=8,
                      curiosities=(0, 0.3, 1, 3)).render())
print()

stay  = Option("stay",  reward=8,   uncertainty=0.5)
leave = Option("leave", reward=5.5, uncertainty=2.5)
print("the same fork, four temperaments (curiosity derived, not authored):")
for t in (guarded, stoic, anxious, tender):
    s = Story("t", span="4s", step="1s", about="acute distress")
    c = s.character("C", temperament=t)
    d = decide(c, [stay, leave], preference=8, decisiveness=2.5,
               sigma_pref=1.5)
    print(f"  {t.name:<9} (curiosity {curiosity_of(c):>4.2f}): "
          f"P(leave) {d.p('leave'):>4.0%} -> {d.choice}")
""")

_ex("lib/pc_other_mind", "0.21 · the other mind (k-ToM)", "depth wins, over-mentalizing loses, and depth is readable from moves",
r"""
# 0.21 -- the OTHER MIND: recursion depth ("I think that you think...") is a
# character trait (Devaine & Daunizeau's k-ToM). Competition rewards it;
# over-attributing it is a rout; and depth can be READ from moves alone.
from soma.narrative import tournament, play, detect_depth

t = tournament((0, 1, 2), rounds=40, reps=12)
print(t.render())
print()
strict = play(2, 0, infer_level=False, rounds=40, reps=12)
infer  = play(2, 0, infer_level=True,  rounds=40, reps=12)
print(f"over-mentalizing a naive opponent: strict 2-ToM earns "
      f"{strict.score_a:.2f},\nthe level-INFERRING 2-ToM earns "
      f"{infer.score_a:.2f} -- seeing a simple person as a schemer\n"
      "hands them your pattern.")
print()
m = play(0, 1, rounds=120, reps=1, seed=4)
print(detect_depth(m.history, seat=1, candidates=(0, 1, 2)).render())
""")

_ex("lib/pc_tell", "0.22 · the tell", "decisiveness is legibility; the guarded are read",
r"""
# 0.22 -- THE TELL: the more decisively a mind converts its model into action,
# the more legible its pattern is to a mind one level deeper. And decisiveness
# derives from CONVICTION -- so the guarded are read.
from soma.narrative import legibility, face_off, social_params_of
from soma.narrative import guarded, stoic, anxious, tender

print(legibility(betas=(2, 5, 12), rounds=40, reps=12).render())
print()
print("a 2-ToM reader vs 1-ToM hiders of each temperament "
      "(α, β derived from\nprecision and conviction -- the dials that also "
      "drive feeling and choice):")
for t in (guarded, stoic, anxious, tender):
    m = face_off(stoic, t, k_a=2, k_b=1, rounds=40, reps=12)
    a, b = social_params_of(t)
    print(f"  {t.name:<9} (α={a}, β={b:>4}): loses {m.score_a:.2f}")
print()
print("Conviction protects the interior and betrays the surface.")
""")

_ex("lib/pc_legitimacy", "0.25 · legitimacy (system justification)", "the belief that holds the holder; an exit is a solvent",
r"""
# 0.25 -- LEGITIMACY: why the people a system injures defend it (Jost;
# Laurin/Kay; Wakslak). A legitimizing belief's conviction is DERIVED from
# three antecedents -- dependence, inescapability, threat -- and its trust in
# the evidence of harm derived inversely (motivated ignorance). While it
# holds, injury buys quiet at the price of self-worth; when it breaks, the
# grief arrives whole and the outrage becomes available.
from soma.narrative import (Story, guarded, stoic, justifies,
                            palliative_tradeoff, antecedent_dose)

# The widow: dependent on the system, and it is the only world there is.
def widow():
    s = Story("the_feather", span="16s", step="1s", about="acute distress")
    neva = s.character("Neva", temperament=guarded)
    justifies(neva, "perch", dependence=0.9, inescapability=0.9)
    return s

print(palliative_tradeoff(widow, "Neva", harm=6.0).render())
print()

# The exodus curve: nothing changes but the thinkability of leaving.
def drifter(inescapability):
    s = Story("the_quarter", span="16s", step="1s", about="acute distress")
    d = s.character("Drifter", temperament=stoic)
    justifies(d, "perch", dependence=0.85, inescapability=inescapability)
    return s

print(antecedent_dose(drifter, "Drifter",
                      levels=(0.95, 0.5, 0.1)).render())
""")

_ex("lib/pc_files", "files · SOMA files, from Python", "write a .soma file, run it with run_file, change a dial, diff the endings",
r"""
# FILES -- write a SOMA file here, run it through the library, change one
# number, and diff the endings. Files saved with the Save button (either
# editor) appear in "Your files" and are visible to this code -- and files
# written here appear in the rail after the run.
src = '''
sim { duration: 6s  dt: 1s }
body Vera @cardiac { intero heart : BPM baseline 70 }
stimulus heart { at 2s: 120 }
loop noticing @cardiac {
  prior:      predict(70)
  sense:      heart
  precision:  0.9
  conviction: 0.3
  act { emit feel(surprise) }
}
'''
with open("first_light.soma", "w") as f:
    f.write(src)

print("workspace now holds:"); workspace(); print()

def feelings(res):
    out = []
    for e in res.chronicle:
        if e.kind == "emit":
            q = str(e.detail.get("quale"))
            q = q.replace("Qualia<", "").rstrip(">")
            out.append(f"{q} at {e.t:g}s")
            break                      # the first is the story
    return ", ".join(out) or "nothing"

print("as written (trusts the senses)  ->", feelings(run_file("first_light.soma")))

# one dial changed: precision so low the racing heart never registers
r2 = run_source(src.replace("precision:  0.9", "precision:  0.05"),
                title="first_light (numb)")
print("at precision 0.05 (numb)        ->", feelings(r2),
      " -- the same heart, unfelt")
""")

_ex("capstone/four_ways_of_leaving", "capstone · four ways of leaving", "attachment, appraisal, and circumplex -- preregistered end to end",
r"""
'''
four_ways_of_leaving: the 0.8 prediction layers, end to end.

One person leaves a room. The library predicts, before any run, four different
people it could happen to -- and then the confabulation gap that only one of
them will show; the emotion a verdict will produce in a fifth person who was
never told what to feel; what happens between two cold negotiators who
correspond perfectly and can't stand each other; and it seals every claim in a
preregistration before checking any of them.

Everything here is a forecast first and a run second. Where a forecast fails,
the report says FALSIFIED -- that is the point of the instrument.

    python3 examples/narrative/four_ways_of_leaving.py
'''
from soma.narrative import (Story, anxious, stoic, trusting, guarded, volatile,
                            predict_feeling, predict_pull, Stance)


def separations():
    '''Four attachment styles; one separation probe; four staked forecasts.'''
    print("=" * 72)
    print("I. FOUR WAYS OF BEING LEFT (soma.narrative.attachment)")
    print("=" * 72)
    for style, temp in (("secure", trusting), ("anxious", anxious),
                        ("avoidant", stoic), ("disorganized", guarded)):
        story = Story(f"leaving_{style}", span="12s", step="1s",
                      about="separation distress")
        mara = story.character("Mara", temperament=temp)
        mara.attaches(style, to="Jonah")
        print()
        print(story.predict_separation("Mara").render())


def the_verdict():
    '''The author supplies the appraisal; the library derives the emotion --
    and then must produce it.'''
    print()
    print("=" * 72)
    print("II. THE VERDICT SHE NEVER NAMED (soma.narrative.appraisal)")
    print("=" * 72)
    # theory-side, before any story exists:
    pf = predict_feeling(congruence=-0.9, agency="other", certainty=0.9,
                         coping=0.2)
    print(f"\n  appraisal: harmful, other-caused, certain, powerless")
    print(f"  {pf.gloss()}")

    story = Story("the_verdict", span="8s", step="1s")
    vera = story.character("Vera", temperament=anxious)
    vera.senses("verdict")
    vera.appraises_event("verdict", congruence=-0.9, agency="other",
                         certainty=0.9, coping=0.2,
                         when="verdict > 5", drives="heart", to=112,
                         fades_to=72)
    story.at("2s", vera.hears("verdict", 9))

    audit = story.preregister()
    audit.expect_feeling("Vera", pf.quale, by="4s")
    audit.expect_peak("Vera", "heart", at_least=105)
    print()
    print(audit.check().render())

    # construct validity: the forward map (appraisal->emotion) is only a real
    # prediction if it is IDENTIFIABLE -- if the inverse (emotion->appraisal)
    # recovers the same emotion for every one in the vocabulary. The same
    # blind-recovery standard the Strange Situation meets.
    from soma.narrative import check_identifiability, explain_emotion
    v = check_identifiability()
    print(f"\n  construct validity — forward and inverse mappings consistent "
          f"for all\n  {v['n']} emotions: {v['recovered']} "
          f"({v['n_correct']}/{v['n']} round-trip). The map is identifiable,")
    print("  so the forecast is a prediction, not a label. And it runs "
          "backward —")
    print("  from the feeling observed to the reading of the world behind it:")
    for emo in ("resentment", "grief", "relief"):
        print(f"    {explain_emotion(emo)}")


def the_negotiation():
    '''Two cold, dominant people: perfect correspondence on warmth, collision
    on dominance -- structurally complementary, affectively corrosive.'''
    print()
    print("=" * 72)
    print("III. THE NEGOTIATION (soma.narrative.circumplex)")
    print("=" * 72)
    pull = predict_pull(Stance(dominance=0.6, warmth=-0.6))
    print(f"\n  Rook's opening {Stance(0.6, -0.6).octant()} move {pull.gloss()}")
    print()
    story = Story("the_negotiation", span="14s", step="1s")
    rook = story.character("Rook", temperament=guarded).stance(
        dominance=0.6, warmth=-0.6)
    wren = story.character("Wren", temperament=volatile).stance(
        dominance=0.5, warmth=-0.5)
    story.meet(rook, wren)
    print(story.predict_dyad(rook, wren).render())


separations()
the_verdict()
the_negotiation()
""")

_ex("capstone/anatomy_of_a_breaking", "capstone · the anatomy of a breaking", "every insight tool on one man: sensitivity, discrimination, early warning, counterfactual, preregistration",
r"""
'''
the_anatomy_of_a_breaking: every study instrument turned on one man.

Halvor kept the harbor ledger for thirty-one years, and believes the only
reason anyone is kept is that they are needed. His granddaughter keeps
visiting anyway -- no errand, no use for him at all -- and that useless,
persistent regard is the evidence his belief cannot metabolize.

The story is small on purpose. The point of this file is the STUDY: five
instruments, each answering a different question about the same predictive
characterization, each checked against real runs:

  I.    the run itself         what actually happens
  II.   sensitivity            which dial writes this ending (Sobol indices)
  III.  discrimination         which scene would separate two readings of him
  IV.   early warning          is the break legible before it happens
  V.    minimal intervention   what smallest change would have prevented it
  VI.   preregistration        the study's own conclusions, staked and checked

    python3 examples/narrative/the_anatomy_of_a_breaking.py
'''
from soma.narrative import Story, stoic


LIE = "the_lie_kept_means_needed"


def build(regard="rising"):
    s = Story("the_anatomy_of_a_breaking", span="20s", step="1s",
              about="a defended belief, slowly overwhelmed by regard")
    halvor = s.character("Halvor", temperament=stoic)
    halvor.senses("her_visits")
    halvor.believes("kept_means_needed",
                    claim="the only reason anyone is kept is that they are needed",
                    disconfirmed_by="her_visits", breakable=True,
                    conviction=0.88)
    halvor.learns(0.02)
    # the regard agitates the body it contradicts: visits he cannot account
    # for drive the heart, and grief is read off the heart a beat later
    halvor.appraises("her_visits", drives="heart", to=95,
                     when="her_visits > 5", fades_to=72)
    halvor.feels("grief", from_body="heart", threshold=80)
    halvor.narrates(downplaying={"grief": "It's just the cold in this office."})
    # her visits: useless regard. "rising": steady and a little warmer each
    # year (the life that breaks him). "faint": dutiful and thin -- reads at
    # almost exactly what the lie predicts, so nothing accumulates (the life
    # in which the belief is never tested hard enough to fail).
    for t in range(2, 18):
        v = (round(min(9, 3 + 0.4 * (t - 2)), 1) if regard == "rising"
             else 2.2)
        s.at(f"{t}s", halvor.hears("her_visits", v))
    return s


def study():
    print("=" * 74)
    print("I. THE RUN — what actually happens")
    print("=" * 74)
    s = build()
    r = s.result()
    revs = [e for e in r.chronicle if e.kind == "revelation"]
    print(f"\n  Halvor's lie {'BREAKS at %ds' % revs[0].t if revs else 'holds'} "
          f"under sixteen beats of useless regard.\n")

    print("=" * 74)
    print("II. SENSITIVITY — which dial writes this ending")
    print("=" * 74)
    rep = build().sensitivity(
        params={f"{LIE}.conviction": (0.4, 0.99),
                f"{LIE}.learn": (0.0, 0.15),
                f"{LIE}.precision": (0.2, 0.9)},
        outcome_name="break_time", character="Halvor", n_base=32, seed=7)
    print()
    print(rep.render())
    print()
    print("  (The heavy interaction is not noise; it is a recovered mechanism. "
          "SOMA's\n  auto-break threshold is 6*conviction/precision — a ratio, "
          "so neither dial\n  acts alone by construction. The study, given "
          "only runs, found the ratio.)")
    print()

    print("=" * 74)
    print("III. DISCRIMINATION — the scene that separates two readings")
    print("=" * 74)
    print("\n  Reading A: armor — held hard (conviction .97) and deaf to the")
    print("  evidence (precision .2): he can only suppress, until overwhelmed.")
    print("  Reading B: habit — held loosely (conviction .6), evidence trusted")
    print("  (precision .8): the senses outrank the prior, so he simply updates.")
    rep = build().discriminate(
        "Halvor",
        version_a={f"{LIE}.conviction": 0.97, f"{LIE}.precision": 0.2},
        version_b={f"{LIE}.conviction": 0.6, f"{LIE}.precision": 0.8},
        probes={"her_visits": [2, 4, 6, 9]},
        outcome_name="break_time")
    print()
    print(rep.render())
    print()
    print("  ('never' here does not mean armored: reading B never BREAKS because")
    print("  it never suppresses — the evidence wins arbitration and he changes")
    print("  his mind without a shattering. The same scene separates a man who")
    print("  breaks from a man who quietly revises.)")
    print()

    print("=" * 74)
    print("IV. EARLY WARNING — is the break legible before it happens?")
    print("=" * 74)
    print()
    print(build().predict_break_onset("Halvor", window=5).render())
    print()
    print("  ...and the same instrument on the life where her regard stays "
          "faint\n  (reads at what the lie predicts; nothing accumulates):")
    print()
    print(build(regard="faint").predict_break_onset("Halvor", window=5).render())
    print()

    print("=" * 74)
    print("V. MINIMAL INTERVENTION — what would have prevented it")
    print("=" * 74)
    rep = build().minimal_intervention(
        target=("break", 0.0),
        dials={f"{LIE}.conviction": (0.88, 3.0),
               f"{LIE}.precision": (0.05, 0.35),
               f"{LIE}.learn": (0.0, 0.02)},
        character="Halvor")
    print()
    print(rep.render())
    print()

    print("=" * 74)
    print("VI. PREREGISTRATION — the study's conclusions, staked and checked")
    print("=" * 74)
    s = build()
    audit = s.preregister()
    audit.expect_break("Halvor")
    audit.expect_feeling("Halvor", "grief")
    audit.expect_gap("Halvor", at_least=0.4)   # he downplays while it builds
    print()
    print(audit.check().render())


study()
""")

_ex("capstone/marriage_that_could_have_held", "capstone · the marriage that could have held", "sensitivity + counterfactual, and a computed point of no return",
r"""
'''
the_marriage_that_could_have_held: the study layer turned on a slow curdling.

Soren's delight in Mira depends on her surprising him -- delight_at_error, a
low-conviction prior being sweetly wrong. His `learn` rate is the tragedy dial:
every firing hardens the prior, and the curdling is not that the flicker of
feeling stops -- it is that the ROUTE flips. Early, a surprise routes to
`perceive`: she moves him, his picture of her revises. Late, the same surprise
routes to `act`: he resists it, defends the picture, and the feeling that still
fires is a feeling *about* his model, not about her. Nothing visible changes.
That is the point.

Four studies, each a question a novelist actually asks about this marriage:

  I.    the run              when the route flips: the year he stops taking her in
  II.   sensitivity          is the tragedy the learning, or the trusting?
  III.  counterfactual       the smallest change to him that keeps him open
  IV.   the last good year   the latest year one extraordinary day still REACHES
                             him -- a point of no return, computed, not asserted

Study IV is composed directly from the insight substrate (run_with + the
chronicle) rather than a canned instrument: the substrate is the API, the
instruments are just its most common compositions.

    python3 examples/narrative/the_marriage_that_could_have_held.py
'''
from soma.narrative import Story, tender, arc, run_with, outcome


LOOP = "appraising_her_face"
YEAR = 31557600.0            # one soma year, in the seconds the Chronicle keeps


def build(extraordinary_day=None, learn=0.08):
    '''The marriage. If `extraordinary_day` is (year, value), one unscripted,
    astonishing day is inserted -- the intervention Study IV searches over.'''
    s = Story("the_marriage", span="30y", step="1y", cadence=True,
              about="the slow erosion of intimacy")
    soren = s.character("Soren", temperament=tender, clock="life")
    soren.senses("her_face", baseline=5)
    soren.appraises("her_face", feeling="delight_at_error", when="her_face > 1",
                    precision=0.75, conviction=0.2,
                    updates=True, stops_seeing=True)
    soren.learns(learn)
    s.over(arc.wobble(around=5, span="24y", every="1y", unit="y", amplitude=3),
           lambda v: soren.hears("her_face", v))
    if extraordinary_day is not None:
        year, value = extraordinary_day
        s.at(f"{year}y", soren.hears("her_face", value))
    return s


def study():
    print("=" * 74)
    print("I. THE RUN — the year he stops taking her in")
    print("=" * 74)
    r = run_with(build())
    beats = [(e.t / YEAR, e.detail["route"]) for e in r.chronicle
             if e.kind == "settle" and e.who.endswith(LOOP)]
    first_act = next((y for y, route in beats if route == "act"), None)
    last_perc = max((y for y, route in beats if route == "perceive"), default=None)
    frac = outcome(r, "perceive_frac", character="Soren")
    print(f"\n  her face goes on varying for 24 years. He takes it in "
          f"(`perceive`) for the")
    print(f"  early marriage; the route first flips to resisting (`act`) at "
          f"year {first_act:.0f},")
    print(f"  and the last beat that truly reaches him is year {last_perc:.0f}. "
          f"Over the whole")
    print(f"  marriage the world gets in on only {frac:.0%} of beats. The "
          f"delight still")
    print(f"  flickers afterward — but it is delight at his own model, "
          f"defended.\n")

    print("=" * 74)
    print("II. SENSITIVITY — is the tragedy the learning, or the trusting?")
    print("=" * 74)
    rep = build().sensitivity(
        params={f"{LOOP}.learn": (0.0, 0.12),
                f"{LOOP}.conviction": (0.05, 0.6),
                f"{LOOP}.precision": (0.4, 0.95)},
        outcome_name="perceive_frac", character="Soren",
        n_base=24, seed=11)
    print()
    print(rep.render())
    print()
    print("  (The outcome is the fraction of his life the world still gets in.)")
    print()

    print("=" * 74)
    print("III. COUNTERFACTUAL — the smallest change that keeps him open")
    print("=" * 74)
    base_frac = outcome(run_with(build()), "perceive_frac", character="Soren")
    print(f"\n  target: the world gets in on at least half his beats "
          f"(baseline: {base_frac:.0%}).")
    rep = build().minimal_intervention(
        target=("perceive_frac", 0.5),
        dials={f"{LOOP}.learn": (0.0, 0.08),
               f"{LOOP}.conviction": (0.05, 0.2),
               f"{LOOP}.precision": (0.75, 0.98)},
        character="Soren", steps=16)
    print()
    print(rep.render())
    print()

    print("=" * 74)
    print("IV. THE LAST GOOD YEAR — a point of no return, computed")
    print("=" * 74)
    print("\n  One extraordinary day — her face at 9.5, utterly unforeseen —")
    print("  inserted at year Y. Does it still REACH him (route: perceive),")
    print("  or does he resist it (route: act)?\n")
    last_good = None
    for year in range(2, 26, 2):
        r = run_with(build(extraordinary_day=(year, 9.5)))
        routes = [e.detail["route"] for e in r.chronicle
                  if e.kind == "settle" and e.who.endswith(LOOP)
                  and abs(e.t / YEAR - year) < 0.6]
        reached = "perceive" in routes
        print(f"    year {year:>2d}: "
              f"{'it reaches him — she moves him' if reached else 'he resists it — the picture holds'}")
        if reached:
            last_good = year
    print(f"\n  POINT OF NO RETURN: after year {last_good}, no single day, "
          f"however astonishing,")
    print("  routes to perceive — his hardened prior outranks anything one day "
          "can say.")
    print("  The marriage's fate is settled years before anything visible "
          "happens,")
    print("  and the year it was settled is computable.")


study()
""")

_ex("capstone/five_marriages", "capstone · five marriages", "the Gottman model, the thin slice, and what saves a hostile couple",
r"""
'''
five_marriages: the Gottman-Murray model, run as five marriages.

Gottman and Murray's mathematics of marriage is the most famous predictive
character simulation there is: parameters read off minutes of one conversation
predicted divorce years out. This simulation rebuilds the model in SOMA -- the
influence functions are couple/lag readings, the negative threshold is a guard
level, repair is an interoceptive bid, emotional inertia is conviction -- and
runs the same contentious conversation through all five couple types.

  I.    five couples, one complaint   the typology's forecasts, checked
  II.   the thin slice                the ending forecast from the first
                                      quarter alone -- the minutes-to-years
                                      claim, in-model and falsifiable
  III.  what saves a hostile couple   minimal intervention: is it the skin
                                      (negative threshold) or the repair?
  IV.   the anatomy of the cascade    negative-affect reciprocity as the
                                      absorbing state, measured

    python3 examples/narrative/five_marriages.py
'''
from soma.narrative import Story, tender, trusting, COUPLE_TYPES, marry, gottman_assess


def couple(type_name):
    s = Story(f"marriage_{type_name}", span="20s", step="1s")
    a = s.character("Ash", temperament=trusting)
    b = s.character("Bee", temperament=tender)
    marry(s, a, b, type_name)
    return s


def study():
    print("=" * 74)
    print("I. FIVE COUPLES, ONE COMPLAINT — the typology's forecasts, checked")
    print("=" * 74)
    reports = {}
    for tname in COUPLE_TYPES:
        rep = gottman_assess(couple(tname))
        reports[tname] = rep
        print()
        print(rep.render())

    print()
    print("=" * 74)
    print("II. THE THIN SLICE — the ending, forecast from the first quarter")
    print("=" * 74)
    print()
    print("  couple             slice says   the marriage      forecast")
    hits = 0
    for tname, rep in reports.items():
        actual = "holds" if any("REGULATED" in v[0] and v[3] for v in rep.verdicts) \
                 or rep.stable_forecast and rep.confirmed else "falls"
        # read the actual from the thin-slice verdict's observed field
        thin_v = next(v for v in rep.verdicts if "THIN SLICE" in v[0])
        actual = thin_v[2]
        ok = thin_v[3]
        hits += ok
        print(f"    {tname:<16s} {rep.thin_forecast:<12s} {actual:<16s} "
              f"{'✓ correct' if ok else '✗ wrong'}")
    print(f"\n  {hits}/{len(reports)} endings called from the first quarter of "
          f"one conversation.")
    print("  (Gottman's claim was 94% from minutes of tape; here the mechanism")
    print("  that makes it possible is visible: the slice carries the couple's")
    print("  thresholds, and the thresholds ARE the ending.)")

    print()
    print("=" * 74)
    print("III. WHAT SAVES A HOSTILE COUPLE — the skin, or the repair?")
    print("=" * 74)
    # A hostile couple's two broken dials: a thin skin (friction triggers at
    # received manner <= 4.5) and no repair. Which single change un-cascades
    # them? We test the skin directly: thicken it (lower the guard) until the
    # marriage holds. Repair can't be added by a dial (it is absent wiring),
    # which is itself the finding Gottman's interventions reflect: you can
    # teach repair, but the model must first contain a bid to strengthen.
    s = couple("hostile")
    rep = s.minimal_intervention(
        target=("mood_drift", 0.0),
        dials={"Ash.appraising_their_manner_friction.precision": (0.1, 0.9),
               "Bee.appraising_their_manner_friction.precision": (0.1, 0.9)},
        character="Ash", mood="rapport", steps=16)
    print()
    print(rep.render())
    print()
    print("  (Lowering the friction loop's precision is 'thickening the skin':")
    print("  the same received coldness carries less weight. The instrument")
    print("  reports whether any single skin-thickening saves this marriage,")
    print("  or whether the cascade is over-determined without repair.)")

    print()
    print("=" * 74)
    print("IV. THE ANATOMY OF THE CASCADE — reciprocity as the absorbing state")
    print("=" * 74)
    print()
    print("  couple             negative reciprocity")
    for tname, rep in reports.items():
        bar = "#" * int(rep.reciprocity * 30)
        print(f"    {tname:<16s} {rep.reciprocity:>4.0%}  {bar}")
    print()
    print("  The unstable couples answer friction with friction nearly every")
    print("  beat — Gottman's absorbing state: once in, the cascade feeds")
    print("  itself. The regulated couples' reciprocity is near zero not")
    print("  because nothing negative arrives, but because it is absorbed —")
    print("  by a thicker skin, by repair, or by disengagement.")


study()
""")

_ex("capstone/the_spiral", "capstone · the spiral (panic)", "a positive-feedback loop: the tipping flutter, hysteresis, the exposure margin",
r"""
'''
the_spiral: Clark's cognitive model of panic, as interoceptive inference.

Clark (1986): a panic attack is a positive feedback loop -- a bodily sensation
is catastrophically appraised as danger, the appraisal produces arousal, the
arousal produces more sensation, which confirms the appraisal. The modern
predictive-processing reading (Paulus; Seth) makes it an inference pathology: a
prior that bodily signals mean catastrophe, held with enough weight that the
body's ordinary noise becomes its own evidence.

In SOMA the circle is two verbs: a flutter drives the heart a little, and a
catastrophizing appraisal READS the heart and DRIVES the heart -- the loop
senses the very channel it raises. Everything else is prediction:

  I.    the circle vs. the shrug     same flutter, two priors: one spirals to
                                     an attack, one carries it uninterpreted
  II.   the tipping flutter          the smallest palpitation that panics --
                                     a sharp threshold, found by sweep
  III.  hysteresis                   the attack OUTLIVES its trigger: the
                                     flutter ends and the spiral self-sustains
                                     (bistability), until regulation arrives
  IV.   the exposure margin          interoceptive exposure = raising the
                                     sensation the body can carry without
                                     interpretation; the minimal tolerance
                                     that prevents the attack, computed

Every study here is hand-composed from the insight substrate (run_with +
outcome + series): no new module was needed. The substrate is the API.

    python3 examples/narrative/the_spiral.py
'''
from soma.narrative import Story, anxious, run_with, outcome, series


ATTACK = 115.0     # sustained heart above this = a panic attack, by definition


def build(*, alarm_at=88.0, flutter=6.0, flutter_beats=(3, 4),
          reassurance_at=None):
    '''One person, one flutter, and a prior about what flutters mean.

    alarm_at: the heart level at which the catastrophizing appraisal engages --
              the body's tolerance for its own noise. 999 = no catastrophizing.
    flutter:  the trigger's strength.
    reassurance_at: optionally, a beat at which regulation arrives (a hand on
              the shoulder, a breath count) -- a down-driver on the same heart.
    '''
    s = Story("the_spiral", span="18s", step="1s",
              about="a panic spiral and its breaking")
    p = s.character("Wren", temperament=anxious)
    p.senses("flutter")
    # the sensation: a flutter nudges the heart up -- ordinary, transient
    p.appraises("flutter", when="flutter > 3", drives="heart", to=92,
                fades_to=72, expects=0.0)
    # the circle: the appraisal that READS the heart and RAISES it. This one
    # loop is Clark's model: sensation -> catastrophic appraisal -> arousal ->
    # more sensation. Above `alarm_at`, the body's state is its own evidence.
    p.appraises("heart", as_threat=True, when=f"heart > {alarm_at}",
                drives="heart", to=132, fades_to=72,
                feeling="terror", expects=72.0)
    if reassurance_at is not None:
        p.senses("reassurance")
        p.appraises("reassurance", when="reassurance > 5",
                    drives="heart", to=68, fades_to=72, expects=0.0)
    for b in flutter_beats:
        s.at(f"{b}s", p.hears("flutter", flutter))
    if reassurance_at is not None:
        s.at(f"{reassurance_at}s", p.hears("reassurance", 8))
        s.at(f"{reassurance_at+1}s", p.hears("reassurance", 8))
    return s


def attacked(story):
    r = run_with(story)
    h = series(r, "heart", character="Wren")
    sustained = sum(1 for v in h if v >= ATTACK)
    return sustained >= 3, r


def study():
    print("=" * 74)
    print("I. THE CIRCLE VS. THE SHRUG — same flutter, two priors")
    print("=" * 74)
    got, r1 = attacked(build(alarm_at=88.0))
    h1 = [round(v) for v in series(r1, "heart", character="Wren")]
    terror = outcome(r1, "feel", character="Wren", quale="terror")
    print(f"\n  the catastrophizer (alarm at 88): heart {h1}")
    print(f"    -> ATTACK: {got}; terror fired {terror:.0f} times")
    got2, r2 = attacked(build(alarm_at=999.0))
    h2 = [round(v) for v in series(r2, "heart", character="Wren")]
    print(f"  the shrug (no catastrophic prior): heart {h2}")
    print(f"    -> attack: {got2}; the same flutter, carried uninterpreted\n")

    print("=" * 74)
    print("II. THE TIPPING FLUTTER — the smallest palpitation that panics")
    print("=" * 74)
    print()
    tip = None
    for f in [1, 2, 3, 4, 5, 6, 7, 8]:
        got, _ = attacked(build(alarm_at=88.0, flutter=float(f)))
        print(f"    flutter {f}: {'ATTACK' if got else 'passes'}")
        if got and tip is None:
            tip = f
    print(f"\n  the threshold is SHARP: below flutter {tip} nothing happens at "
          f"all; at {tip}, the")
    print("  full attack. Panic's all-or-nothing character is the signature of "
          "a system")
    print("  with two attractors and a separatrix between them, not of a dial.\n")

    print("=" * 74)
    print("III. HYSTERESIS — the attack outlives its trigger")
    print("=" * 74)
    got, r = attacked(build(alarm_at=88.0, flutter_beats=(3, 4)))
    h = series(r, "heart", character="Wren")
    t = r.times
    after_trigger = [round(v) for v, tt in zip(h, t) if tt >= 6]
    print(f"\n  the flutter ends at 5s. The heart, after: {after_trigger}")
    print("  The spiral is SELF-SUSTAINING: heart above the alarm keeps the")
    print("  appraisal firing, which keeps the heart above the alarm. Two")
    print("  stable states — rest and attack — and the flutter only chose")
    print("  between them. The way back is not the way in:")
    got_r, rr = attacked(build(alarm_at=88.0, reassurance_at=9))
    hr = [round(v) for v in series(rr, "heart", character="Wren")]
    print(f"\n  with regulation arriving at 9s: heart {hr}")
    print("  Removing the trigger did nothing; only a DOWN-driver — the")
    print("  regulation the spiral itself cannot supply — exits the attack")
    print("  state. (Cramer & Borsboom's hysteresis in symptom networks: the")
    print("  path out requires more than undoing the path in.)\n")

    print("=" * 74)
    print("IV. THE EXPOSURE MARGIN — the tolerance that prevents the attack")
    print("=" * 74)
    print()
    print("  Interoceptive exposure works by habituation: the sensation level")
    print("  the body can carry WITHOUT engaging the catastrophic appraisal")
    print("  rises. Sweeping that tolerance against the same flutter:")
    print()
    margin = None
    for alarm in [86, 88, 90, 92, 94, 96, 98]:
        got, _ = attacked(build(alarm_at=float(alarm)))
        print(f"    tolerance {alarm}: {'ATTACK' if got else 'no attack'}")
        if not got and margin is None:
            margin = alarm
    print(f"\n  THE MARGIN: tolerance {margin} is enough — the flutter peaks at "
          f"92, so the")
    print("  therapy has a computable target: teach the body to carry 92")
    print("  uninterpreted, and this trigger cannot reach the circle at all.")
    print("  The prediction is quantitative and falsifiable per-person: the")
    print("  margin is the flutter's peak, not a universal number.")


study()
""")

_ex("capstone/the_strange_situation", "capstone · the Strange Situation, in full", "four children, one script, and construct validity turned on itself",
r"""
'''
the_strange_situation: the canonical probe, run whole, and turned on itself.

Ainsworth's Strange Situation is the most consequential standardized experiment
in the study of character: eight scripted episodes -- play, a stranger, two
separations, two reunions -- and a coding scheme that reads a child's whole
relational pattern from four behaviors in the two reunions. This simulation
runs the entire protocol on SOMA children and then makes the strongest claim a
model of the instrument can make:

  I.    four children, one script    the same eight episodes produce four
                                     textbook-distinct coded profiles
  II.   construct validity           the classifier never sees the installed
                                     style, only the behavior stream -- and
                                     must recover all four (parameter recovery,
                                     the identifiability standard)
  III.  the child nobody labeled     a hand-built child, no style installed
                                     from the table, classified honestly from
                                     tape -- what the instrument is FOR
  IV.   what the tape can't show     the avoidant child's narrated calm over a
                                     racing heart, preregistered and checked

    python3 examples/narrative/the_strange_situation.py
'''
from soma.narrative import (Story, trusting, anxious, stoic, guarded,
                            strange_situation, validate_instrument)


TEMPS = {"secure": trusting, "anxious": anxious,
         "avoidant": stoic, "disorganized": guarded}


def child_with(style):
    s = Story(f"ss_{style}", span="24s", step="1s",
              about="separation distress in a standardized protocol")
    child = s.character("Noa", temperament=TEMPS[style])
    child.attaches(style, to="mother")
    return s, child


def study():
    print("=" * 74)
    print("I. FOUR CHILDREN, ONE SCRIPT — the protocol codes them apart")
    print("=" * 74)
    for style in TEMPS:
        s, c = child_with(style)
        print()
        print(f"  [installed: {style} — the coder below never sees this]")
        print(strange_situation(s, c).render())

    print()
    print("=" * 74)
    print("II. CONSTRUCT VALIDITY — blind recovery of every installed style")
    print("=" * 74)
    results = validate_instrument(child_with)
    print()
    for style in TEMPS:
        mark = "✓" if results[style] == style else "✗"
        print(f"    {mark} installed {style:<13s} -> classified {results[style]}")
    print(f"\n    INSTRUMENT {'VALID' if results['recovered'] else 'INVALID'}: "
          f"{'all four styles recovered from behavior alone' if results['recovered'] else 'recovery failed'}")

    print()
    print("=" * 74)
    print("III. THE CHILD NOBODY LABELED — classification as discovery")
    print("=" * 74)
    # a hand-built child: no style bundle. High-precision alarm, a hair-trigger
    # protest, contact sought hard but never soothing -- built from raw verbs,
    # the way an author actually works.
    s = Story("ss_unlabeled", span="24s", step="1s",
              about="separation distress in a standardized protocol")
    kit = s.character("Kit", temperament=anxious)
    kit.senses("mother_near", baseline=8.0)
    kit.appraises("mother_near", as_threat=True, when="mother_near < 3",
                  drives="heart", to=122, fades_to=101, precision=0.97,
                  conviction=0.2, expects=8.0,
                  shows_on="protest_face", shows_value=9.0)
    kit.feels("dread", from_body="heart", threshold=95.0)
    kit.appraises("mother_near", when="mother_near * heart > 650",
                  shows_on="clings", shows_value=9.0, expects=8.0)
    kit.appraises("mother_near", when="mother_near * heart > 700",
                  shows_on="protest_face", shows_value=8.0, expects=8.0)
    kit._attachment = dict(style="?", figure="mother", near="mother_near",
                           resting=72.0, arousal_to=122.0)
    rep = strange_situation(s, kit)
    print()
    print(rep.render())
    print("\n  (No table was consulted. The tape says who this child is: the")
    print("  clinging that will not soothe — coded as the pattern it matches.)")

    print()
    print("=" * 74)
    print("IV. WHAT THE TAPE CAN'T SHOW — preregistered, then checked")
    print("=" * 74)
    s, c = child_with("avoidant")
    audit = s.preregister()
    audit.expect_gap("Noa", at_least=0.4)      # says calm...
    audit.expect_peak("Noa", "heart", at_least=95)  # ...over a racing heart
    audit.expect_feeling("Noa", "dread")
    # run the protocol timeline through the same story so the claims are
    # checked against the actual Strange Situation, not an empty room
    rep = strange_situation(s, c)   # (installs the protocol wiring)
    print()
    print("  The avoidant child LOOKS calm on the tape. The instrument that")
    print("  sees both registers — the narrated account and the body's own")
    print("  record — was preregistered to find them split:")
    print()
    print(f"  physiological arousal over displayed calm: "
          f"{'PRESENT — confirmed' if rep.physio_over_display else 'absent — falsified'}"
          f" (peak {rep.detail['peak']}, classified {rep.classification})")
    print("\n  (Sroufe & Waters 1977; Diamond et al. 2006: the A-pattern's")
    print("  independence is a performance the heart never joins.)")


study()
""")

_ex("capstone/twelve_seconds_in_a_jury_room", "capstone · twelve seconds in a jury room", "the drift-diffusion model, the tell of a bias, and a hung-verdict deadline",
r"""
'''
twelve_seconds_in_a_jury_room: the drift-diffusion model, run as character.

Every other SOMA layer predicts what a character feels or becomes. This one
predicts something the others never touch and the lab measures to the
millisecond: HOW LONG a decision takes and HOW OFTEN it is wrong. The
drift-diffusion model (Ratcliff; Gold & Shadlen) is the dominant account of
speeded two-choice decisions -- a noisy accumulation of evidence to a boundary
-- and it makes distributional predictions no deterministic model can:
right-skewed reaction times, error responses shaped differently from correct
ones, and the speed-accuracy tradeoff traced from a single dial.

Four jurors face the same ambiguous evidence. What differs is how each decides.

  I.    four ways to decide       the same evidence, four RT/accuracy
                                  signatures -- caution, acuity, and bias, each
                                  a different DDM parameter
  II.   the tell of a bias        the prejudiced juror's correct verdicts come
                                  fast and their errors come SLOW -- the
                                  fingerprint of a mind that leaned before it
                                  looked, which a symmetric model cannot show
  III.  the speed-accuracy dial   one juror, told to hurry then to be sure:
                                  the tradeoff traced from the boundary alone,
                                  dissociating caution from ability
  IV.   the deadline              a hung verdict clock: how accuracy collapses
                                  as the time to decide is cut -- computed, and
                                  a foreman's dilemma made quantitative

This is also where SOMA gains stochasticity: the accumulation is noisy but
seeded, so every distribution here is reproducible and the deterministic core
of every earlier layer is untouched.

    python3 examples/narrative/twelve_seconds_in_a_jury_room.py
'''
from soma.narrative import Story, trusting, DECISION_STYLES
from soma.narrative.decision import DecisionStyle, predict_decision


NAMES = {"deliberate": "Halden the careful",
         "impulsive": "Reine the quick",
         "keen": "Ada the sharp-eyed",
         "prejudiced": "Coll the sure"}


def study():
    print("=" * 74)
    print("I. FOUR WAYS TO DECIDE — same evidence, four signatures")
    print("=" * 74)
    print()
    print("    juror                accuracy   RT (correct)   RT (error)   skew")
    print("    " + "-" * 66)
    for style, who in NAMES.items():
        s = Story("jury", span="1s", step="1s", about="a verdict")
        j = s.character("Juror", temperament=trusting)
        s.decides(j, style=style)
        r = s.predict_decision("Juror", trials=4000, seed=3)
        print(f"    {who:<20s} {r.accuracy:>6.0%}      {r.mean_rt:>6.2f}s      "
              f"{r.mean_rt_error:>6.2f}s     {r.skew:+.2f}")
    print()
    print("  Halden (wide boundary) is slow and right; Reine (narrow) is quick")
    print("  and often wrong -- same evidence quality, opposite caution. Ada")
    print("  (high drift: she simply sees more) is fast AND right, the one")
    print("  combination caution alone can't buy. Every RT distribution leans")
    print("  right, the DDM's fingerprint.")

    print()
    print("=" * 74)
    print("II. THE TELL OF A BIAS — fast convictions, slow acquittals")
    print("=" * 74)
    s = Story("jury", span="1s", step="1s", about="a verdict")
    j = s.character("Juror", temperament=trusting)
    s.decides(j, style="prejudiced")
    r = s.predict_decision("Juror", trials=6000, seed=3)
    print(f"\n  Coll starts already leaning toward 'guilty'. When the evidence")
    print(f"  agrees, the verdict comes fast: {r.mean_rt:.2f}s. When the")
    print(f"  evidence points the other way, the walk has to climb all the way")
    print(f"  back across the room, and the RARE correct acquittal is SLOW:")
    print(f"  {r.mean_rt_error:.2f}s — {r.mean_rt_error - r.mean_rt:+.2f}s slower.")
    print(f"\n  That asymmetry — fast one way, slow the other — is the")
    print(f"  fingerprint of a prior. A juror without one shows no such gap; a")
    print(f"  symmetric model cannot produce it at all. The bias is legible in")
    print(f"  the TIMING even when the verdict is correct.")

    print()
    print("=" * 74)
    print("III. THE SPEED-ACCURACY DIAL — hurry, then be sure")
    print("=" * 74)
    s = Story("jury", span="1s", step="1s", about="a verdict")
    j = s.character("Juror", temperament=trusting)
    s.decides(j, drift=0.13, boundary=1.0)
    sat = s.speed_accuracy("Juror", boundaries=[0.5, 0.8, 1.1, 1.5, 2.0],
                           trials=4000, seed=3)
    print()
    print(sat.render())
    print()
    print("  One juror, one evidence quality, five instructions from the")
    print("  foreman — from 'we haven't got all day' to 'be certain'. The")
    print("  tradeoff is smooth and monotone, and it dissociates two things")
    print("  ordinary language conflates: this is the SAME juror being more")
    print("  careful, not a better one. Only the boundary moved.")

    print()
    print("=" * 74)
    print("IV. THE DEADLINE — how accuracy collapses under the clock")
    print("=" * 74)
    print("\n  The judge imposes a deadline: decide within T, or it's a mistrial.")
    print("  We read accuracy AMONG the verdicts actually returned in time,")
    print("  for a careful juror (wide boundary) as the clock tightens:\n")
    base = DecisionStyle(drift=0.12, boundary=1.6, start_bias=0.5,
                         nondecision=0.2)
    s = Story("jury", span="1s", step="1s", about="a verdict")
    j = s.character("Juror", temperament=trusting)
    s.decides(j, drift=0.12, boundary=1.6)
    full = s.predict_decision("Juror", trials=6000, seed=3)
    import random
    print("    deadline    verdicts returned    accuracy of those")
    for deadline in [1.0, 1.5, 2.0, 3.0, 5.0, 99.0]:
        # re-run the raw walks, censoring at the deadline
        rng = random.Random(3)
        from soma.narrative.decision import _one_trial
        st = base
        n_in, n_corr = 0, 0
        for _ in range(6000):
            ok, rt = _one_trial(st, rng)
            if ok is not None and rt <= deadline:
                n_in += 1
                n_corr += (ok is True)
        acc = n_corr / n_in if n_in else 0.0
        pct = n_in / 6000
        label = "none" if deadline == 99.0 else f"{deadline:.1f}s"
        print(f"      {label:<9s}   {pct:>6.0%}               {acc:>5.0%}")
    print()
    print("  A tight deadline doesn't just lose the slow deciders — it")
    print("  systematically keeps the EASY verdicts (which finish first) and")
    print("  discards the hard ones, so the returned verdicts look accurate")
    print("  while the hard cases go undecided. The foreman's real dilemma,")
    print("  made quantitative: haste doesn't lower accuracy evenly, it hides")
    print("  the cases that most needed the time.")


study()
""")

_ex("capstone/what_the_body_learns", "capstone · what the body learns", "conditioning and learned helplessness, run as one study",
r"""
'''
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
'''
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


conditioning_study()
helplessness_study()
""")

_RAIL_ORDER = [
    "lib/hello", "lib/see_the_soma", "lib/handwritten_soma",
    "lib/appraisal", "lib/preregister", "lib/attachment", "lib/predict_break",
    "lib/conditioning", "lib/helplessness", "lib/decision",
    "lib/strange_situation", "lib/gottman",
    "lib/sensitivity", "lib/counterfactual",
    "lib/pc_signature", "lib/pc_portrait", "lib/pc_network", "lib/pc_diary",
    "lib/pc_choice", "lib/pc_other_mind", "lib/pc_tell", "lib/pc_legitimacy",
    "lib/pc_files",
    "capstone/four_ways_of_leaving", "capstone/anatomy_of_a_breaking",
    "capstone/marriage_that_could_have_held", "capstone/five_marriages",
    "capstone/the_spiral", "capstone/the_strange_situation",
    "capstone/twelve_seconds_in_a_jury_room", "capstone/what_the_body_learns",
]


def as_payload():
    by_key = {e["key"]: e for e in EXAMPLES}
    ordered = [by_key[k] for k in _RAIL_ORDER if k in by_key]
    # append any not listed (defensive: never drop an example)
    ordered += [e for e in EXAMPLES if e["key"] not in _RAIL_ORDER]
    return ordered
