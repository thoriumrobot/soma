# Predictive Character Simulation with SOMA — A Tutorial

*How to build characters that can be **predicted**, and how those predictions
become novelistic insight.*

This tutorial teaches the high-level SOMA library (`soma.narrative`): a way to
describe a fictional person in feelings, beliefs, and relationships, run them
forward in time, and then ask the kinds of questions a novelist asks — *when
would this person break? what is she really feeling under the composure? what
single thing, changed, would have saved this marriage?* The library answers
those questions with staked, checkable predictions rather than assertions.

You do not need to install anything. Everything here runs in your browser.

**A companion tutorial.** This document covers the *prediction* layers —
appraisal, attachment, tipping points, conditioning, the Gottman model,
drift-diffusion decisions, and the sensitivity/counterfactual insight tools. Its
companion, [`TUTORIAL_CHARACTERIZATION.md`](TUTORIAL_CHARACTERIZATION.md),
covers the later *predictive characterization* layers — the behavioral
signature, self-guides, state distributions, phase landscapes, symptom
networks, the inverse problem, choice under active inference, and recursive
theory of mind. The two are complementary; read either first.

---

## Part 0 — Running code as you read

Open **`index.html`** (or `soma_playground.html`) in any modern browser. It
loads a real Python interpreter (via Pyodide, ~10 MB the first time, cached
after) and runs the actual SOMA library — the same code the command line runs,
not a re-implementation.

At the top of the page is a **mode switch** with two buttons:

- **SOMA** — the base language: bodies, loops, stimuli, written by hand.
- **Library** — the high-level `soma.narrative` API, written as Python. **This
  is the mode this tutorial uses.**

Click **Library**. You will see:

- a **left rail** of ready-to-run examples (the same ones this tutorial walks
  through),
- a **code editor** in the middle,
- an **output pane** on the right,
- a **▶ Run** button (or press **Ctrl/⌘ + Enter**).

To follow along: click **Library**, paste any code block from this tutorial into
the editor, and press **Run**. The output pane will show exactly the output
printed in this tutorial. Click **New** to start from a blank Python file, or
pick an example from the rail to load it.

Two things worth knowing:

1. **Both directions work on one page.** Library code can run *hand-written
   SOMA text* through `run_source(...)`, and any character you build with the
   library can print the SOMA it compiles to with `story.source()`. You can
   write SOMA, drive it from Python, read the SOMA back — all in the same
   editor.
2. **Errors are friendly.** If your code raises, you get a red banner with just
   your own traceback (no interpreter internals), and partial output up to the
   error is preserved.

Everything below is real, runnable code with its real output.

---

## Part 1 — The basic idea in one example

A SOMA character is built around a **loop**: a small predictive process that
holds an expectation, senses the world, computes the gap between them
(*prediction error*), and either updates its belief or acts. That one loop is
enough to model a surprising amount of inner life. The high-level library lets
you write it in the vocabulary of a person rather than a control system.

Here is the smallest useful program. A character named Wen sees a face she likes.

```python
# The high-level library: describe a person in feelings and beliefs, and it
# compiles to SOMA and runs. Press Run.
from soma.narrative import Story, tender

story = Story("hello", span="8s", step="1s", about="a first delight")
c = story.character("Wen", temperament=tender)
c.senses("her_face")
c.appraises("her_face", feeling="delight", when="her_face > 3")

story.at("2s", c.hears("her_face", 7))
print(story.run(width=76))
```

**Output:**

```
─────────────────────────────── SOMA · hello ───────────────────────────────
╭─ BODY · channels over time ──────────────────────────────────────────────╮
│   extero her_face     ▁▁███████  0→7
╰──────────────────────────────────────────────────────────────────────────╯
╭─ NARRATOR vs GROUND TRUTH ───────────────────────────────────────────────╮
│   THE STORY SHE TELLS                   THE BODY'S RECORD
│   ───────────────────────────────────────────────────────────────────────
│                                       │ 2.0s (7x) feels Qualia<delight>
╰──────────────────────────────────────────────────────────────────────────╯
╭─ WINNOW-S · storyful moments, ranked ────────────────────────────────────╮
│   ████████·· delight in error
│      7 times across 6.0s the prediction failed and the failure felt like
│      delight -- being surprised, and glad of it.
╰──────────────────────────────────────────────────────────────────────────╯
╭─ CHRONICLE · trace (17 of 17 events) ────────────────────────────────────╮
│     0.0s settle   appraising_h sense=0.0 belief=0.0 error=0.0 pi_s=0.88 …
│     2.0s stimulus her_face     value=7.0
│     2.0s settle   appraising_h sense=7.0 belief=0.0 error=6.16 pi_s=0.88…
│     2.0s emit     appraising_h quale=Qualia<delight>
│     …
╰──────────────────────────────────────────────────────────────────────────╯
```

**How the code maps to the output, line by line:**

- `Story("hello", span="8s", step="1s")` sets up an 8-second simulation ticking
  once per second. Time in SOMA is literal; every row of the trace is one tick.
- `story.character("Wen", temperament=tender)` creates a person. A *temperament*
  is a bundle of defaults for how strongly she trusts her senses versus her
  expectations — `tender` means open, responsive, easily moved.
- `c.senses("her_face")` gives Wen an *exteroceptive channel* — something she can
  perceive from the outside world. You can see it in the **BODY** panel:
  `her_face` starts at 0 and jumps to 7 (the `▁▁███████` sparkline).
- `c.appraises("her_face", feeling="delight", when="her_face > 3")` is the loop:
  *when the face is present (> 3), feel delight.* This is what fires seven times
  in the trace (`emit … quale=Qualia<delight>`).
- `story.at("2s", c.hears("her_face", 7))` is the event: at 2 seconds, the face
  appears at strength 7. That is the `stimulus her_face value=7.0` row.

The **WINNOW-S** panel is the first hint of what makes this a *character*
simulation and not a state machine. It automatically finds the storyful pattern:
the delight is *delight in error* — Wen predicted nothing (`belief=0.0`), the
face arrived (`sense=7.0`), and the large prediction error (`error=6.16`) is
itself what feels like delight. That is a real theory of a particular kind of
joy: the pleasure of being happily surprised. The library found it in the run;
nobody wrote "she is happily surprised."

The **NARRATOR vs GROUND TRUTH** panel is the other key idea: SOMA always keeps
two records — what the character would *say* is happening, and what her *body*
actually did. When those diverge, you have the material of fiction. (Here they
agree; later they will not.)

---

## Part 2 — Three concepts you need

### 2.1 Everything is ordinary SOMA underneath

The library is a convenience. Whatever you build compiles to plain SOMA source
you can read, edit, and run directly. Print it with `.source()`:

```python
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
```

**Output:**

```
// kept -- generated by soma.narrative
// Every construct below was produced from a high-level narrative description;
// it is ordinary SOMA and can be edited, run, sifted, prosed, and perturbed.
@consent("a defended belief")

sim { duration: 14s  dt: 1s }

body Ink_body @cardiac {
  extero kept_for_nothing : Signal baseline 0
  intero only_needed_seen : Signal baseline 0
}

loop the_lie_only_needed @cardiac {
  prior:      predict(2)
  sense:      kept_for_nothing
  precision:  0.35
  conviction: 0.85
  learn:      0.03
  overwhelm:  auto
  act {
    update -> the_truth_about_only_needed
    emit feel(worthlessness) when kept_for_nothing < 3
    move ! set(only_needed_seen, 9) when perceiving
  }
}

stimulus kept_for_nothing { at 2s: 8  at 3s: 8  at 4s: 8  ... }
```

Notice what `believes(..., breakable=True)` compiled to: a loop with **high
conviction** (`0.85`) and **low precision** (`0.35`) — a mind that trusts its
belief far more than the evidence — plus a slow `learn` rate that hardens the
belief every time it is confirmed, and an `overwhelm: auto` clause that lets the
belief eventually **break** if the disconfirming evidence accumulates past a
threshold. That whole structure came from one English-like line. This is the
value of the high-level layer: it encodes the *mechanism* of a defended belief
so you can think in characters, not dials.

### 2.2 You can write SOMA by hand and run it too

The bridge goes the other way. Write SOMA source as a string and run it through
`run_source`:

```python
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
```

**Output:**

```
 2.0s  felt Qualia<surprise>
 3.0s  felt Qualia<surprise>
 4.0s  felt Qualia<surprise>
 5.0s  felt Qualia<surprise>
 6.0s  felt Qualia<surprise>
```

The heart is predicted at 70, jumps to 120 at 2s, and the loop — trusting its
senses (`precision: 0.9`) over its expectation (`conviction: 0.3`) — registers
surprise every tick the mismatch persists. The `run_source` result is a
`Result` object whose `.chronicle` is the full event log; you can read it in
Python however you like.

### 2.3 The Chronicle is the ground truth; predictions read it

Every run produces a **Chronicle** — a timestamped list of everything that
happened: `settle` (the loop resolved a tick), `emit` (a feeling fired),
`revelation` (a belief broke), `narrate` (the narrator spoke), and more. Every
predictive tool in this tutorial works by **reading the Chronicle**: running the
character forward and measuring what the body actually did. Predictions are
never assertions about a real person — they are measurements of what *this model*
does. The library is careful to say so.

---

## Part 3 — The predictive simulations, simple to complex

Everything so far was descriptive: build a character, watch them run. The rest
of the tutorial is about **prediction** — staking a claim about what a character
*would* do in a situation the author never scripted, and checking it against the
run. Each simulation below is a documented psychological model rebuilt in SOMA,
and each makes a *falsifiable* claim: a signature result a weaker account could
not produce.

The order runs from the simplest to the most complex. We begin with a pure
function (an emotion from four numbers, no simulation at all), then introduce the
one method every later prediction relies on — preregistration — and only then
turn to the simulations proper, ending with the standardized multi-episode
protocols that classify a character blind from behavior.

### 3.1 Appraisal — predicting the *feeling* from the situation

**The idea.** Appraisal theory (Scherer, Smith & Ellsworth, the OCC model) holds
that an emotion is not caused by an event but by a person's *reading* of it along
a few dimensions: was this good or bad for what I wanted (congruence)? who caused
it (agency)? is it settled (certainty)? can anything be done (coping)? Give those
dimensions and the specific discrete emotion follows. Because the reading, not
the event, produces the feeling, the same event appraised two ways yields two
emotions — the reason two people respond differently to one piece of news.

The library implements the forward map (appraisal → emotion) and, more strongly,
its **inverse** (emotion → the appraisal that must have produced it), plus a
check that the two are mutually consistent for all 14 emotions.

```python
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
```

**Output:**

```
wronged, with power              -> anger  (move against)
wronged, powerless               -> resentment  (withhold)
a certain, uncontrollable loss   -> grief  (withdraw and search)

construct validity: all 14 emotions recover (True)

grief: they construed that bad for what they wanted, no one caused it, it is settled, nothing can be done — and so are moved to withdraw and search -- deactivate, and reach for what is gone
```

**What the output means.** The first three lines are the whole of appraisal
theory in miniature. Notice the first two rows: *the same bad event, the same
other-blame, the same certainty* — only the sense of **power** differs. With
power, the reading produces **anger** and the impulse to *move against*. Without
power, the identical situation produces **resentment** and the impulse to
*withhold* — anger with nowhere to go. That single dimension is the difference
between confrontation and a grudge. A novelist knows this intuitively; here it
is mechanized.

`construct validity: all 14 emotions recover (True)` earns the word
*prediction*. A forward map from appraisal to emotion is only a genuine
prediction, rather than an arbitrary labeling, if it is **identifiable**: you
must be able to run it backwards and recover the same emotion. The library checks
all 14 emotions round-trip forward→inverse→forward, and every one lands on
itself. A psychometric instrument has to meet the same standard before its scores
mean anything.

The last line shows the inverse in action: `explain_emotion("grief")` reads a
feeling *back* to the construal behind it — "no one caused it, it is settled,
nothing can be done" — plus the action tendency (Frijda's term for what an
emotion moves you to do). This is how an observer reasons from behavior to inner
state, which is the reader's whole task in a novel.

