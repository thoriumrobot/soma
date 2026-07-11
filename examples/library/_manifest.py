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
"""
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
"""
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
"""
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
        print(f"{e.t:>4}s  felt {e.detail.get('quale')}")
""")

# --------------------------------------------------------------------------
_ex("lib/predict_break", "predict · the tipping point", "forecast a break before it happens",
"""
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
"""
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
"""
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
"""
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
"""
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
"""
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
"""
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
"""
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
"""
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
"""
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
"""
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
_RAIL_ORDER = [
    "lib/hello", "lib/see_the_soma", "lib/handwritten_soma",
    "lib/appraisal", "lib/preregister", "lib/attachment", "lib/predict_break",
    "lib/conditioning", "lib/helplessness", "lib/decision",
    "lib/strange_situation", "lib/gottman",
    "lib/sensitivity", "lib/counterfactual",
]


def as_payload():
    by_key = {e["key"]: e for e in EXAMPLES}
    ordered = [by_key[k] for k in _RAIL_ORDER if k in by_key]
    # append any not listed (defensive: never drop an example)
    ordered += [e for e in EXAMPLES if e["key"] not in _RAIL_ORDER]
    return ordered
