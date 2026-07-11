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

## Part 5 — Putting it together

Each simulation above is a self-contained lens, but they compose. A single
character can carry an attachment style, a defended belief with a tipping point,
a decision temperament, and a preregistered forecast — and the insight tools
(sensitivity, counterfactual) can then interrogate any outcome that results. The
richer examples that ship with SOMA (`the_negotiator`, `two_sisters`,
`the_diplomat`, in the SOMA-mode example rail) do exactly this: they build one
person out of many layers and then *predict* them — the pressure at which a
composed professional's honesty becomes a lie, the resentment a sister hides
behind grace, the longing a diplomat defends against and never acts on.

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
- Read the shipped examples in the SOMA-mode rail (`the_negotiator` and the
  others) for characters that combine many layers, and run their `--predict`
  studies from the command line for the fuller analyses.
- The reference for the prediction layers is `PREDICTION.md`; the base language
  is documented in `GRAMMAR.md` and taught in `TUTORIAL.md`.

Every claim in this tutorial is a claim about a *model* of a character, never
about a real person — that caveat is printed on the predictions themselves, and
it is the right frame: these are instruments for thinking precisely about
imagined people, and precision, here, is the whole source of the insight.