**The novelistic insight.** Emotion is interpretation. To make a character feel
resentment rather than anger, you do not write "she felt resentment"; you arrange
for her to be *wronged without recourse*, and the feeling follows. The model
makes the causal structure of emotion explicit, so you can compose feelings from
situations.

---

### 3.2 Preregistration — the method behind every prediction

**The idea.** Before we run a single simulation, we need the method that makes a
prediction honest. Looking at a finished run and saying "of course she was always
going to break" costs nothing and proves nothing. Real prediction means writing
your claims down *before* you see the outcome and then checking them. The library
enforces this: you open a preregistration, stake specific forecasts, and check
them against the run — and once you check, the registration is sealed, so you
cannot slip in a claim after the fact. This is the scientific practice of
preregistration, built into the tool, and it is where the ✓ CONFIRMED and
✗ FALSIFIED verdicts you will see throughout the rest of this tutorial come from.

```python
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
```

**Output:**

```
PREREGISTERED FORECASTS — staked before the run, checked after
  ✓ CONFIRMED: Nadia feels dread by 4s
      first at 2.0s (5 in all)
  ✓ CONFIRMED: Nadia narrates over a gap (>= 0.4)
      gap 0.55 at 2.0s
  ✓ CONFIRMED: Nadia's heart peaks >= 110
      peak 118.0
  ✗ FALSIFIED: Nadia feels joy
      no such feeling in the Chronicle
  3 confirmed, 1 falsified.
  (Verdicts are claims about this model of the character, never about a real person.)
```

**What the code does.** Nadia hears something alarming (`ear` at strength 9); a
threat appraisal drives her heart up to 118, which makes her feel dread; and her
narrator is set to downplay that dread with "I'm fine." Four forecasts are staked
against this setup *before* it runs: that she feels dread by 4s, that her
narrator's account splits from her body by a measurable gap, that her heart peaks
above 110, and — deliberately — that she feels joy.

**What the output means.** Three forecasts hold and one fails, exactly as it
should. She feels dread early. Her narrator "narrates over a gap" of 0.55 — it
says "I'm fine" while the heart record shows real distress, and that divergence
between the told story and the bodily truth is measured, not asserted. Her heart
peaks at 118. And the joy forecast is marked **✗ FALSIFIED** rather than quietly
dropped. That the system *can* return a falsification is what makes the three
confirmations worth anything; a method that ratifies every guess predicts
nothing.

The `expect_gap` forecast is worth watching for, because the same felt-but-
disowned structure recurs across the simulations below — most sharply in the
avoidant attachment style and the avoidant child of the Strange Situation. Here
it appears in its simplest form, preregistered and confirmed.

**The novelistic insight.** Preregistration is the discipline that keeps
character work honest. A model that "explains" any outcome after the fact
explains nothing; the value is in deciding what a person *would* do before the
scene is written, then finding out whether your instrument agrees. Every
✓ and ✗ in the rest of this tutorial is a claim staked in advance and checked
against what the body actually did.

---

### 3.3 Attachment — forecasting how someone meets a separation

**The idea.** Attachment theory (Bowlby, Ainsworth, Main) says that early
experience installs a *style* — secure, anxious, avoidant, or disorganized —
that governs how a person responds to the threat of losing a bond. The library
lets you install a style and then **forecasts** how the character will meet a
separation the author never wrote: whether they protest, whether their body
spikes, whether they settle on reunion, whether they show approach and avoidance
at once. Each forecast is preregistered from the style table — staked before the
run, in the sense we just built — and then checked.

```python
# Install an attachment style; the library stakes a style-specific forecast
# BEFORE the run, then checks it. Here are the two most telling styles in full.
from soma.narrative import Story, anxious, stoic

for style, temp in [("avoidant", stoic), ("anxious", anxious)]:
    s = Story(f"sep_{style}", span="12s", step="1s", about="separation distress")
    c = s.character("Mara", temperament=temp)
    c.attaches(style, to="Jonah")
    print(s.predict_separation("Mara").render())
    print()
```

**Output:**

```
Separation probe — Mara (avoidant); forecast staked by the style table before the run:
  ✓ CONFIRMED: a visible protest fires on separation — forecast False, observed False
  ✓ CONFIRMED: the narrator reports calm over a real somatic spike (confabulation gap) — forecast True, observed True
  ✓ CONFIRMED: separation genuinely raises the body's arousal — forecast True, observed True
  ✓ CONFIRMED: approach and avoidance both fire on the figure — forecast False, observed False
  (narrated calm over a real somatic spike -- repressive coping, measurable as a confabulation gap riding on an elevated heart record)

Separation probe — Mara (anxious); forecast staked by the style table before the run:
  ✓ CONFIRMED: a visible protest fires on separation — forecast True, observed True
  ✓ CONFIRMED: the narrator reports calm over a real somatic spike (confabulation gap) — forecast False, observed False
  ✓ CONFIRMED: separation genuinely raises the body's arousal — forecast True, observed True
  ✓ CONFIRMED: arousal settles substantially after reunion — forecast False, observed False
  ✓ CONFIRMED: approach and avoidance both fire on the figure — forecast False, observed False
  (loud protest, and arousal that outlasts the reunion -- the alarm's gain is kept up)
```

**What the output means.** Each report stakes four or five style-specific claims
and then checks them against a separation the author never scripted. Read the two
side by side and the styles come apart cleanly:

- The **avoidant** Mara shows *no visible protest* and *no* approach-avoidance
  conflict — but her body's arousal rises anyway, and her narrator reports calm
  over that spike. The forecast predicted exactly this pattern: outward
  composure, inward alarm, a confabulation gap between the two. That is the
  avoidant signature — a racing heart under a calm face.
- The **anxious** Mara shows the opposite: a *loud protest*, real arousal, and —
  the diagnostic line — arousal that does *not* settle after the reunion. The
  alarm stays on. Where the avoidant child disowns the distress, the anxious
  child cannot put it down.

Every claim was staked from the style table before the run and every claim held,
which means the installed styles genuinely produce their textbook signatures
rather than merely being labeled with them. (The two styles not shown, secure
and disorganized, confirm the same way; the secure child protests and then
settles, the disorganized child shows approach and avoidance firing at once.)

**The novelistic insight.** Character is a way of meeting loss. The same
departure lands differently on four people, and the difference is legible in the
body even when the words conceal it. Attachment gives you a principled way to
keep a character's response to separation *consistent* across scenes — the same
style will protest, or downplay, or freeze, every time — which is a large part of
what makes an invented person feel like one person rather than a series of moods.
The avoidant style is the one to keep: its calm is a performance the heart never
joins, and that gap is fiction's most dependable engine.

---

### 3.4 The tipping point and early warning — forecasting a break

**The idea.** A defended belief ("I did not matter") can absorb disconfirming
evidence for a long time and then break all at once. Two questions a novelist
asks: *how much* pressure does it take to break it (the tipping point), and *can
you see the break coming* before it happens (early warning)? The second is the
deeper claim — it comes from dynamical-systems theory: near a tipping point, a
system slows down and its fluctuations grow, so an approaching break leaves a
statistical signature *before* it occurs.

```python
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
```

**Output:**

```
tipping point: {'who': 'Vane', 'channel': 'the_evidence', 'breaks_at': 3.0, 'in_range': (0.0, 9.0)}

EARLY WARNING — Vane, read only before any revelation:
  signal: overwhelm-debt (the destabilizing variable)
  accumulator at 18.9 of bound 20.1, slope +2.10/s
  fluctuation variance trend:   -0.39 (flat/falling)
  fluctuation autocorr. trend:  +0.36 (rising)
  -> FORECAST: break coming (strong signal) — crossing predicted at ≈14s
  ✓ the full run: broke at 14s
```

**What the output means.** The **tipping point** result says that if the evidence
were held at a constant level, the belief would break once that level reached
**3.0** on the 0–9 scale — a precise threshold found by sweeping the input and
watching for the revelation. This is the "how much does it take" answer.

The **early warning** panel is the harder claim, and the more interesting one. It
reads *only the data from before any break has happened*: the accumulating
"overwhelm-debt" (the suppressed disconfirming surprise), its slope, and two
early-warning statistics borrowed from ecology and climate science — whether the
fluctuations' **variance** and **autocorrelation** are rising, the fingerprints
of what dynamical-systems theorists call "critical slowing down." From the
approach alone it forecasts **"break coming … crossing predicted at ≈14s,"** and
the check line confirms the full run did break at 14s. Nothing about the break
itself was used to predict it.

**The novelistic insight.** People come apart on a schedule you can read in
advance if you know where to look. The break feels sudden from outside — one more
ordinary day, and then collapse — but the system was destabilizing measurably the
whole time. This is the structure of every "she seemed fine until she wasn't"
story, made mechanical: the debt accumulates silently, the fluctuations grow, and
the moment of breaking is the last step of a long approach, not a bolt from the
blue.

---

### 3.5 Conditioning — the reward prediction error, and spontaneous recovery

**The idea.** The most quantitatively validated model in behavioral neuroscience
is the reward prediction error (Rescorla–Wagner; the temporal-difference account
of Sutton & Barto; Schultz's finding that dopamine neurons fire exactly this
signal). Learning is driven by the gap between reward received and reward
expected. SOMA's loop already computes a prediction error, so conditioning falls
out of it naturally. The library's signature test is the one a *single* learning
trace cannot pass: **spontaneous recovery** — after a conditioned response is
extinguished and the animal rests, the response comes back on its own, proving
extinction was new learning layered over an intact memory, not erasure.

```python
# The reward prediction error, run as learning. The signature prediction plain
# Rescorla-Wagner cannot make: after extinction and a REST, the response returns.
from soma.narrative import Story, trusting

s = Story("pavlov", span="10s", step="1s", about="conditioning")
rat = s.character("Bell", temperament=trusting)
s.conditions(rat, cs="tone", us="food")
rep = s.predict_conditioning("Bell", acquire=10, extinguish=12, rest=10, reacquire=6)
print(rep.render())
```

**Output:**

```
CONDITIONING — Bell: tone → food (value = acquired + context trace)
    acquisition  ▁▁▅▇██████  [0.0 → 7.5]
    extinction   ██▃▂▁▁▁▁▁▁▁▁  [7.5 → 0.5]
    rest         ▂▃▄▅▆▆▇▇▇█  [1.7 → 6.5]
    reacquisition ▁▁▅▇██  [0.5 → 7.5]
    peak RPE (unpredicted reward): +7.20; once predicted it falls toward 0 — dopamine's signature
    ✓ CONFIRMED: acquisition: value climbs to near the reward — peaked at 7.5
    ✓ CONFIRMED: the RPE shrinks as reward becomes predicted (dopamine's signature) — 3.60 → 0.46
    ✓ CONFIRMED: extinction: the conditioned value falls — 7.5 → 0.5
    ✓ CONFIRMED: SPONTANEOUS RECOVERY: after rest the value returns (extinction was new learning, not erasure) — 0.5 → 6.5 after rest
    ✓ CONFIRMED: savings: relearning starts from the intact trace and is no slower — 5 vs 4 beats; starts 0.5 vs 0.0
```

**What the output means.** Read the four sparklines as a story across the
animal's training:

- **acquisition** `▁▁▅▇██████` — the tone comes to predict food; the learned
  value climbs from 0 to 7.5 and plateaus.
- **extinction** `██▃▂▁▁▁▁▁▁` — food stops; the response falls back to ~0.5.
- **rest** `▂▃▄▅▆▆▇▇▇█` — *nothing happens at all*, and yet the value climbs back
  to 6.5. This is spontaneous recovery, the result the whole example is built
  around.
- **reacquisition** `▁▁▅▇██` — retraining, which starts from a higher floor.

The `peak RPE (unpredicted reward): +7.20 … falls toward 0` line is dopamine's
signature exactly. The prediction error is large when the reward is a surprise
and shrinks to nothing once the reward is fully predicted, because a predicted
reward stops being news. Each `✓ CONFIRMED` is a staked prediction the run bore
out. The recovery one is emphasized because a naive single-value model *predicts
it should not happen*: if extinction simply pushed the value back down, rest
could not bring it back. The library instead models two traces, a slow "acquired"
memory and a fast "context" correction, so the recovery is the slow trace
re-emerging once the fast one decays.

**The novelistic insight.** You do not unlearn a love or a fear; you learn a
second thing on top of it, and the first is still there underneath. The old
response returns after a quiet interval, whether as the ex-smoker's craving on a
stressful day or the old grief that resurfaces at an anniversary. The person has
not regressed; extinction never erased anything. "Getting over it" is a fragile
new layer laid over an intact old one.

---

### 3.6 Learned helplessness — why one defeat generalizes and another doesn't

**The idea.** Seligman and Maier found that exposure to *uncontrollable* bad
events (not just bad events — *uncontrollable* ones) produces a passive,
helpless state that transfers to new situations. Abramson, Seligman & Teasdale's
reformulation added the variable that decides *whether* the helplessness
transfers: the person's **explanatory style**. Someone who explains failure
*globally* ("I ruin everything") carries the deficit into unrelated situations;
someone who explains it *specifically* ("I couldn't do that one thing") does not.
This is the classic **triadic design**, and its sharpest prediction is that
transfer asymmetry.

```python
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
print(f"\ntransfer asymmetry holds: {td['transfer_signature']}")
```

**Output:**

```
style      pretreatment      novel task    outcome
--------------------------------------------------------
global     controllable      dissimilar    copes
global     controllable      similar       copes
global     none              dissimilar    copes
global     none              similar       copes
global     uncontrollable    dissimilar    DEFICIT
global     uncontrollable    similar       DEFICIT
specific   controllable      dissimilar    copes
specific   controllable      similar       copes
specific   none              dissimilar    copes
specific   none              similar       copes
specific   uncontrollable    dissimilar    copes
specific   uncontrollable    similar       DEFICIT

transfer asymmetry holds: True
```

**What the output means.** The table is the full 2×3×2 design: two explanatory
styles × three pretreatments (controllable / uncontrollable / none) × two test
situations (similar / dissimilar to the original). Read the `DEFICIT` rows and
the whole theory is visible:

- A deficit appears **only after uncontrollable pretreatment**. Controllable
  adversity and no adversity both leave the subject coping — it is not hardship
  that breaks you, it is hardship you cannot affect.
- For the **global** style, the uncontrollable deficit shows up in *both* the
  similar and the dissimilar novel task — it generalizes everywhere.
- For the **specific** style, the uncontrollable deficit shows up *only* in the
  similar task — it stays contained.

`transfer asymmetry holds: True` confirms the signature contrast (global
transfers to a dissimilar task; specific does not). In the model this comes from
a single design choice: the *scope* of the learned control-belief. A global
learner keeps one belief about control that follows them everywhere; a specific
learner keeps a separate belief per situation, so a genuinely new situation
starts fresh.

**The novelistic insight.** Two people suffer the same defeat and walk away with
different futures — and the divide is not the event but the sentence each says
about it. "This always happens to me" and "that particular thing went wrong" are
different characters, and the difference determines whether the wound spreads or
stays local. The reformulation is, at bottom, a theory of how self-narration
shapes fate — which is a novelist's native subject.

---

### 3.7 Drift-diffusion decisions — how long a choice takes and how often it's wrong

**The idea.** Every simulation so far predicts what a character *feels* or
*becomes*. This one predicts something different and, in the lab, measured to the
millisecond: *how long a decision takes and how often it errs.* The
drift-diffusion model (Ratcliff; Gold & Shadlen) is the dominant account of
speeded two-choice decisions. It treats a choice as noisy evidence accumulating
toward one of two boundaries, and from four interpretable parameters it predicts
whole reaction-time distributions and error rates at once. (This is where SOMA
gains its one source of randomness — a seeded, reproducible noise isolated from
the otherwise-deterministic core.)

```python
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
```

**Output:**

```
juror style   accuracy   RT correct   RT error   skew
impulsive        68%       0.92s      0.89s   +2.32
deliberate       85%       3.37s      3.22s   +0.70
keen             92%       1.76s      1.77s   +1.62
muddled          63%       2.32s      2.24s   +1.29
prejudiced       86%       1.52s      2.65s   +1.92

SPEED-ACCURACY TRADEOFF — Juror, boundary swept (drift held fixed):
    boundary   accuracy   mean RT
      0.60        67%     1.03s
      1.00        75%     2.25s
      1.50        84%     3.49s
      2.00        91%     4.30s
    ✓ CONFIRMED: wider boundary raises accuracy (more evidence, fewer errors) — ['67%', '75%', '84%', '91%']
    ✓ CONFIRMED: wider boundary lengthens RT (more evidence takes longer) — ['1.03', '2.25', '3.49', '4.30']
```

**What the output means.** Each row is a decision *temperament* built from the
DDM's parameters, and each makes a distinct, checkable claim:

- **impulsive** — fast (0.92s) and error-prone (68%): a narrow boundary, commits
  on little evidence.
- **deliberate** — slow (3.37s) and accurate (85%): a wide boundary, waits for
  more evidence. Same evidence *quality* as impulsive; only the caution differs.
- **keen** — fast *and* accurate (1.76s, 92%): a high drift rate — this juror
  simply sees more per unit time, the one combination caution alone cannot buy.
- **muddled** — slow and inaccurate: a low drift rate, poor evidence.
- **prejudiced** — the tell is in the timing: correct verdicts come fast (1.52s)
  but errors come **slow** (2.65s). That asymmetry is the fingerprint of a
  *starting bias* — a juror leaning toward one verdict before the evidence, so
  reaching the wrong one means climbing upstream the whole way. A symmetric model
  cannot produce it.

Every `skew` is positive: reaction-time distributions have a long right tail,
the DDM's universal signature.

The second panel traces the **speed-accuracy tradeoff** by moving *one* dial —
the decision boundary — while holding evidence quality fixed. Accuracy climbs
(67%→91%) and time lengthens (1.03s→4.30s) together, monotonically. This
dissociates two things ordinary language conflates: being *careful* (a wide
boundary) is not the same as being *smart* (a high drift). The same juror,
instructed to hurry or to be sure, walks this curve.

**The novelistic insight.** A decision has a shape in time, and the shape gives
the decider away. The juror who leans "guilty" before the evidence gives herself
away not in *what* she concludes but in *how long* her acquittals take against her
convictions. Character shows up in tempo. The speed-accuracy curve, meanwhile, is
the mechanical form of a familiar tension — the deadline that trades correctness
for speed — with one subtlety worth keeping: hurrying does not lower accuracy
evenly. It discards the hard cases, which are the ones that most needed the time.

---

### 3.8 The Strange Situation — blind classification from behavior

**The idea.** Ainsworth's Strange Situation is the most consequential
standardized experiment in developmental psychology: a one-year-old goes through
eight scripted episodes — play, a stranger's entrance, two separations from the
caregiver, two reunions — and a trained coder reads the child's *attachment
classification* not from anything the child says but from four behaviors in the
two reunion episodes (proximity-seeking, contact-maintaining, avoidance,
resistance). The library runs the whole protocol and codes it the way a coder
codes a tape — **from the behavior stream alone, never seeing which style was
installed.** That blindness makes the model's central claim testable as
*parameter recovery*: install a style, run the protocol, classify blind, and the
classification must recover the installed style for all four.

```python
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
print(f"\ninstrument valid: {r['recovered']}")
```

**Output:**

```
STRANGE SITUATION — Noa, coded from the behavior stream alone:
    first_reunion    seek 1.7  maintain 1.7  avoid 6.3  resist 1.0
    second_reunion   seek 1.7  maintain 1.7  avoid 6.3  resist 1.0
    disorganization index: absent | physiological arousal over displayed calm: PRESENT | settles by the end: yes
    -> CLASSIFICATION: AVOIDANT

  installed secure        -> classified secure
  installed anxious       -> classified anxious
  installed avoidant      -> classified avoidant
  installed disorganized  -> classified disorganized

instrument valid: True
```

**What the output means.** The top block is one coded tape. The four numbers per
reunion are Ainsworth's scales, scored 1–7 from the behavior the run produced.
For this avoidant child: **low seeking (1.7), low maintaining (1.7), high
avoidance (6.3), low resistance (1.0)** — the child does not approach the mother
on reunion. The diagnostic line reports the avoidant signature precisely:
**"physiological arousal over displayed calm: PRESENT"** — the body spiked during
the separations even though the reunion behavior is cool and distant. The coder,
reading only this, writes **AVOIDANT** — and that is indeed the style that was
installed.

The bottom block is the validity test: all four installed styles are recovered
from behavior alone. `instrument valid: True` is the strong claim — the model's
types are not just labels stapled on; they are *recoverable from the behavior the
model generates*, which is what it means for a classification instrument to be
valid.

The avoidant child is the one to dwell on. Its outward behavior reads as
independence — "I don't need you." But the physiological record shows the
separation was as distressing for this child as for any other; the difference is
that the avoidant child has learned to *not show it*, and even the narrator's
account reports calm. The distress is real and disowned at once.

**The novelistic insight.** You can read a person's deepest relational pattern
from a few minutes of how they behave at a reunion — and the reading can be
blind, needing no access to their inner report, because the pattern is *in the
behavior*. The avoidant child teaches the sharpest lesson: apparent independence
can be a performance laid over an unmet need, and the body keeps the true account
even when the face and the words do not. That gap — composure over a racing
heart — is one of the most reliable engines of characterization there is.

---

### 3.9 The Gottman marriage model — thin-slice divorce prediction

**The idea.** Gottman and Murray's *Mathematics of Marriage* is the most famous
predictive character simulation of all: from parameters fitted to a few minutes
of one conversation, they predicted which newlyweds would divorce with ~94%
accuracy. The model turns on a handful of measurable quantities — the ratio of
positive to negative interaction, negative-affect reciprocity (does one partner's
hostility trigger the other's?), and whether repair attempts land — and it sorts
couples into stable types (validating, volatile, conflict-avoiding) and unstable
ones (hostile, hostile-detached). The library rebuilds this and reproduces its
most famous move: the **thin-slice forecast**, calling the outcome from the first
quarter of one conversation.

```python
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
```

**Output:**

```
OK       validating: ratio  14.00:1  reciprocity   0%  thin-slice: holds
OK         volatile: ratio  14.00:1  reciprocity   0%  thin-slice: holds
OK          avoider: ratio   0.00:1  reciprocity   0%  thin-slice: holds
OK          hostile: ratio   0.00:1  reciprocity  96%  thin-slice: falls
OK hostile_detached: ratio   0.00:1  reciprocity  96%  thin-slice: falls
```

**What the output means.** Each row is a couple type put through one contentious
conversation (a grievance is raised; what happens next is the marriage). Three
numbers tell the story:

- **ratio** — positive to negative interactions. The stable types (validating,
  volatile) run at 14:1; the unstable types (hostile, hostile-detached) at 0:1.
  Gottman's famous "magic ratio" is 5:1, and the split falls cleanly on either
  side of it. (The avoider sits at 0:1 too but is *stable* — see below.)
- **reciprocity** — negative-affect reciprocity, the probability that one
  partner's hostility is answered by the other's. This is the cascade signature:
  **96%** in the unstable couples (hostility feeds hostility, an absorbing
  state), **0%** in the regulated ones. This single number separates the doomed
  couples from the safe ones more cleanly than the ratio does.
- **thin-slice** — the forecast made from the *first quarter of the
  conversation alone*. It calls "holds" for every stable type and "falls" for
  every unstable one, matching the full run's outcome in all five cases.

Note the **avoider**: a 0:1 ratio but a stable marriage and a "holds" forecast.
This is Gottman's conflict-avoiding couple — they do not generate much
positive affect, but they do not cascade either, because their low mutual
influence keeps the negativity from feeding on itself. The model captures
"stability by disengagement," a genuinely different route to a lasting marriage
than warmth.

**The novelistic insight.** A marriage's fate is legible early, in the *pattern*
of how a couple handles one disagreement — not in the content of what they fight
about but in whether the fight cascades. The thin-slice result is why a perceptive
observer can sit with a couple for ten minutes and know: it is not that they
argue, it is *how the argument travels* — whether a hard word is absorbed or
answered in kind. The 96%-vs-0% reciprocity split is the mechanical heart of
that intuition, and it gives a writer a precise lever: to doom a couple, make
each cutting remark reliably summon another; to save them, let one of them, even
once, decline to answer in kind.

---

## Part 4 — Insights *about* the predictions

The simulations in Part 3 make predictions; each was staked in advance and
checked, in the manner Section 3.2 established. The two tools in this part are
different in kind. They are *post-hoc analyses* — they take a run that has
already happened and interrogate it, asking which parameter actually drove the
outcome and what smallest change would have flipped it. These are the tools that
turn a prediction into an *explanation*.

### 4.1 Sensitivity — which dial writes the ending

**The idea.** A character has many parameters. Which ones actually determine the
outcome, and which are decorative? Variance-based (Sobol) sensitivity analysis
answers this rigorously: it apportions the variance in an outcome across the
parameters, separating each dial's effect *on its own* (main effect) from its
effect *through interaction* with others (total effect).

```python
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
```

**Output:**

```
SENSITIVITY of 'break_time' (Ink) — variance-based, 120 runs
  dial                                  main   total   reading
  the_lie_only_needed.conviction        1.00   1.00   acts on its own
  the_lie_only_needed.learn             0.12   1.00   acts through interaction
  the_lie_only_needed.precision         1.00   1.00   acts on its own
  (main = variance removed if this dial were fixed; total = variance attributable to it including interactions)
```

**What the output means.** The analysis ran the character 120 times, sampling the
three dials across their ranges, and measured how `break_time` (when the belief
breaks) responds. Two columns: **main** is how much of the outcome's variance a
dial controls by itself; **total** includes its interactions with the others.

- **conviction** and **precision** both read *"acts on its own"* (main ≈ total ≈
  1.0): each single-handedly determines when the belief breaks. That makes sense
  — how much you trust the belief versus the evidence is exactly the tug-of-war
  that sets the breaking time.
- **learn** reads *"acts through interaction"* (main 0.12, total 1.00): the
  hardening rate barely matters on its own, but it matters a great deal *in
  combination* with the others. It shapes the outcome only through how it
  compounds conviction over time.

(Sobol indices are variance fractions and are bounded in [0, 1]; the library
clamps them so a dial can never be reported as controlling more than 100% of the
variance.)

**The novelistic insight.** Not every trait a character has is load-bearing. This
tells you *which* ones the ending actually hangs on — and warns you when a trait
matters only in concert with another, never alone. "The hardening didn't doom him
by itself; it doomed him because he was already too sure" is an interaction
effect, and the analysis names it as one.

### 4.2 Counterfactual — the smallest change that would have saved him

**The idea.** Fiction is full of margins: the marriage that would have held, the
confession that would have landed a day earlier. The counterfactual tool finds
the *smallest single change* to any one dial that flips the outcome — the precise
margin the story turned on.

```python
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
```

**Output:**

```
MINIMAL INTERVENTION — least single change to make 'break' reach 0 for Ink:
  THE MARGIN: this ending turns on one dial —
  the_lie_only_needed.conviction: 0.85 → 2.55 (Δ 1.7, 79% of range) flips 1 → 0
  other single-dial routes, by increasing size:
  the_lie_only_needed.precision: 0.35 → 0.05 (Δ 0.3, 100% of range) flips 1 → 0
  ('smallest' is normalized to each dial's own range, so dials on different scales compare fairly)
```

**What the output means.** In the base run, Ink's belief breaks. The tool asks:
what is the *least* single-dial change that would prevent it? The answer: raise
conviction from 0.85 to 2.55 — make Ink *more* certain of the belief, so the
evidence can never overturn it. It also reports the alternative route (drop
precision to 0.05 — make Ink trust the evidence even less), noting it requires
moving that dial across its entire range, so it is the "larger" intervention when
each is normalized to its own scale.

The result is itself an insight: the belief breaks because Ink is *not quite
certain enough* to defend it against the evidence. A little more conviction and
the defense holds — the character would have survived intact, and unhealed.

**The novelistic insight.** Every ending has a margin, and naming it precisely is
often where the meaning lands. "She would have kept the belief if she had been
just a little more sure of it" reframes a breakdown as a near-miss and locates
the exact fulcrum the drama balanced on. It doubles as a compositional test: to
make an ending feel *inevitable*, confirm that no small single change flips it
(the "over-determined" case the sensitivity tool detects); to make it feel like a
near-thing, engineer it to turn on one narrow margin.

---

## Part 5 — Capstone studies: the tools, composed

Parts 3 and 4 taught each prediction and each insight tool on its own,
with small, focused stories built to show one mechanism clearly. Real
studies rarely stop at one tool. The eight examples below are complete,
unedited command-line programs from SOMA's example library — each composes
several of the tools you've now learned into a single worked study of one
character, one marriage, or one small group, the way an actual analysis
would. They run in the **Library** rail under **capstone · ...**, exactly
as written here; nothing has been trimmed.

---

### 5.1 Four ways of leaving — the tools composed, end to end

**The idea.** One person leaves a room. This capstone predicts, before any run, four
different people it could happen to, an emotion a fifth person never
named, and what happens between two cold negotiators who correspond
perfectly and can't stand each other. The Part 3 sections taught
attachment, appraisal, and circumplex one at a time, each on its own small
story; this file stakes preregistered forecasts across all three at
once — every claim is staked before the run and checked after, exactly as
Section 3.2 taught, at full scale.

```python
"""
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
"""
from soma.narrative import (Story, anxious, stoic, trusting, guarded, volatile,
                            predict_feeling, predict_pull, Stance)


def separations():
    """Four attachment styles; one separation probe; four staked forecasts."""
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
    """The author supplies the appraisal; the library derives the emotion --
    and then must produce it."""
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
    """Two cold, dominant people: perfect correspondence on warmth, collision
    on dominance -- structurally complementary, affectively corrosive."""
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
```

**Output:**

```
========================================================================
I. FOUR WAYS OF BEING LEFT (soma.narrative.attachment)
========================================================================

Separation probe — Mara (secure); forecast staked by the style table before the run:
  ✓ CONFIRMED: a visible protest fires on separation — forecast False, observed False
  ✓ CONFIRMED: the narrator reports calm over a real somatic spike (confabulation gap) — forecast False, observed False
  ✓ CONFIRMED: separation genuinely raises the body's arousal — forecast True, observed True
  ✓ CONFIRMED: arousal settles substantially after reunion — forecast True, observed True
  ✓ CONFIRMED: approach and avoidance both fire on the figure — forecast False, observed False
  (distress rises, and the body settles on reunion -- the figure works as a regulator)

Separation probe — Mara (anxious); forecast staked by the style table before the run:
  ✓ CONFIRMED: a visible protest fires on separation — forecast True, observed True
  ✓ CONFIRMED: the narrator reports calm over a real somatic spike (confabulation gap) — forecast False, observed False
  ✓ CONFIRMED: separation genuinely raises the body's arousal — forecast True, observed True
  ✓ CONFIRMED: arousal settles substantially after reunion — forecast False, observed False
  ✓ CONFIRMED: approach and avoidance both fire on the figure — forecast False, observed False
  (loud protest, and arousal that outlasts the reunion -- the alarm's gain is kept up)

Separation probe — Mara (avoidant); forecast staked by the style table before the run:
  ✓ CONFIRMED: a visible protest fires on separation — forecast False, observed False
  ✓ CONFIRMED: the narrator reports calm over a real somatic spike (confabulation gap) — forecast True, observed True
  ✓ CONFIRMED: separation genuinely raises the body's arousal — forecast True, observed True
  ✓ CONFIRMED: approach and avoidance both fire on the figure — forecast False, observed False
  (narrated calm over a real somatic spike -- repressive coping, measurable as a confabulation gap riding on an elevated heart record)

Separation probe — Mara (disorganized); forecast staked by the style table before the run:
  ✓ CONFIRMED: a visible protest fires on separation — forecast True, observed True
  ✓ CONFIRMED: the narrator reports calm over a real somatic spike (confabulation gap) — forecast False, observed False
  ✓ CONFIRMED: separation genuinely raises the body's arousal — forecast True, observed True
  ✓ CONFIRMED: arousal settles substantially after reunion — forecast False, observed False
  ✓ CONFIRMED: approach and avoidance both fire on the figure — forecast True, observed True
  (approach and avoidance on the same figure -- fright without solution, ambivalence as mechanism)

========================================================================
II. THE VERDICT SHE NEVER NAMED (soma.narrative.appraisal)
========================================================================

  appraisal: harmful, other-caused, certain, powerless
  predicted feeling: resentment (tendency: withhold -- oppose without power, at a distance, in time, intensity 0.90) -- other-blame without power: the anger pattern minus control (Scherer: low power turns antagonism inward or into time)

PREREGISTERED FORECASTS — staked before the run, checked after
  ✓ CONFIRMED: Vera feels resentment by 4s
      first at 2.0s (3 in all)
  ✓ CONFIRMED: Vera's heart peaks >= 105
      peak 112.0
  2 confirmed, 0 falsified.
  (Verdicts are claims about this model of the character, never about a real person.)

  construct validity — forward and inverse mappings consistent for all
  14 emotions: True (14/14 round-trip). The map is identifiable,
  so the forecast is a prediction, not a label. And it runs backward —
  from the feeling observed to the reading of the world behind it:
    resentment: they construed that bad for what they wanted, someone else caused it, it is settled, nothing can be done — and so are moved to withhold -- oppose without power, at a distance, in time
    grief: they construed that bad for what they wanted, no one caused it, it is settled, nothing can be done — and so are moved to withdraw and search -- deactivate, and reach for what is gone
    relief: they construed that good for what they wanted, no one caused it, it is settled, the bad outcome had been braced for — and so are moved to recover -- release the braced body, stand down

========================================================================
III. THE NEGOTIATION (soma.narrative.circumplex)
========================================================================

  Rook's opening arrogant-calculating move invites aloof-introverted (warmth -> -0.60: correspondence, robust across studies; dominance -> -0.60: reciprocity, weaker and context-moderated (strongest in conflict; weaker between familiars))

Dyad forecast — Rook & Wren: complementarity 0.77 (warmth 0.95, dominance 0.45) -> the interaction should STRAINS.
  ✓ CONFIRMED: the interaction strains — forecast strains, observed rapport deltas -4.0/-4.0
  ✓ CONFIRMED: hostile correspondence sustains itself (friction persists; rapport ends negative) — forecast persists & negative, observed 30 frictions, last at 14s; deltas -4.0/-4.0
  ✓ CONFIRMED: who gives ground: the looser-held self (Wren) drifts further from their opening manner — forecast Wren, observed Wren (drift Rook 0.1 vs Wren 0.8)
  (warmth correspondence is the robust axis; dominance reciprocity is staked at lower confidence (context-moderated in the literature))
```

**What the output means.** The output has three parts, one per tool.

**Part I** runs the same separation probe from Section 3.3 across all four
attachment styles at once, not just the two shown there. Read the four
one-line summaries at the end of each block: secure settles on reunion (the
figure works as a *regulator*); anxious protests loudly and *stays* aroused
past the reunion; avoidant shows the calm-over-a-spike split from Section
3.3; and disorganized is the one style Section 3.3 didn't examine in
detail — it is the only one where *both* approach and avoidance fire on the
same figure at once, "fright without solution." Nineteen of the twenty
possible staked claims confirm — secure, anxious, and disorganized each
stake five, but avoidant stakes only four, because the model deliberately
declines to forecast whether an avoidant child's arousal settles after
reunion: suppression, not settling, is what defines the style, so there is
no claim to check there.

**Part II** exercises appraisal's inverse map (Section 3.1) on a fifth
person, Vera, who was given only a bare appraisal (harmful, other-caused,
certain, powerless) and never told what to feel. The prediction is
*resentment*, and the preregistered forecast — that she'll feel it by 4
seconds, with a heart rate above 105 — confirms. The construct-validity
check then runs the whole 14-emotion round-trip again, this time printing
three emotions' full inverse readings side by side (resentment, grief,
relief), so you can see how differently the same "bad, certain, nothing to
be done" core reads once agency and coping shift.

**Part III** is circumplex prediction (interpersonal theory, not covered as
its own section in Part 3): two characters are given only a numeric
*stance* — dominance and warmth — and the library forecasts what happens
when they meet, before any interaction is written. Rook and Wren are both
cold (negative warmth), which the model calls *correspondence* — coldness
answers coldness — and both dominant, which is *reciprocity's* harder case
(two people both trying to lead). The forecast — that this pairing STRAINS,
that the hostility is self-sustaining, and even *which* of the two will
give ground first (Wren, the one holding their manner more loosely) — all
confirm.

**The novelistic insight.** Three unrelated theories, run from one file, agreeing with themselves
across twenty-four preregistered claims. That reliability is the case for
treating psychological typologies as a *library* rather than a one-off
trick: attachment, appraisal, and circumplex are independent instruments,
built independently, and they compose without friction because each
predicts from a small, principled parameter set rather than from a
memorized outcome. A novelist assembling a scene with four characters,
each carrying a different attachment style, meeting a fifth who feels
something nobody named, negotiated by two more who read each other's
stance at a glance — can stake all of it in advance.

---

### 5.2 The anatomy of a breaking — every instrument on one man

**The idea.** Halvor kept a harbor ledger for thirty-one years and believes the only
reason anyone is kept is that they are needed. His granddaughter visits
anyway, for no errand — persistent, useless regard, the evidence his belief
cannot metabolize. The story is deliberately small; the
point is the study. This is the single richest file in the library: five
different instruments, each answering a different question about the same
predictive characterization of one man, each checked against real runs.
It is the fullest demonstration of what Part 4's insight tools are for.

```python
"""
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
"""
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
```

**Output:**

```
==========================================================================
I. THE RUN — what actually happens
==========================================================================

  Halvor's lie BREAKS at 10s under sixteen beats of useless regard.

==========================================================================
II. SENSITIVITY — which dial writes this ending
==========================================================================

SENSITIVITY of 'break_time' (Halvor) — variance-based, 160 runs
  dial                                  main   total   reading
  …e_lie_kept_means_needed.precision    0.04   0.76   acts through interaction
  the_lie_kept_means_needed.learn       0.00   0.72   acts through interaction
  …_lie_kept_means_needed.conviction    0.17   0.71   acts through interaction
  (main = variance removed if this dial were fixed; total = variance attributable to it including interactions)

  (The heavy interaction is not noise; it is a recovered mechanism. SOMA's
  auto-break threshold is 6*conviction/precision — a ratio, so neither dial
  acts alone by construction. The study, given only runs, found the ratio.)

==========================================================================
III. DISCRIMINATION — the scene that separates two readings
==========================================================================

  Reading A: armor — held hard (conviction .97) and deaf to the
  evidence (precision .2): he can only suppress, until overwhelmed.
  Reading B: habit — held loosely (conviction .6), evidence trusted
  (precision .8): the senses outrank the prior, so he simply updates.

DISCRIMINATION — the scene that separates two readings of Halvor (outcome: break_time):
  probe                          reading A   reading B   apart
  her_visits=4                      15.0       never    1.00
  her_visits=6                      13.0       never    1.00
  her_visits=9                       7.0       never    1.00
  her_visits=2                     never       never    0.00
  -> WRITE THIS SCENE: her_visits=4 — the two natures come apart most here.
  (divergence 1.00 = the two readings differ qualitatively (one breaks, one never does) — the sharpest possible separation)

  ('never' here does not mean armored: reading B never BREAKS because
  it never suppresses — the evidence wins arbitration and he changes
  his mind without a shattering. The same scene separates a man who
  breaks from a man who quietly revises.)

==========================================================================
IV. EARLY WARNING — is the break legible before it happens?
==========================================================================

EARLY WARNING — Halvor, read only before any revelation:
  signal: overwhelm-debt (the destabilizing variable)
  accumulator at 17.8 of bound 24.9, slope +4.45/s
  fluctuation variance trend:   +0.80 (rising)
  fluctuation autocorr. trend:  -0.64 (flat/falling)
  -> FORECAST: break coming (strong signal) — crossing predicted at ≈11s
  ✓ the full run: broke at 10s

  ...and the same instrument on the life where her regard stays faint
  (reads at what the lie predicts; nothing accumulates):

EARLY WARNING — Halvor, read only before any revelation:
  signal: overwhelm-debt (the destabilizing variable)
  accumulator at 11.0 of bound 16.1, slope +1.10/s
  fluctuation variance trend:   +0.88 (rising)
  fluctuation autocorr. trend:  -0.32 (flat/falling)
  -> FORECAST: stable (strong signal) — at this rate the bound is not reached until ≈25s, past the horizon
  ✓ the full run: never broke

==========================================================================
V. MINIMAL INTERVENTION — what would have prevented it
==========================================================================

MINIMAL INTERVENTION — least single change to make 'break' reach 0 for Halvor:
  THE MARGIN: this ending turns on one dial —
  the_lie_kept_means_needed.conviction: 0.88 → 2.56 (Δ 1.68, 79% of range) flips 1 → 0
  other single-dial routes, by increasing size:
  the_lie_kept_means_needed.precision: 0.35 → 0.05 (Δ 0.3, 100% of range) flips 1 → 0
  ('smallest' is normalized to each dial's own range, so dials on different scales compare fairly)

==========================================================================
VI. PREREGISTRATION — the study's conclusions, staked and checked
==========================================================================

PREREGISTERED FORECASTS — staked before the run, checked after
  ✓ CONFIRMED: Halvor's lie breaks (self-revelation)
      revelation at 10.0s in the_lie_kept_means_needed
  ✓ CONFIRMED: Halvor feels grief
      first at 8.0s (13 in all)
  ✓ CONFIRMED: Halvor narrates over a gap (>= 0.4)
      gap 0.55 at 8.0s
  3 confirmed, 0 falsified.
  (Verdicts are claims about this model of the character, never about a real person.)
```

**What the output means.** **I. The run.** Halvor's lie breaks at 10 seconds under sixteen beats of
his granddaughter's regard — the baseline fact everything else explains.

**II. Sensitivity** (Section 4.1) finds something Section 4.1's own example
didn't show: every dial here reads *"acts through interaction"* — none
writes the outcome on its own. The report explains why in its own words:
SOMA's auto-break threshold is a *ratio*, conviction over precision, so by
construction neither dial alone can be decisive. The study recovered that
mathematical fact from runs alone, without being told the formula.

**III. Discrimination** is a tool this tutorial hasn't introduced yet: given
two competing *readings* of a character (here, "armor" — held hard and deaf
to evidence — versus "habit" — held loosely, evidence trusted), it finds the
probe that would separate them most sharply. Three candidate scenes —
`her_visits` at 4, 6, and 9 — all reach the maximum possible divergence
(1.00): at any of them, "armor" breaks and "habit" never does. The report
names the first of the three, `her_visits=4`, as the scene to write, and
that tie is itself the finding: once his granddaughter's regard passes a
fairly low bar, the two readings are already fully separated, so the
smallest, least dramatic version of the scene tells you just as much as a
more extreme one would. Discrimination doesn't say which reading is true;
it says which scene — and here, how modest a scene — would *tell* you.

**IV. Early warning** (Section 3.4) is run twice: once on the life that
breaks, forecasting the crossing at ≈11s against an actual break at 10s;
once on a counterfactual life where the granddaughter's regard stays faint
and nothing ever accumulates enough to cross. Same instrument, both
directions, both correct.

**V. Minimal intervention** (Section 4.2) finds the margin: raising
conviction from 0.88 to 2.56 would have kept the lie intact.

**VI. Preregistration** (Section 3.2) closes the study by staking its own
three headline conclusions — that the lie breaks, that Halvor feels grief,
that his narrator downplays it — before checking them. All three confirm.

**The novelistic insight.** No single tool tells you what a character *is*; each answers a different
question a reader might ask, and a full study is the composition of all
of them. Sensitivity says the ending is over-determined by a ratio, not any
one trait. Discrimination says where to set a scene if you want to reveal
which of two readings is correct. Early warning says the break was legible
in advance, on this life and not on the counterfactual one. The
counterfactual names the exact margin. And preregistration keeps every one
of those claims honest. Put together, this is what "understanding a
character" can mean when the understanding is checkable rather than
asserted: not a single fact, but a small system of mutually consistent
answers to different questions, all about the same acted-out life.

---

### 5.3 The marriage that could have held — a point of no return, computed

**The idea.** Soren's delight in his wife Mira depends on her surprising him — a
low-conviction prior being sweetly wrong, the same *delight-in-error*
pattern from Part 1's very first example. His `learn` rate is the tragedy
dial: every firing hardens the prior, and the curdling isn't that the
feeling stops — it's that the *route* flips. Early in the marriage, a
surprise routes to `perceive`: she moves him, his picture of her revises.
Late, the same surprise routes to `act`: he defends the picture instead,
and whatever still fires is a feeling about his own model, not about her.
Nothing visible changes. That is the point of the study.

```python
"""
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
"""
from soma.narrative import Story, tender, arc, run_with, outcome


LOOP = "appraising_her_face"
YEAR = 31557600.0            # one soma year, in the seconds the Chronicle keeps


def build(extraordinary_day=None, learn=0.08):
    """The marriage. If `extraordinary_day` is (year, value), one unscripted,
    astonishing day is inserted -- the intervention Study IV searches over."""
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
```

**Output:**

```
==========================================================================
I. THE RUN — the year he stops taking her in
==========================================================================

  her face goes on varying for 24 years. He takes it in (`perceive`) for the
  early marriage; the route first flips to resisting (`act`) at year 7,
  and the last beat that truly reaches him is year 6. Over the whole
  marriage the world gets in on only 23% of beats. The delight still
  flickers afterward — but it is delight at his own model, defended.

==========================================================================
II. SENSITIVITY — is the tragedy the learning, or the trusting?
==========================================================================

SENSITIVITY of 'perceive_frac' (Soren) — variance-based, 120 runs
  dial                                  main   total   reading
  appraising_her_face.learn             0.00   0.53   acts through interaction
  appraising_her_face.conviction        0.12   0.12   acts on its own
  appraising_her_face.precision         0.07   0.07   acts on its own
  (main = variance removed if this dial were fixed; total = variance attributable to it including interactions)

  (The outcome is the fraction of his life the world still gets in.)

==========================================================================
III. COUNTERFACTUAL — the smallest change that keeps him open
==========================================================================

  target: the world gets in on at least half his beats (baseline: 23%).

MINIMAL INTERVENTION — least single change to make 'perceive_frac' reach 0.5 for Soren:
  THE MARGIN: this ending turns on one dial —
  appraising_her_face.learn: 0.08 → 0.035 (Δ 0.045, 56% of range) flips 0.226 → 0.516
  ('smallest' is normalized to each dial's own range, so dials on different scales compare fairly)

==========================================================================
IV. THE LAST GOOD YEAR — a point of no return, computed
==========================================================================

  One extraordinary day — her face at 9.5, utterly unforeseen —
  inserted at year Y. Does it still REACH him (route: perceive),
  or does he resist it (route: act)?

    year  2: it reaches him — she moves him
    year  4: it reaches him — she moves him
    year  6: it reaches him — she moves him
    year  8: he resists it — the picture holds
    year 10: he resists it — the picture holds
    year 12: he resists it — the picture holds
    year 14: he resists it — the picture holds
    year 16: he resists it — the picture holds
    year 18: he resists it — the picture holds
    year 20: he resists it — the picture holds
    year 22: he resists it — the picture holds
    year 24: he resists it — the picture holds

  POINT OF NO RETURN: after year 6, no single day, however astonishing,
  routes to perceive — his hardened prior outranks anything one day can say.
  The marriage's fate is settled years before anything visible happens,
  and the year it was settled is computable.
```

**What the output means.** **I. The run** reports the headline fact plainly: the route first flips
at year 7, the last year anything truly reaches him is year 6, and across
the whole marriage the world gets in on only 23% of beats.

**II. Sensitivity** asks the harder question a reader would actually have:
is the tragedy that he *learns too fast*, or that he *trusts himself too
much*? The answer is specific — `learn` is the dial that matters, and it
acts almost entirely *through interaction* (main effect near zero, total
effect 0.53) rather than on its own. It is not simply that he hardens; it
is that hardening compounds with how much he already trusts his own
picture.

**III. The counterfactual** finds the specific fix: dropping his `learn` rate
from 0.08 to 0.035 — less than half — would keep the world reaching him on
at least half of all beats instead of less than a quarter.

**IV. The last good year** is composed directly from the raw insight
substrate (`run_with` and the Chronicle) rather than a canned instrument —
the tutorial's one demonstration that the substrate underneath every report
you've seen is itself an ordinary, usable API. The question: if one
extraordinary day were inserted at year Y, would it still reach him? The
sweep finds a sharp answer — yes through year 6, no from year 8 onward —
and names the number: **year 6 is the point of no return**. No day,
however astonishing, gets through after that, because his hardened prior
by then outranks anything a single day can say.

**The novelistic insight.** A marriage's ending is often described as a moment — the fight, the
discovery, the day someone finally says it out loud. This study makes the
case that the moment is usually the *last* event in a process that finished
long before, and that the year it finished is a computable fact about the
model, not a narrative convenience. "He stopped being reachable in year six"
is a very different, much sadder claim than "he left in year twenty" — and
it is the claim the data actually supports. A novelist who wants a marriage
to feel *tragic* rather than merely *sad* can use exactly this structure:
let the visible ending arrive on schedule, decades after the real one, and
let a reader who checks the record find the actual year underneath it.

---

### 5.4 Five marriages — the Gottman model, run as a typology

**The idea.** Five marriages face the identical contentious conversation in this
file — the same setup Section 3.9 used — but audited far more closely
than one summary line per couple can show. A single number per couple is
a verdict, not an explanation; this capstone asks whether the *forecast
itself* holds up under scrutiny, couple by couple, claim by claim. And for
the one type that fails — the hostile couple — what would it actually
take to save it?

```python
"""
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
"""
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
```

**Output:**

```
==========================================================================
I. FIVE COUPLES, ONE COMPLAINT — the typology's forecasts, checked
==========================================================================

GOTTMAN ASSESSMENT — Ash & Bee (validating): warm, mutually influenced, lets small negativity pass, repairs
  positivity ratio 14.00:1 over the whole run (first quarter: 4.00:1); negative reciprocity 0%
  ✓ CONFIRMED: a validating couple is REGULATED: rapport holds — forecast holds, observed deltas +3.5/+3.9
  ✓ CONFIRMED: their positivity outweighs the negative (ratio >= 1) — forecast >= 1, observed 14.00:1
  ✓ CONFIRMED: THIN SLICE: the first quarter alone forecasts the ending — forecast holds, observed holds

GOTTMAN ASSESSMENT — Ash & Bee (volatile): hot and loud, quick to fire AND quick to repair -- stable because the positive is louder still
  positivity ratio 14.00:1 over the whole run (first quarter: 4.00:1); negative reciprocity 0%
  ✓ CONFIRMED: a volatile couple is REGULATED: rapport holds — forecast holds, observed deltas +3.5/+3.9
  ✓ CONFIRMED: their positivity outweighs the negative (ratio >= 1) — forecast >= 1, observed 14.00:1
  ✓ CONFIRMED: a volatile couple is loud: many affect events — forecast >= 20, observed 45
  ✓ CONFIRMED: THIN SLICE: the first quarter alone forecasts the ending — forecast holds, observed holds

GOTTMAN ASSESSMENT — Ash & Bee (avoider): conflict-avoiding: little influence either way, little said, stable by disengagement
  positivity ratio 0.00:1 over the whole run (first quarter: 0.00:1); negative reciprocity 0%
  ✓ CONFIRMED: a avoider couple is REGULATED: rapport holds — forecast holds, observed deltas -0.4/+0.0
  ✓ CONFIRMED: an avoider couple is quiet: few affect events — forecast <= 8, observed 3
  ✓ CONFIRMED: THIN SLICE: the first quarter alone forecasts the ending — forecast holds, observed holds

GOTTMAN ASSESSMENT — Ash & Bee (hostile): engaged and corrosive: thin-skinned (low negative threshold), no repair that lands -- the cascade
  positivity ratio 0.00:1 over the whole run (first quarter: 0.00:1); negative reciprocity 96%
  ✓ CONFIRMED: a hostile couple CASCADES: rapport falls — forecast falls, observed deltas -5.0/-4.7
  ✓ CONFIRMED: negativity outweighs the positive (ratio < 1) — forecast < 1, observed 0.00:1
  ✓ CONFIRMED: THIN SLICE: the first quarter alone forecasts the ending — forecast falls, observed falls

GOTTMAN ASSESSMENT — Ash & Bee (hostile_detached): one attacks, one stonewalls: hostility met with withdrawal, the coldest configuration
  positivity ratio 0.00:1 over the whole run (first quarter: 0.00:1); negative reciprocity 96%
  ✓ CONFIRMED: a hostile_detached couple CASCADES: rapport falls — forecast falls, observed deltas -5.0/-4.7
  ✓ CONFIRMED: negativity outweighs the positive (ratio < 1) — forecast < 1, observed 0.00:1
  ✓ CONFIRMED: THIN SLICE: the first quarter alone forecasts the ending — forecast falls, observed falls

==========================================================================
II. THE THIN SLICE — the ending, forecast from the first quarter
==========================================================================

  couple             slice says   the marriage      forecast
    validating       holds        holds            ✓ correct
    volatile         holds        holds            ✓ correct
    avoider          holds        holds            ✓ correct
    hostile          falls        falls            ✓ correct
    hostile_detached falls        falls            ✓ correct

  5/5 endings called from the first quarter of one conversation.
  (Gottman's claim was 94% from minutes of tape; here the mechanism
  that makes it possible is visible: the slice carries the couple's
  thresholds, and the thresholds ARE the ending.)

==========================================================================
III. WHAT SAVES A HOSTILE COUPLE — the skin, or the repair?
==========================================================================

MINIMAL INTERVENTION — least single change to make 'mood_drift' reach 0 for Ash:
  THE MARGIN: this ending turns on one dial —
  appraising_their_manner_friction.precision: 0.9 → 0.15 (Δ 0.75, 94% of range) flips -4.67 → 0
  ('smallest' is normalized to each dial's own range, so dials on different scales compare fairly)

  (Lowering the friction loop's precision is 'thickening the skin':
  the same received coldness carries less weight. The instrument
  reports whether any single skin-thickening saves this marriage,
  or whether the cascade is over-determined without repair.)

==========================================================================
IV. THE ANATOMY OF THE CASCADE — reciprocity as the absorbing state
==========================================================================

  couple             negative reciprocity
    validating         0%  
    volatile           0%  
    avoider            0%  
    hostile           96%  ############################
    hostile_detached  96%  ############################

  The unstable couples answer friction with friction nearly every
  beat — Gottman's absorbing state: once in, the cascade feeds
  itself. The regulated couples' reciprocity is near zero not
  because nothing negative arrives, but because it is absorbed —
  by a thicker skin, by repair, or by disengagement.
```

**What the output means.** **I.** Every couple type gets its own preregistered claims, not just a
ratio. The validating and volatile couples are confirmed REGULATED; the
avoider couple is confirmed regulated *and* quiet (few affect events at
all — stability by disengagement, the same reading Section 3.9 gave); the
hostile and hostile-detached couples are confirmed to CASCADE. Every single
staked claim, across all five types, confirms.

**II. The thin slice** restates Section 3.9's headline result as a table:
five endings, called from the first quarter of one conversation, five
correct calls. The commentary makes the mechanism explicit in a way Section
3.9 didn't have room for: the slice carries the couple's *thresholds*, and
the thresholds *are* the ending — there is no hidden variable the thin
slice is missing.

**III.** The counterfactual asks the question a therapist would actually
ask: for the hostile couple, is the fix the *skin* (how much a partner's
own guard filters incoming coldness) or the *repair* (whether a bid to
reconnect lands)? It names the skin: thickening the friction loop's
precision from 0.9 to 0.15 is enough on its own to flip the mood drift from
strongly negative to zero. The skin, not the repair, is the lever this
particular cascade turns on.

**IV.** The reciprocity numbers from Section 3.9 are shown as a bar chart
across all five types: 0% for every regulated couple, 96% for both unstable
ones. The explanation names what the number *means*: the regulated couples
aren't receiving less negativity, they're *absorbing* it — by a thicker
skin, a landing repair, or simple disengagement — while the unstable
couples answer nearly every hostile beat with another one, Gottman's
absorbing state.

**The novelistic insight.** Section 3.9 showed *that* the model sorts five couples correctly. This
one shows *how much more* a single instrument can say once you stop asking
only for the verdict: which claims specifically hold for which type, what
the thin slice's reliability actually rests on, and, most usefully, that
two structurally different repairs (a thicker skin, a landing apology)
are not interchangeable, and the model can tell you which one a given
cascade needs. Saving a marriage, on this evidence, means finding
the one dial a given cascade actually turns on — not applying warmth in
general, but locating the specific lever, per couple, that this method
makes findable.

---

### 5.5 The spiral — panic as a positive feedback loop

**The idea.** Every simulation so far has one attractor: a belief holds or breaks, a
mood settles or doesn't. This capstone introduces a genuinely different
shape. Clark's (1986) cognitive model of panic treats an attack as a
positive feedback loop: a bodily sensation is catastrophically appraised as
dangerous, the appraisal raises arousal, the raised arousal produces more
sensation, which confirms the appraisal. In SOMA the circle is built from
two verbs: a flutter drives the heart a little, and a catastrophizing
appraisal *reads* the heart and *drives* the heart — the loop senses the
very channel it raises. The result is a system with **two stable states**
and a sharp threshold between them, not a single dial that scales smoothly.

```python
"""
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
"""
from soma.narrative import Story, anxious, run_with, outcome, series


ATTACK = 115.0     # sustained heart above this = a panic attack, by definition


def build(*, alarm_at=88.0, flutter=6.0, flutter_beats=(3, 4),
          reassurance_at=None):
    """One person, one flutter, and a prior about what flutters mean.

    alarm_at: the heart level at which the catastrophizing appraisal engages --
              the body's tolerance for its own noise. 999 = no catastrophizing.
    flutter:  the trigger's strength.
    reassurance_at: optionally, a beat at which regulation arrives (a hand on
              the shoulder, a breath count) -- a down-driver on the same heart.
    """
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
```

**Output:**

```
==========================================================================
I. THE CIRCLE VS. THE SHRUG — same flutter, two priors
==========================================================================

  the catastrophizer (alarm at 88): heart [20, 35, 46, 132, 132, 132, 132, 132, 132, 132, 132, 132, 132, 132, 132, 132, 132, 132, 132]
    -> ATTACK: True; terror fired 16 times
  the shrug (no catastrophic prior): heart [20, 35, 46, 92, 92, 92, 92, 92, 92, 92, 92, 92, 92, 92, 92, 92, 92, 92, 92]
    -> attack: False; the same flutter, carried uninterpreted

==========================================================================
II. THE TIPPING FLUTTER — the smallest palpitation that panics
==========================================================================

    flutter 1: passes
    flutter 2: passes
    flutter 3: passes
    flutter 4: ATTACK
    flutter 5: ATTACK
    flutter 6: ATTACK
    flutter 7: ATTACK
    flutter 8: ATTACK

  the threshold is SHARP: below flutter 4 nothing happens at all; at 4, the
  full attack. Panic's all-or-nothing character is the signature of a system
  with two attractors and a separatrix between them, not of a dial.

==========================================================================
III. HYSTERESIS — the attack outlives its trigger
==========================================================================

  the flutter ends at 5s. The heart, after: [132, 132, 132, 132, 132, 132, 132, 132, 132, 132, 132, 132, 132]
  The spiral is SELF-SUSTAINING: heart above the alarm keeps the
  appraisal firing, which keeps the heart above the alarm. Two
  stable states — rest and attack — and the flutter only chose
  between them. The way back is not the way in:

  with regulation arriving at 9s: heart [20, 35, 46, 132, 132, 132, 132, 132, 132, 68, 68, 68, 68, 68, 68, 68, 68, 68, 68]
  Removing the trigger did nothing; only a DOWN-driver — the
  regulation the spiral itself cannot supply — exits the attack
  state. (Cramer & Borsboom's hysteresis in symptom networks: the
  path out requires more than undoing the path in.)

==========================================================================
IV. THE EXPOSURE MARGIN — the tolerance that prevents the attack
==========================================================================

  Interoceptive exposure works by habituation: the sensation level
  the body can carry WITHOUT engaging the catastrophic appraisal
  rises. Sweeping that tolerance against the same flutter:

    tolerance 86: ATTACK
    tolerance 88: ATTACK
    tolerance 90: ATTACK
    tolerance 92: no attack
    tolerance 94: no attack
    tolerance 96: no attack
    tolerance 98: no attack

  THE MARGIN: tolerance 92 is enough — the flutter peaks at 92, so the
  therapy has a computable target: teach the body to carry 92
  uninterpreted, and this trigger cannot reach the circle at all.
  The prediction is quantitative and falsifiable per-person: the
  margin is the flutter's peak, not a universal number.
```

**What the output means.** **I.** The same small flutter is given to two priors. The catastrophizer's
heart rate locks at 132 and stays there — the attack — while a character
with no catastrophic prior carries the identical flutter up to 92 and it
settles, uninterpreted. Same input, two entirely different outcomes,
because interpretation is what makes it a panic attack rather than a
sensation.

**II. The tipping flutter** sweeps the trigger's strength and finds panic's
signature: below strength 4, *nothing happens at all*; at 4, the *full*
attack, immediately. There is no gradual middle — the threshold is sharp,
which the commentary correctly reads as the signature of two attractors
separated by a boundary, not of a dial with a smooth response curve.

**III. Hysteresis** is the result that has no analogue anywhere else in this
tutorial. The flutter ends at 5 seconds — the trigger is *gone* — and the
heart rate stays locked at 132 anyway, because the appraisal-arousal circle
is now sustaining itself: high heart rate keeps the catastrophic appraisal
firing, which keeps the heart rate high, with no external input required.
Removing the trigger does nothing. Only an explicit *down-driver* —
regulation arriving from outside the circle — exits the attack state. The
path out is not the reverse of the path in.

**IV. The exposure margin** turns this into a therapeutic prediction: as the
body's tolerance for unexplained sensation rises (interoceptive exposure's
mechanism), the same flutter stops triggering the circle once tolerance
passes the flutter's own peak (92). The margin is quantitative and
falls out of the model, not a universal number — it is specific to how
strong this person's trigger is.

**The novelistic insight.** Bistability is a different kind of character claim than anything else in
this tutorial: not "how strongly does she feel this" but "which of two
qualitatively different states is she in, and how far is the boundary."
It explains something ordinary accounts of emotion struggle with — why a
panic attack can persist well after whatever triggered it is gone, why
"just calm down" doesn't work from inside the loop, and why exposure
therapy's target is a *margin* (a tolerance to build) rather than a feeling
to suppress. A character written with this structure doesn't have panic as
a mood that rises and falls with the scene; they have a boundary they can
cross, after which the scene's content stops mattering.

---

### 5.6 The Strange Situation, in full — construct validity turned on itself

**The idea.** Four children go through Ainsworth's eight-episode protocol in this
file, one after another, and a coder who never sees which attachment
style was installed has to name all four correctly. Section 3.8 ran the
Strange Situation once, on one child, to show what a single coded tape
looks like; this capstone runs the complete study the protocol was
designed to support — all four styles coded blind, the validity check
that recovers them, and then the instrument's two most telling
demonstrations: a child built from scratch with no style installed from a
lookup table, and the felt-but-disowned split Section 3.3 first
described, staked as a formal claim against the tape rather than told as
a standalone story.

```python
"""
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
"""
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
```

**Output:**

```
==========================================================================
I. FOUR CHILDREN, ONE SCRIPT — the protocol codes them apart
==========================================================================

  [installed: secure — the coder below never sees this]
STRANGE SITUATION — Noa, coded from the behavior stream alone:
    first_reunion    seek 6.4  maintain 6.4  avoid 1.6  resist 1.0
    second_reunion   seek 6.4  maintain 6.4  avoid 1.6  resist 1.0
    disorganization index: absent | physiological arousal over displayed calm: absent | settles by the end: yes
    -> CLASSIFICATION: SECURE

  [installed: anxious — the coder below never sees this]
STRANGE SITUATION — Noa, coded from the behavior stream alone:
    first_reunion    seek 7.0  maintain 7.0  avoid 1.0  resist 6.3
    second_reunion   seek 7.0  maintain 7.0  avoid 1.0  resist 6.3
    disorganization index: absent | physiological arousal over displayed calm: absent | settles by the end: NO
    -> CLASSIFICATION: ANXIOUS

  [installed: avoidant — the coder below never sees this]
STRANGE SITUATION — Noa, coded from the behavior stream alone:
    first_reunion    seek 1.7  maintain 1.7  avoid 6.3  resist 1.0
    second_reunion   seek 1.7  maintain 1.7  avoid 6.3  resist 1.0
    disorganization index: absent | physiological arousal over displayed calm: PRESENT | settles by the end: yes
    -> CLASSIFICATION: AVOIDANT

  [installed: disorganized — the coder below never sees this]
STRANGE SITUATION — Noa, coded from the behavior stream alone:
    first_reunion    seek 4.3  maintain 4.3  avoid 3.7  resist 6.3
    second_reunion   seek 4.3  maintain 4.3  avoid 3.7  resist 6.3
    disorganization index: PRESENT | physiological arousal over displayed calm: absent | settles by the end: NO
    -> CLASSIFICATION: DISORGANIZED

==========================================================================
II. CONSTRUCT VALIDITY — blind recovery of every installed style
==========================================================================

    ✓ installed secure        -> classified secure
    ✓ installed anxious       -> classified anxious
    ✓ installed avoidant      -> classified avoidant
    ✓ installed disorganized  -> classified disorganized

    INSTRUMENT VALID: all four styles recovered from behavior alone

==========================================================================
III. THE CHILD NOBODY LABELED — classification as discovery
==========================================================================

STRANGE SITUATION — Kit, coded from the behavior stream alone:
    first_reunion    seek 7.0  maintain 7.0  avoid 1.0  resist 6.3
    second_reunion   seek 7.0  maintain 7.0  avoid 1.0  resist 6.3
    disorganization index: absent | physiological arousal over displayed calm: absent | settles by the end: NO
    -> CLASSIFICATION: ANXIOUS

  (No table was consulted. The tape says who this child is: the
  clinging that will not soothe — coded as the pattern it matches.)

==========================================================================
IV. WHAT THE TAPE CAN'T SHOW — preregistered, then checked
==========================================================================

  The avoidant child LOOKS calm on the tape. The instrument that
  sees both registers — the narrated account and the body's own
  record — was preregistered to find them split:

  physiological arousal over displayed calm: PRESENT — confirmed (peak 115.0, classified avoidant)

  (Sroufe & Waters 1977; Diamond et al. 2006: the A-pattern's
  independence is a performance the heart never joins.)
```

**What the output means.** **I.** All four installed styles are coded from behavior in one pass, and
each reunion-scale reading is a small portrait on its own: secure shows
high seeking and low avoidance, settling by the end; anxious shows high
resistance and does *not* settle; avoidant shows high avoidance and — the
detail Section 3.3 flagged — physiological arousal present under a calm
surface; disorganized is the only profile with its disorganization index
present at all, and it does not settle either.

**II.** The blind classifier recovers all four installed styles from
behavior alone, with no access to what was installed — the same validity
result Section 3.8 showed, now stated as a table with all four rows
visible together.

**III. The child nobody labeled** is the sharpest demonstration in the
file. Kit is not built with `attaches(style=...)` from the temperament
table at all — Kit is hand-built from raw appraisal verbs, with the
attachment style explicitly marked unknown (`style="?"`) at construction.
The coder has no table to consult and no answer to check against; it reads
the tape exactly as it would for any other child, and returns ANXIOUS. This
is classification as *discovery*, not lookup — the same instrument that
recovers an installed label in Part II can also assign one to a character
who was never given one, which is the actual use case for a coding scheme
in practice: nobody hands a real clinician the ground truth.

**IV.** The avoidant child's split — narrated calm over measured
physiological arousal — is preregistered specifically against the protocol
(not a standalone story, as in Section 3.3) and confirmed: peak heart rate
115, classified avoidant, arousal present despite displayed calm.

**The novelistic insight.** Knowing an instrument works is one thing; knowing what it's actually
good for is another. Kit shows the real use case: not just recovering
labels you already know, but assigning one to a character built without
any label in mind — which is the situation a novelist is actually in when
a character arrives by instinct rather than by type. The instrument
doesn't require you to decide the attachment style before you write the
child; it can tell you afterward, from nothing but how the child behaves
in one scene. That reverses the usual relationship between psychological
theory and craft: theory doesn't have to precede the character, it can
follow from one faithfully imagined.

---

### 5.7 Twelve seconds in a jury room — a deadline, made quantitative

**The idea.** Four jurors deliberate on identical evidence in this file, and what
separates them is nothing about the case — only how each one's mind
accumulates it. Section 3.7 showed five decision temperaments and the
speed-accuracy tradeoff from one boundary; this capstone stages the same
drift-diffusion model as an actual jury deliberation and pushes one step
further than Section 3.7 had room for: not just how caution trades
against speed, but what happens to a group's verdicts when a *clock* is
added — the deadline every real jury eventually faces.

```python
"""
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
"""
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
```

**Output:**

```
==========================================================================
I. FOUR WAYS TO DECIDE — same evidence, four signatures
==========================================================================

    juror                accuracy   RT (correct)   RT (error)   skew
    ------------------------------------------------------------------
    Halden the careful      86%        3.40s        3.45s     +0.68
    Reine the quick         66%        0.93s        0.94s     +2.31
    Ada the sharp-eyed      92%        1.78s        1.76s     +1.60
    Coll the sure           86%        1.61s        2.65s     +1.78

  Halden (wide boundary) is slow and right; Reine (narrow) is quick
  and often wrong -- same evidence quality, opposite caution. Ada
  (high drift: she simply sees more) is fast AND right, the one
  combination caution alone can't buy. Every RT distribution leans
  right, the DDM's fingerprint.

==========================================================================
II. THE TELL OF A BIAS — fast convictions, slow acquittals
==========================================================================

  Coll starts already leaning toward 'guilty'. When the evidence
  agrees, the verdict comes fast: 1.60s. When the
  evidence points the other way, the walk has to climb all the way
  back across the room, and the RARE correct acquittal is SLOW:
  2.73s — +1.14s slower.

  That asymmetry — fast one way, slow the other — is the
  fingerprint of a prior. A juror without one shows no such gap; a
  symmetric model cannot produce it at all. The bias is legible in
  the TIMING even when the verdict is correct.

==========================================================================
III. THE SPEED-ACCURACY DIAL — hurry, then be sure
==========================================================================

SPEED-ACCURACY TRADEOFF — Juror, boundary swept (drift held fixed):
    boundary   accuracy   mean RT
      0.50        64%     0.84s
      0.80        71%     1.63s
      1.10        77%     2.49s
      1.50        84%     3.44s
      2.00        90%     4.24s
    ✓ CONFIRMED: wider boundary raises accuracy (more evidence, fewer errors) — ['64%', '71%', '77%', '84%', '90%']
    ✓ CONFIRMED: wider boundary lengthens RT (more evidence takes longer) — ['0.84', '1.63', '2.49', '3.44', '4.24']

  One juror, one evidence quality, five instructions from the
  foreman — from 'we haven't got all day' to 'be certain'. The
  tradeoff is smooth and monotone, and it dissociates two things
  ordinary language conflates: this is the SAME juror being more
  careful, not a better one. Only the boundary moved.

==========================================================================
IV. THE DEADLINE — how accuracy collapses under the clock
==========================================================================

  The judge imposes a deadline: decide within T, or it's a mistrial.
  We read accuracy AMONG the verdicts actually returned in time,
  for a careful juror (wide boundary) as the clock tightens:

    deadline    verdicts returned    accuracy of those
      1.0s            2%                 88%
      1.5s           10%                 85%
      2.0s           19%                 84%
      3.0s           38%                 84%
      5.0s           64%                 84%
      none           85%                 84%

  A tight deadline doesn't just lose the slow deciders — it
  systematically keeps the EASY verdicts (which finish first) and
  discards the hard ones, so the returned verdicts look accurate
  while the hard cases go undecided. The foreman's real dilemma,
  made quantitative: haste doesn't lower accuracy evenly, it hides
  the cases that most needed the time.
```

**What the output means.** **I.** Four jurors face identical evidence and differ only in DDM
parameters, giving four distinct signatures: careful (wide boundary: slow,
accurate), quick (narrow boundary: fast, error-prone), sharp-eyed (high
drift: fast *and* accurate — better evidence quality, the one combination
caution alone can't buy), and a fourth, biased juror held for Part II.

**II. The tell of a bias** isolates what Section 3.7 only touched on. A
juror who starts already leaning toward "guilty" reaches that verdict fast
when the evidence agrees, but a *correct acquittal* — evidence overturning
the lean — takes over a second longer, because the accumulating evidence
has to climb back across the whole width of the initial bias before it can
reach the opposite boundary. The asymmetry is specifically in the *timing*
of correct answers, which is a signature a model without a starting bias
cannot produce at all.

**III.** The speed-accuracy tradeoff is traced again with a finer sweep (five
boundary settings here instead of four) and framed as five foreman
instructions, from "we haven't got all day" to "be certain" — the same
underlying tradeoff Section 3.7 showed, restated as the lived experience of
being told to hurry or to be sure rather than as a bare table of numbers.

**IV. The deadline** is new. Instead of asking how accuracy changes as
caution changes, it asks what happens to a *fixed*, careful juror when a
clock is added. The result is the study's sharpest finding: as the
deadline tightens from unlimited down to 1 second, the fraction of
verdicts returned in time collapses from 85% to 2% — but the accuracy
*of the verdicts that do get returned* barely moves (84% to 88%). A tight
deadline doesn't make the jury wrong more often; it makes the jury silent
on the hard cases and confident on the easy ones, while looking, from the
verdicts alone, just as reliable as ever.

**The novelistic insight.** This is a case where the composed study finds something neither
component would show alone. A naive read of "the deadline doesn't hurt
accuracy much" would be reassuring; the actual finding is closer to
alarming, once you notice what's being measured. The jury isn't getting
better at hard cases under time pressure — it's failing to return a
verdict on them at all, and the accuracy number is silently computed only
over the easy cases that happened to finish first. The reassuring
statistic ("we're just as accurate as ever") and the buried truth it's
quietly excluding ("we simply stopped ruling on the hard ones") are the
same event, read two ways — a courtroom drama, a newsroom, or a boardroom
under deadline all run on that same quiet substitution.

---

### 5.8 What the body learns — two theories of learning, side by side

**The idea.** Conditioning and learned helplessness meet in one file here, run back
to back rather than in Sections 3.5 and 3.6's separate treatments. The
point of putting them together is not new results — every finding below is
one you've already seen — but the family resemblance that only becomes
visible side by side: both are prediction-error machines built on the same
loop, and the question this capstone actually asks is what changes when
the identical primitive is pointed at two different things.

```python
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
```

**Output:**

```
==========================================================================
I & II. THE DOPAMINE CURVE, AND SPONTANEOUS RECOVERY
==========================================================================

CONDITIONING — Bell: tone → food (value = acquired + context trace)
    acquisition  ▁▁▅▇██████  [0.0 → 7.5]
    extinction   ██▃▂▁▁▁▁▁▁▁▁  [7.5 → 0.5]
    rest         ▂▃▄▅▆▆▇▇▇█  [1.7 → 6.5]
    reacquisition ▁▁▅▇██  [0.5 → 7.5]
    peak RPE (unpredicted reward): +7.20; once predicted it falls toward 0 — dopamine's signature
    ✓ CONFIRMED: acquisition: value climbs to near the reward — peaked at 7.5
    ✓ CONFIRMED: the RPE shrinks as reward becomes predicted (dopamine's signature) — 3.60 → 0.46
    ✓ CONFIRMED: extinction: the conditioned value falls — 7.5 → 0.5
    ✓ CONFIRMED: SPONTANEOUS RECOVERY: after rest the value returns (extinction was new learning, not erasure) — 0.5 → 6.5 after rest
    ✓ CONFIRMED: savings: relearning starts from the intact trace and is no slower — 5 vs 4 beats; starts 0.5 vs 0.0

  The value climbs as the tone comes to predict food; the reward
  prediction error — the dopamine signal — is largest at the first
  unpredicted reward and falls toward zero as the prediction
  improves. Extinction drives the value down. Then a REST, with no
  tone and no food, and the response RETURNS on its own: the proof
  that extinction never erased the original — it layered a new,
  fragile 'not anymore' over a trace that outlasts it. A single
  value could not do this; two traces can. (Pavlov 1927; Bouton.)

==========================================================================
III & IV. THE TRIADIC DESIGN AND THE TRANSFER ASYMMETRY
==========================================================================

  The full triadic design — three pretreatments x two explanatory
  styles x similar/dissimilar novel task — coded for the
  helplessness deficit:

    style      pretreatment      novel task    outcome
    ------------------------------------------------------------
    global     controllable      dissimilar    copes
    global     controllable      similar       copes
    global     none              dissimilar    copes
    global     none              similar       copes
    global     uncontrollable    dissimilar    DEFICIT
    global     uncontrollable    similar       DEFICIT
    specific   controllable      dissimilar    copes
    specific   controllable      similar       copes
    specific   none              dissimilar    copes
    specific   none              similar       copes
    specific   uncontrollable    dissimilar    copes
    specific   uncontrollable    similar       DEFICIT

  Read the uncontrollable rows: the deficit appears ONLY after
  uncontrollable adversity (controllable and none immunize), and
  its reach is set by explanatory style. GLOBAL ('I ruin
  everything') carries the helplessness into a wholly unrelated
  task; SPECIFIC ('I couldn't do that one thing') confines it to
  situations like the first.

  reformulation's full pattern reproduced: True
  transfer asymmetry (global transfers, specific does not): True

  Two people, the same defeat, different futures — and the dividing
  line is not the event but the sentence each says about it. That
  is the reformulation's whole claim, and here it is mechanism:
  a global style is one control-belief shared across every task; a
  specific style keeps a separate belief per task, so a dissimilar
  task starts fresh. The scope of the belief IS the explanatory
  style. (Abramson, Seligman & Teasdale 1978; Alloy et al. 1984.)
```

**What the output means.** **Part I & II** reproduce Section 3.5's conditioning study exactly,
number for number: the same acquisition, extinction, rest, and
reacquisition sparklines, the same dopamine signature in the shrinking
reward-prediction error (peak +7.20, falling toward 0.46), and the same
spontaneous recovery after rest (0.5 → 6.5 with no tone and no food in
between). Nothing here is new; what's worth noticing is *what kind* of
prediction this is — a sensory one. The loop's `sense:` channel is the
tone, and the error it computes is the gap between the tone's predicted
and actual consequence.

**Part III & IV** reproduce Section 3.6's full triadic design and the
transfer asymmetry exactly as well: a deficit only after uncontrollable
adversity, and only a global explanatory style carrying it into an
unrelated task. Here the same loop's error is computing something
different — not whether a sensory cue predicts an outcome, but whether an
*action* does. The `agency` channel from Section 3.6 stands in for that
belief, and the same value-loop machinery that learned "tone predicts
food" in Part I now learns "my actions predict relief" or "they don't."

Put the two side by side and the file's own framing becomes literal, not
just a figure of speech: "both fall straight out of SOMA's loop, whose
error term IS a prediction error." The code makes this concrete —
`conditioning_study()` and `helplessness_study()` are peer functions,
called one after the other, each wiring the identical loop primitive to a
different question. Conditioning is what that loop does when the world is
genuinely learnable; helplessness is what it does when the world stops
answering, and the character's belief about *why* determines how far the
resulting deficit reaches.

**The novelistic insight.** A mind updates on the gap between what it expected and what it got —
seven words that, attached to two different channels, produce two of
psychology's most quantitatively validated and least alike-looking
theories. Seeing them side by side, sharing an author's framing rather
than each getting its own isolated section, is itself a small piece of
evidence for the loop's generality — the same primitive that explains a
dog salivating to a bell also explains why one person's defeat stays
contained and another's spreads to everything they touch. A single
mechanism, two very different-looking outcomes, depending only on what the
error signal is attached to and how far its consequences are allowed to
travel.

## Part 6 — Putting it together

Each simulation in Parts 3 and 4 is a self-contained lens; Part 5 showed that
they compose. A single character can carry an attachment style, a defended
belief with a tipping point, a decision temperament, and a preregistered
forecast — and the insight tools (sensitivity, counterfactual) can then
interrogate any outcome that results, exactly as the capstone studies just did.
The narrative-only examples that also ship with SOMA (`the_negotiator`,
`two_sisters`, `the_diplomat`, in the SOMA-mode example rail) build the same
kind of many-layered person without the prediction/insight machinery turned
on them — the pressure at which a composed professional's honesty becomes a
lie, the resentment a sister hides behind grace, the longing a diplomat
defends against and never acts on. Worth reading once you've seen what the
full instrument can do.

### The common shape of every prediction

Look back and you will see one shape repeated:

1. **Build** a character in the vocabulary of feelings, beliefs, relationships.
2. **Stake** a forecast — a specific, falsifiable claim about what they will do.
3. **Run** them forward; the Chronicle records what the body actually did.
4. **Check** the forecast against the Chronicle.
5. **Interrogate** the result: which trait drove it, what would have flipped it.

And every simulation leads with the prediction a *simpler* account could not
make — spontaneous recovery for conditioning, the transfer asymmetry for
helplessness, the slow-error signature for a biased decision, blind recovery for
the Strange Situation, the thin-slice for Gottman. That is what keeps these
genuinely *predictive* rather than merely descriptive: each one stakes a claim
that could come out false, and doesn't.

### Why this yields novelistic insight

A novel's deepest claims are causal and counterfactual: *this person feels this
because she read the situation that way; the marriage failed because each cut was
answered in kind; he would have survived if he had been a little less sure.*
These are exactly the claims the library makes checkable. The simulations do not
replace a writer's judgment; they externalize the *mechanism* beneath an
intuition, so you can compose feelings from situations, doom or save a couple by
one reliable rule, and locate the precise margin an ending balanced on. The most
useful thing the library keeps is the body's record beneath the narrator's
account: the gap between what a person says and what is true, which is where most
of fiction lives.

### Where to go next

- Try modifying any example above in the **Library** editor: change a
  temperament, a threshold, a couple type, and re-run.
- Use `story.source()` on anything you build, copy the SOMA into **SOMA** mode,
  and inspect or perturb it directly.
- The eight **capstone** examples in the Library rail (Part 5) are the
  full, unedited command-line studies — run any of them directly with
  `python3 examples/narrative/<name>.py` for output at full terminal width,
  or keep editing them in the browser.
- The SOMA-mode rail's narrative-only examples (`the_negotiator` and the
  others) build equally layered characters without the prediction/insight
  tools turned on them — read those for the craft, then bring what Part 5
  taught to bear on them yourself.
- The reference for the prediction layers is `PREDICTION.md`; the base language
  is documented in `GRAMMAR.md` and taught in `TUTORIAL.md`.

Every claim in this tutorial is a claim about a *model* of a character, never
about a real person — that caveat is printed on the predictions themselves, and
it is the right frame: these are instruments for thinking precisely about
imagined people, and precision, here, is the whole source of the insight.
