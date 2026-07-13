# Predictive Characterization in SOMA — A Tutorial

*A self-contained guide to the high-level libraries for turning a described
character into falsifiable predictions.*

Generated against SOMA 0.26.0. Every code block in this tutorial was executed
through the same library the browser playground uses; every output block is the
real, unedited result of running the code directly above it.

---

## What this tutorial is about

Most character work — in fiction, in psychology, in everyday judgement — stops
at description: *she is anxious*, *he is guarded*, *they have trust issues*. A
description is not a prediction. It does not tell you what the person will feel
in a situation you have not yet seen, which of two people will crack first, or
what the smallest change is that would give a marriage a different ending.

**Predictive characterization** is the practice of turning a described
character into a *generative model* — a small simulation whose structure is the
person — and then reading predictions off it. The unit of a prediction here is
not a label but a **falsifiable claim**: *this character, in this unseen
situation, will do this*, computed rather than asserted, and reproducible so
that it either holds when you run it or does not.

SOMA is a small language for simulating the mind–body loop. Its high-level
libraries (`soma.narrative`) let you author a character in a dozen lines — in
terms of what they sense, what they believe, and how they feel — and then apply
a growing family of instruments that each extract a different kind of
prediction. This tutorial walks that family from the simplest idea to the most
elaborate, always in the same shape: **the concept, the code, the generated
output, and what the output means.**

**A companion tutorial.** This document covers the *predictive
characterization* layers — signature, self-guides, density, landscape, network,
inverse problem, choice, theory of mind, the tell, and legitimacy/system
justification (the 0.15–0.25 work). Its companion,
[`TUTORIAL_PREDICTIVE.md`](TUTORIAL_PREDICTIVE.md), covers the earlier
*prediction* layers — appraisal, attachment, tipping points, conditioning, the
Gottman model, drift-diffusion decisions, and the sensitivity/counterfactual
insight tools. The two are complementary: read either first. Everything in both
runs unmodified in the browser playground (`index.html`) in **Library** mode.

---

## Part 1 — The basic concepts

### 1.1 A character is a loop

The smallest useful object is a `Story` — a little world with a clock — holding
a `Character`. A character has *senses* (channels the world can push on) and
*appraisals* (rules that turn what is sensed into a feeling). When you run the
story, the character's loop reads the world each tick and may emit a feeling.


```python
from soma.narrative import Story, tender

# A Story is a little world with a clock. A character lives in it.
story = Story("a first feeling", span="6s", step="1s", about="being seen")
ivy = story.character("Ivy", temperament=tender)

# Ivy has a sense (a channel the world can push on) and an appraisal:
# a rule that turns what she senses into a feeling.
ivy.senses("a_smile", baseline=0)
ivy.appraises("a_smile", feeling="warmth", when="a_smile > 3")

# The world does something at 2 seconds.
story.at("2s", ivy.hears("a_smile", 7))

# Run the loop and print the dashboard.
print(story.run(width=72))
```

Output:

```
──────────────────────── SOMA · a first feeling ────────────────────────
╭─ BODY · channels over time ──────────────────────────────────────────╮
│   extero a_smile      ▁▁█████  0→7
╰──────────────────────────────────────────────────────────────────────╯
╭─ NARRATOR vs GROUND TRUTH ───────────────────────────────────────────╮
│   THE STORY SHE TELLS                 THE BODY'S RECORD
│   ───────────────────────────────────────────────────────────────────
│                                     │ 2.0s (5x) feels Qualia<warmth>
╰──────────────────────────────────────────────────────────────────────╯
╭─ WINNOW-S · storyful moments, ranked ────────────────────────────────╮
│   ███████··· delight in error
│      5 times across 4.0s the prediction failed and the failure felt
│      like warmth -- being surprised, and glad of it.
╰──────────────────────────────────────────────────────────────────────╯
╭─ CHRONICLE · trace (13 of 13 events) ────────────────────────────────╮
│     0.0s settle   appraising_a sense=0.0 belief=0.0 error=0.0 pi_s=0…
│     1.0s settle   appraising_a sense=0.0 belief=0.0 error=0.0 pi_s=0…
│     2.0s stimulus a_smile      value=7.0
│     2.0s settle   appraising_a sense=7.0 belief=0.0 error=6.16 pi_s=…
│     2.0s emit     appraising_a quale=Qualia<warmth>
│     3.0s settle   appraising_a sense=7.0 belief=0.0 error=6.16 pi_s=…
│     3.0s emit     appraising_a quale=Qualia<warmth>
│     4.0s settle   appraising_a sense=7.0 belief=0.0 error=6.16 pi_s=…
│     4.0s emit     appraising_a quale=Qualia<warmth>
│     5.0s settle   appraising_a sense=7.0 belief=0.0 error=6.16 pi_s=…
│     5.0s emit     appraising_a quale=Qualia<warmth>
│     6.0s settle   appraising_a sense=7.0 belief=0.0 error=6.16 pi_s=…
│     6.0s emit     appraising_a quale=Qualia<warmth>
╰──────────────────────────────────────────────────────────────────────╯
```


Read the dashboard top to bottom. **BODY** shows the sensed channel `a_smile`
rising from 0 to 7 at the two-second mark. **NARRATOR vs GROUND TRUTH** contrasts
what the character could say with what her body actually recorded — here, she
feels *warmth* on every tick from 2.0s on, five in all. **WINNOW** ranks the
storyful moments: the
model has recognized this as "delight in error" — the prediction (that nothing
was there) failed, and the failure felt good. The **CHRONICLE** is the raw
trace: at 2.0s a stimulus of 7 arrives, the prediction error jumps to 6.16, and
an `emit` fires `warmth`. Every later tick re-emits because the smile persists.

The point: you described nothing about *warmth* directly. You said Ivy senses a
smile and appraises it as warmth past a threshold, and the loop generated the
feeling, its timing, and its intensity. That generativity is what makes
prediction possible.

### 1.2 The library compiles to a language

The narrative library is a convenience layer. Underneath, it writes ordinary
SOMA — the base language of bodies, loops, and arbitration. You can always read
what it produced, which is useful for understanding exactly what a character
*is*.


```python
from soma.narrative import Story, tender

story = Story("a first feeling", span="6s", step="1s", about="being seen")
ivy = story.character("Ivy", temperament=tender)
ivy.senses("a_smile", baseline=0)
ivy.appraises("a_smile", feeling="warmth", when="a_smile > 3")
story.at("2s", ivy.hears("a_smile", 7))

# The library COMPILES to SOMA, the base language. You can read what it wrote:
print(story.source())
```

Output:

```
// a first feeling -- generated by soma.narrative
// Every construct below was produced from a high-level narrative description;
// it is ordinary SOMA and can be edited, run, sifted, prosed, and perturbed.

sim { duration: 6s  dt: 1s }

body Ivy_body @cardiac {
  extero a_smile : Signal baseline 0
}

loop appraising_a_smile @cardiac {
  prior:      predict(0)
  sense:      a_smile
  precision:  0.88
  conviction: 0.2
  act {
    emit feel(warmth) when a_smile > 3
  }
}

stimulus a_smile { at 2s: 7 }
```


Notice the `loop` block: `precision: 0.88` and `conviction: 0.2` came from the
`tender` temperament, and the `predict(0)` line is the prior expectation. The
appraisal became a guard (`when a_smile > 3`) and an `emit feel(warmth)`. The
high-level `appraises(...)` call is sugar for this; anything you can author in
the library, you can read, check, and perturb as SOMA.

### 1.3 Temperament is two dials that arbitrate

The engine of every prediction in this tutorial is one idea: perception is a
contest between what you *sense* and what you already *believe*, and a
temperament sets who wins. Two dials do the arbitrating — **precision** (trust
in the senses) and **conviction** (trust in the prior). Watch the same evidence
move two temperaments' beliefs at different speeds.


```python
from soma.narrative import Story, tender, guarded

# A temperament is two dials that arbitrate between the senses and the prior:
#   precision  = trust in what is sensed   (tender 0.88, guarded 0.45)
#   conviction = trust in the prior belief (tender 0.20, guarded 0.80)
# Watch the SAME evidence -- a face, shown steadily from 2s on -- move each
# person's belief at a different speed. Tender believes her eyes; guarded
# holds the prior and updates only grudgingly.
for temp in (tender, guarded):
    story = Story("learning a face", span="8s", step="1s", about="recognition")
    p = story.character("P", temperament=temp)
    p.senses("face", baseline=0)
    p.appraises("face", feeling="recognition", when="face > 3",
                updates=True, learn=0.1)
    for t in range(2, 8):
        story.at(f"{t}s", p.hears("face", 8))     # the face is really there
    story.run(width=60)
    r = story.result()
    belief = [round(e.detail.get("belief", 0), 1)
              for e in r.chronicle if e.kind == "settle"]
    print(f"{temp.name:<8} (precision {temp.precision}): belief -> {belief}")
```

Output:

```
tender   (precision 0.88): belief -> [0.0, 0.0, 0.0, 4.8, 6.7, 7.5, 7.5, 7.5, 7.5]
guarded  (precision 0.45): belief -> [0.0, 0.0, 0.0, 0.8, 1.5, 2.2, 2.8, 3.3, 3.8]
```


The face is really there (value 8, shown every tick from 2s on). `tender`, who
trusts her senses, drives her belief up to 7.5 within three ticks. `guarded`,
who trusts his prior, crawls to 3.8 over the same span — the same world, a
slower mind, because he weights his expectation more heavily than the evidence.

This is the whole basis of predictive characterization: **a character is a
particular setting of these dials, wired to particular senses and appraisals**,
and that setting determines everything downstream — what they feel, what they
choose, how they read other people, and how readable they are in turn. The rest
of this tutorial is a tour of instruments that each read a different prediction
off that same small machine.

---

## Part 2 — The prediction layers, simple to complex

The instruments below build in sophistication, and they fall into three groups.
The first three (2.1–2.3) predict a *single character's* responses across
situations: the profile of what they take in, the emotion a failure produces,
the distribution of states they occupy. The next three widen the lens from a
single response to the *space* of trajectories — first for a relationship
(2.4–2.5), then, turning the same idea inward, for a single psyche (2.6). The
next make a person *emergent* from a symptom network (2.7) and then recover
that network from behaviour (2.8), before moving from what a character feels to
what they *do*: how they choose (2.9), how they play against other minds (2.10),
and how readable they are in the process (2.11). The last (2.12) turns the whole
apparatus on a character's *loyalty to what harms them*, and derives even that
from their circumstances.

Two ideas recur and are worth watching for. The first is the **attractor**, a
stable state a trajectory settles into; it is introduced on a couple in 2.4 and
then reused, unchanged, on a single mind in 2.6. The second is the **inverse
move**, recovering hidden structure from behaviour alone, which appears first
for a symptom network in 2.8 and again for a mind's recursion depth in 2.10.


### 2.1 The signature — two people, the same average, different profiles (0.15)

The oldest mistake in personality measurement is the trait *average*: scoring a
person as "60% anxious" and stopping there. Mischel and Shoda's work on the
Wediko summer camp showed that two children with identical average aggression
can be opposite people — one aggressive *when adults demand*, the other *when
peers tease*. Character lives in the **if–then profile across situations**, not
the mean.

`signature` computes that profile. Here are two people built on the *same*
temperament, differing only in which situation they trust and which they defend
against.


```python
from soma.narrative import (Story, guarded, signature, similarity,
                            diagnostic_situation)

# Two people, the SAME temperament. What makes them different people is their
# if-THEN profile: which situations they take in, and which they defend against.
story = Story("wediko", span="8s", step="1s", about="acute distress")

ren = story.character("Ren", temperament=guarded)
ren.senses("judgment"); ren.senses("warmth")
ren.appraises("judgment", as_threat=True, feeling="fear",
              precision=0.3, conviction=0.9)          # distrusts judgment
ren.appraises("warmth", feeling="comfort",
              precision=0.9, conviction=0.2, updates=True)   # trusts warmth

sol = story.character("Sol", temperament=guarded)     # SAME temperament
sol.senses("judgment"); sol.senses("warmth")
sol.appraises("judgment", feeling="fear",
              precision=0.9, conviction=0.2, updates=True)   # trusts judgment
sol.appraises("warmth", as_threat=True, feeling="wariness",
              precision=0.3, conviction=0.9)          # distrusts warmth

battery = {"a judging eye": {"judgment": 8},
           "an open warmth": {"warmth": 8}}
sr = signature(story, ren, battery)
ss = signature(story, sol, battery)
print(sr.render()); print()
print(ss.render()); print()
print(f"profile similarity: {similarity(sr, ss):.2f} "
      f"(mean levels equal: {sr.mean_level() == ss.mean_level()})")
d = diagnostic_situation(story, ren, sol, battery)
print(f"the one situation that separates them: '{d['situation']}' "
      f"(separation {d['separation']})")
```

Output:

```
Behavioral signature -- Ren (if...then profile; every situation unseen; ▼ suppress ▲ take in ◆ breaks):
  ▼ if a judging eye            then they SUPPRESS it, feeling fear
  ▲ if an open warmth           then they TAKE IT IN, feeling comfort
  mean level (the trait-score view): suppresses 50%, takes in 50%, breaks 0%

Behavioral signature -- Sol (if...then profile; every situation unseen; ▼ suppress ▲ take in ◆ breaks):
  ▲ if a judging eye            then they TAKE IT IN, feeling fear
  ▼ if an open warmth           then they SUPPRESS it, feeling wariness
  mean level (the trait-score view): suppresses 50%, takes in 50%, breaks 0%

profile similarity: 0.33 (mean levels equal: True)
the one situation that separates them: 'an open warmth' (separation 0.75)
```


Ren *suppresses* a judging eye (he distrusts judgment — low precision, high
conviction) but *takes in* warmth; Sol is his mirror. Their **mean levels are
identical** (each takes in one situation and suppresses the other — the
program even confirms `mean levels equal: True`), yet their **profile
similarity is 0.33** — they are barely the same person situation-for-situation.

The final line is the practical pay-off: `diagnostic_situation` searches the
battery for the single situation that best *separates* the two — here "an open
warmth", with a separation of 0.75. This is a prediction you can act on: if you
want to tell these two apart, don't watch them under judgement (where they look
similar) — watch them offered warmth. The instrument doesn't just characterize;
it tells you what to observe.

### 2.2 The self-guides — the same failure, two different sufferings (0.15)

Higgins' self-discrepancy theory distinguishes two ways of falling short.
Failing to become who you *want* to be (the **ideal** self) yields
dejection-family emotions — sadness, disappointment, despair. Failing to become
who you feel you *must* be (the **ought** self) yields agitation-family
emotions — guilt, anxiety, tension. The library installs a self-guide and
predicts which family a given failure will produce.


```python
from soma.narrative import Story, anxious, selfguides

# Higgins' self-discrepancy theory: falling short of who you WANT to be
# (the IDEAL self) breeds dejection; falling short of who you feel you MUST be
# (the OUGHT self) breeds agitation. Same shortfall, different suffering --
# and the library derives which.
story = Story("the guides", span="8s", step="1s", about="acute distress")
nora = story.character("Nora", temperament=anxious)   # holds an ideal
theo = story.character("Theo", temperament=anxious)   # holds an ought

pi = selfguides.ideal(nora, "her_craft", standard=9.0)
po = selfguides.ought(theo, "providing", standard=9.0)
print(pi.gloss())
print(po.gloss())

# stage the same failure (severity 4) for both, and check the predicted feeling
out = selfguides.contrast(story, nora, theo, severity=4.0)
for who, v in out.items():
    mark = "CONFIRMED" if v["confirmed"] else "FALSIFIED"
    print(f"  {who}: predicted {v['predicted_family']} "
          f"('{v['predicted_quale']}'), felt {v['felt']} -- {mark}")
```

Output:

```
Nora: shortfall on 'her_craft' against an ideal (own standpoint) -> dejection family, default quale 'despair'; regulatory focus: promotion. [the hoped-for self did not arrive (dejection)]
Theo: shortfall on 'providing' against an ought (own standpoint) -> agitation family, default quale 'guilt'; regulatory focus: prevention. [a duty of one's own, broken (agitation)]
  Nora: predicted dejection ('despair'), felt ['despair'] -- CONFIRMED
  Theo: predicted agitation ('guilt'), felt ['guilt'] -- CONFIRMED
```


Nora holds an *ideal* about her craft; Theo an *ought* about providing. Both
fail by the same amount (severity 4). The library predicts Nora will feel
**dejection** ("despair") with a *promotion* regulatory focus, and Theo
**agitation** ("guilt") with a *prevention* focus — and when the failure is
actually staged, both predictions are **CONFIRMED** against what the loop emits.
The same objective shortfall produces two different sufferings, and which one is
predictable from the *structure* of the self-guide, not the size of the failure.

### 2.3 The density — the distribution is the person (0.15)

Fleeson's Whole Trait Theory reframes a trait as a *density distribution* of
states: nobody is anxious at a constant level; they occupy a characteristic
*spread* of states, and the shape of that spread — its width, its skew — is
itself the trait. `density` samples a person across many unseen provocations and
reports the shape.


```python
from soma.narrative import Story, anxious, stoic, density, compare_density

# Fleeson's Whole Trait Theory: a "trait" is really a DISTRIBUTION of states.
# The same provocations, sampled across a range, reveal the SHAPE of a person's
# reactivity -- and two people with different shapes live differently wide lives.
story = Story("widths", span="8s", step="1s", about="acute distress")

wren = story.character("Wren", temperament=anxious)    # reactive
wren.senses("news")
wren.appraises("news", as_threat=True, drives="heart", to=118,
               when="news > 6", fades_to=70)

moss = story.character("Moss", temperament=stoic)      # steady
moss.senses("news")
moss.appraises("news", as_threat=True, drives="heart", to=94, fades_to=70)

dw = density(story, wren, "news", samples=16, seed=3)
dm = density(story, moss, "news", samples=16, seed=3)
print(dw.render()); print()
print(dm.render()); print()
cmp = compare_density(dw, dm)
print(f"the wider life: {cmp['wider']}  "
      f"(sd {cmp['sd'][0]} vs {cmp['sd'][1]}; "
      f"reactivity {cmp['reactivity'][0]} vs {cmp['reactivity'][1]})")
```

Output:

```
Density -- Wren, arousal across 16 unseen situations on 'news':
  47 |█        ▂| 98   (the distribution IS the character)
  mean 56.33 (the trait score)   sd 20.10 (the width -- itself a trait)   skew +1.60
  range [46.67, 98.16]   reactivity to the cue +0.74

Density -- Moss, arousal across 16 unseen situations on 'news':
  47 |▁        █| 74   (the distribution IS the character)
  mean 70.73 (the trait score)   sd 9.09 (the width -- itself a trait)   skew -2.27
  range [46.67, 74.16]   reactivity to the cue +0.57

the wider life: Wren  (sd 20.096 vs 9.091; reactivity 0.736 vs 0.567)
```


Wren and Moss face the same range of news. Wren's states have **mean 56 with a
wide sd of 20** and a long right tail (skew +1.60) — she is usually calm but has
a heavy tail of alarm. Moss sits at **mean 71 with a narrow sd of 9**, skewed
the other way. The comparison names Wren as living "the wider life". These are
two different *distributions*, not two different points: if you only recorded
each person's average you would call Moss the more reactive, since his mean is
higher. The width — the part a single measurement hides — tells the truer story
about who is volatile.

### 2.4 The landscape — the space of a relationship's endings (0.16)

The instruments so far predict what one person feels. The next question is
larger: across *all* the ways a situation could open, where does it tend to end
up? For a relationship, this is a **phase portrait** — sweep every opening mood
for both partners and see which stable state (attractor) each trajectory
settles into. The library builds Gottman's couple types and maps their
landscapes.


```python
from soma.narrative import Story, trusting
from soma.narrative.gottman import marry
from soma.narrative.phase import phase_portrait

# 0.16 predicts the SPACE of a relationship's endings, not one ending. Build a
# couple, then sweep every opening mood and see where each trajectory settles.
def couple(kind):
    s = Story(f"{kind}", span="20s", step="1s", about="marital friction")
    a = s.character("Ada", temperament=trusting)
    b = s.character("Ben", temperament=trusting)
    marry(s, a, b, kind)
    return s

for kind in ("validating", "hostile"):
    p = phase_portrait(couple(kind), grid=4, beats=16)
    print(f"--- {kind} couple ---")
    print(p.render())
    print()
```

Output:

```
--- validating couple ---
PHASE PORTRAIT — Ada x Ben (1 attractor):
  w: (7.6, 7.6) [warm] holding 100% of the plane
  basins (Ada →, Ben ↑; w=warm):
      9.0 |wwww|
      6.3 |wwww|
      3.7 |wwww|
      1.0 |wwww|
          ----
  the warm basin holds 100% of the plane — the couple's resilience, as a region.

--- hostile couple ---
PHASE PORTRAIT — Ada x Ben (1 attractor):
  c: (2.4, 2.4) [cold] holding 100% of the plane
  basins (Ada →, Ben ↑; c=cold):
      9.0 |cccc|
      6.3 |cccc|
      3.7 |cccc|
      1.0 |cccc|
          ----
  NO WARM ATTRACTOR: every opening decays to the cold state. The landscape does not contain a good ending.
```


The grid letters each basin by its **temperature** — `w` for warm, `c` for
cold — so the two landscapes are legible at a glance: the validating couple's
plane is solid `w`, the hostile couple's solid `c`. (With a split landscape —
one whose openings can end in different attractors — the boundary between the
regions is drawn in the grid itself, and any two attractors sharing a
temperature fall back to index letters so the basins stay distinguishable.) The **validating couple's** entire plane drains into a single warm
attractor at (7.6, 7.6): whatever mood they start the evening in, they end up
warm — that is their resilience, shown as a region rather than asserted as a
virtue. The **hostile couple's** plane contains **no warm attractor at all**:
every opening, even a warm one, decays to the cold state at (2.4, 2.4). This is a prediction
about the *shape of their possibilities* — the hostile couple cannot reach a
good ending not because of bad luck on a given night but because their landscape
does not contain one.

### 2.5 The ensemble — the distribution over endings, and its pivot (0.16)

A phase portrait sweeps starting conditions. An **ensemble** sweeps the
*parameters* of the person — how much they trust a face, how fast being right
hardens them — across plausible ranges, and reads the distribution of endings,
then asks which dial the ending most *hinges* on (an effect size, Cohen's d).


```python
from soma.narrative import Story, anxious, futures, pivotal, by_outcome

# Instead of one run, sample a whole ENSEMBLE of nearby worlds -- vary two dials
# of one character within plausible ranges -- and read the DISTRIBUTION of
# endings, plus which dial the ending most hinges on (Cohen's d).
story = Story("trusting a face", span="12s", step="1s", about="reassurance")
soren = story.character("Soren", temperament=anxious)
soren.senses("her_face", baseline=50)
soren.appraises("her_face", feeling="reassurance", when="her_face > 55",
                updates=True, learn=0.06)
for t in range(2, 12):
    story.at(f"{t}s", soren.hears("her_face", 75))   # her face is warm

LOOP = "appraising_her_face"        # the loop the library generated
# an ending is "stays open" if he keeps perceiving her (vs armoring against her)
classify = by_outcome("perceive_frac", above=0.5,
                      labels=("stays open", "armors"), character="Soren")
rep = futures(story,
              {f"{LOOP}.learn": (0.0, 0.12),      # how fast being right hardens
               f"{LOOP}.precision": (0.55, 0.95)},  # how much he trusts her face
              classify, samples=24, seed=7)
print(rep.render())
print()
print("what the ending most hinges on (effect size, Cohen's d):")
for dial, d in pivotal(rep):
    print(f"  {dial:<32} d = {d:+.2f}")
```

Output:

```
FUTURES — trusting a face: 24 nearby worlds
  armors         █████████████████████████  96%
  stays open     █                          4%
  modal fate: 'armors'   settledness: destiny (entropy 0.25)

what the ending most hinges on (effect size, Cohen's d):
  appraising_her_face.learn        d = +1.41
  appraising_her_face.precision    d = -0.34
```


Across 24 nearby worlds, this marriage **armors 96% of the time** — the outcome
is nearly *destiny* (entropy 0.25), not a coin-flip. And the pivotal dial is the
**learning rate** (d = +1.41), far more than how much he trusts her face
(precision, d = −0.34). So the ensemble predicts more than "he will probably
close off"; it identifies the lever that decides it. What settles his fate is how
fast being right makes him harder to surprise, and barely at all how warm she is
— a quantitative claim about where an intervention would have to act.

### 2.6 The intrapersonal landscape — a disorder as an attractor (0.17)

Now turn the landscape *inward*. A single psyche can have more than one stable
state, and a disorder can be one of them. Robinaugh's panic model is a loop:
bodily arousal, misread as catastrophe, drives more arousal. The **arousal
schema** sets how readily the body is read as danger. `state_portrait` maps the
psyche's own plane.


```python
from soma.narrative import Story, anxious, state_portrait

# 0.17 turns the landscape inward: a single psyche can have two stable states.
# Robinaugh's panic model -- arousal, misread as danger, drives more arousal.
# The AROUSAL SCHEMA sets how readily the body is read as catastrophe.
def panic_person(schema):
    guard = round(85 - 50 * schema)          # high schema -> low bar to misread
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

port = state_portrait(panic_person(0.85), "Noa",
                      ("arousal", "perceived_threat"), grid=5, lo=0, hi=100,
                      beats=24, high_label="panic", low_label="calm",
                      healthy_is="low")
print(port.render())
print()
print("REAPPRAISAL -- raise the bar at which the body is read as danger:")
for schema in (0.85, 0.6, 0.4, 0.2):
    port = state_portrait(panic_person(schema), "Noa",
                          ("arousal", "perceived_threat"), grid=5, lo=0, hi=100,
                          beats=24, high_label="panic", low_label="calm",
                          healthy_is="low")
    panic = 1 - port.healthy_share
    gone = "  <- panic attractor GONE" if panic == 0 else ""
    print(f"  schema {schema:.2f}: panic basin {panic:>4.0%} "
          + "#" * round(panic * 20) + gone)
```

Output:

```
PHASE PORTRAIT — Noa.arousal x Noa.perceived_threat (2 attractors):
  c: (20.0, 5.0) [calm] holding 36% of the plane
  p: (95.0, 90.0) [panic] holding 64% of the plane
  basins (Noa.arousal →, Noa.perceived_threat ↑; c=calm, p=panic):
    100.0 |ppppp|
     75.0 |ppppp|
     50.0 |cccpp|
     25.0 |cccpp|
      0.0 |cccpp|
          -----
  the healthy basin holds 36% of the plane — a psyche is a set of attractors, and a disorder is one of them.

REAPPRAISAL -- raise the bar at which the body is read as danger:
  schema 0.85: panic basin  64% #############
  schema 0.60: panic basin  64% #############
  schema 0.40: panic basin  52% ##########
  schema 0.20: panic basin   0%   <- panic attractor GONE
```


At a high arousal schema (0.85) the psyche has **two** attractors: a calm state
holding 36% of the plane and a **panic** state holding 64%. A person like this
isn't "anxious" as a level — they have a large basin of their own state space
that drains into a self-sustaining attack. The **reappraisal** sweep is the
therapeutic prediction: as the schema falls (raising the bar at which the body
is read as danger), the panic basin shrinks — 64%, 64%, 52% — and at 0.2 the
**panic attractor is gone entirely**. Therapy, in this model, is a
*bifurcation*: not talking someone out of a feeling, but changing the landscape
until the bad attractor ceases to exist.

### 2.7 The network — a person as a system of symptoms (0.18)

The panic model in 2.6 already coupled a few appraisals into a feedback loop.
Cramer and colleagues push that idea to its limit: a disorder as a *network* of
symptoms that activate each other — poor sleep drives fatigue drives low mood,
and so on — with no central "depression" variable at all. The disorder is an
emergent property of the wiring, and vulnerability is **connectivity**: the same
stress on a more tightly-wired network tips where a loosely-wired one shrugs.


```python
from soma.narrative import depression_network, stress_response, hysteresis_loop

# 0.18: a person AS a network of symptoms that feed each other (Cramer et al.).
# Vulnerability is CONNECTIVITY -- the same stress, a different wiring strength.
for label, conn in (("resilient", 0.45), ("vulnerable", 1.40)):
    net = depression_network(name=label, connectivity=conn)
    print(stress_response(net, levels=(0, 1, 2, 2.5, 3)).render())
    print()

# and once tipped, does lifting the stress lift the person? Sweep it back down.
print("does removing the stress lift the depression?")
for label, conn in (("vulnerable", 1.4), ("severe", 3.2)):
    print(hysteresis_loop(depression_network(name=label, connectivity=conn)).render())
    print()
```

Output:

```
STRESS RESPONSE — resilient (connectivity 0.45):
    stress    0: ············ 0 symptoms
    stress    1: ············ 0 symptoms
    stress    2: ············ 0 symptoms
    stress  2.5: ············ 0 symptoms
    stress    3: ████████████ 9 symptoms  <- tips
  tips into depression at stress ≥ 3

STRESS RESPONSE — vulnerable (connectivity 1.4):
    stress    0: ············ 0 symptoms
    stress    1: ············ 0 symptoms
    stress    2: ████········ 3 symptoms
    stress  2.5: █████████··· 7 symptoms  <- tips
    stress    3: ████████████ 9 symptoms
  tips into depression at stress ≥ 2.5

does removing the stress lift the depression?
HYSTERESIS — vulnerable (connectivity 1.4):
    stress   up sweep            down sweep
        4    █████████ 9
        3    █████████ 9 <-triggers  █████████ 9
        2    █········ 1             ██████··· 6
        1    ········· 0             ········· 0 <-releases
        0    ········· 0             ········· 0
  triggers at 3.0, releases at 1 — the depression outlives its cause by 2
  hysteretic: lifting the stress below its trigger is not enough — it
  releases only at 1. The depression outlives its cause.

HYSTERESIS — severe (connectivity 3.2):
    stress   up sweep            down sweep
        4    █████████ 9
        3    █████████ 9             █████████ 9
        2    ███████·· 7 <-triggers  █████████ 9
        1    ········· 0             ███████·· 7
        0    ········· 0             █████···· 5
  triggers at 2.0, never releases in range — the depression outlives its cause by ∞
  spontaneous non-recovery: removing the stressor does NOT lift the depression — the network holds itself down.
```


The **resilient** network (connectivity 0.45) absorbs stress up to 2.5 and only
tips at 3; the **vulnerable** one (1.4) already carries three active symptoms at
stress 2 and tips at 2.5. But the deeper prediction is what happens when the
stress *lifts*. Both networks are **hysteretic** — the depression outlives its
cause, releasing only well below the stress that triggered it (the vulnerable
one triggers at 3 but doesn't release until 1). And at **severe** connectivity
(3.2) the loop never opens: the down-sweep still shows five active symptoms at
*zero* stress. That is **spontaneous non-recovery** — the network holds itself
down with no help from the world, the model's account of why a depression can
persist long after the loss that started it is gone.

### 2.8 The inverse problem — recovering the wiring from a diary (0.19)

Every layer so far ran *forward*: author a structure, generate behaviour. The
clinic faces the *inverse* problem: given a person's behaviour, recover their
structure. Two patients report the same nine symptoms — same diagnosis, same
checklist. `simulate_diary` generates each person's daily self-reports, and
`estimate_network` fits a person-specific network (a lag-1 vector
autoregression) from that diary *alone* — recovering, for each, a different
hub and therefore a different treatment target.


```python
from soma.narrative import (symptom_network, DEPRESSION_SYMPTOMS,
                            simulate_diary, compare_hubs)

# 0.19: the INVERSE problem. Ana and Bo report the same nine symptoms. Simulate
# each person's daily diary, then estimate their PERSONAL network from the diary
# alone (a lag-1 vector-autoregression), and recover different treatment targets.
S = DEPRESSION_SYMPTOMS
ANA = [("insomnia","fatigue"), ("fatigue","mood"), ("mood","interest"),
       ("mood","worthless"), ("mood","concentration"), ("interest","mood"),
       ("worthless","mood"), ("mood","appetite"), ("mood","suicidal"),
       ("concentration","mood"), ("fatigue","concentration")]   # mood-centred
BO  = [("insomnia","fatigue"), ("insomnia","concentration"),
       ("insomnia","mood"), ("insomnia","interest"),
       ("fatigue","concentration"), ("fatigue","psychomotor"),
       ("fatigue","interest"), ("insomnia","appetite"),
       ("mood","worthless"), ("worthless","suicidal"), ("fatigue","mood")]  # sleep-driven

for name, edges, thr in (("Ana", ANA, None), ("Bo", BO, {"insomnia": 1.5})):
    net = symptom_network(name, S, edges, connectivity=1.0, thresholds=thr or {})
    diary = simulate_diary(net, days=250, seed=5)
    r = compare_hubs(diary)
    mark = "OK" if r["correct"] else "MISS"
    print(f"{name}: recovered hub = '{r['recovered_hub']}' "
          f"(true '{r['true_hub']}') {mark}  -> treat {r['recovered_hub']}")
print()
print("Same checklist, different wiring, different target -- from the diary alone.")
```

Output:

```
Ana: recovered hub = 'mood' (true 'mood') OK  -> treat mood
Bo: recovered hub = 'insomnia' (true 'insomnia') OK  -> treat insomnia

Same checklist, different wiring, different target -- from the diary alone.
```


Ana's diary recovers **mood** as the hub; Bo's recovers **insomnia** — both
correct (`OK`), and both recovered from nothing but the day-to-day fluctuations
of their symptoms. Same DSM label, same symptom list, but the *dynamics* betray
different architectures, and the model recommends treating a different symptom
in each. This is what person-specific modelling buys the clinic: the average
patient does not exist, and a diary is enough to tell two of them apart.

### 2.9 Choice — the space of a character's decisions (0.20)

The layers up to here predict what a character *feels* or *becomes*. This one
predicts what they *do* at a fork. Under active inference, a decision balances
two things a chooser wants at once: getting close to what they *prefer*
(pragmatic value) and *learning* something (epistemic value). A single dial,
**curiosity**, trades exploration against exploitation — and curiosity turns out
to be derivable from the same temperament dials as feeling.


```python
from soma.narrative import (Option, decide, explore_exploit, curiosity_of,
                            Story, guarded, stoic, anxious, tender)

# 0.20: choice under active inference. Choiceworthiness = how close an option
# lands to what you prefer (pragmatic) + curiosity x how much you'd learn
# (epistemic). One dial -- curiosity -- trades exploration against exploitation.
safe  = Option("the known road",   reward=6, uncertainty=0.6)
risky = Option("the unknown road", reward=5, uncertainty=3.5)   # pays LESS
print(explore_exploit(safe, risky, preference=8,
                      curiosities=(0, 0.3, 1, 3)).render())
print()

# and curiosity is a TEMPERAMENT: derived from the same dials as feeling.
stay  = Option("stay",  reward=8,   uncertainty=0.5)
leave = Option("leave", reward=5.5, uncertainty=2.5)
print("the same fork, four temperaments (curiosity derived, not authored):")
for t in (guarded, stoic, anxious, tender):
    s = Story("t", span="4s", step="1s", about="acute distress")
    c = s.character("C", temperament=t)
    d = decide(c, [stay, leave], preference=8, decisiveness=2.5, sigma_pref=1.5)
    print(f"  {t.name:<9} (curiosity {curiosity_of(c):>4.2f}): "
          f"P(leave) {d.p('leave'):>4.0%} -> {d.choice}")
```

Output:

```
EXPLORE/EXPLOIT — chooser: the safe bet 'the known road' vs the uncertain 'the unknown road'
    curiosity  0.0: P(the unknown road) ██████ 30%
    curiosity  0.3: P(the unknown road) █████████████ 63%
    curiosity  1.0: P(the unknown road) ████████████████████ 98%
    curiosity  3.0: P(the unknown road) ████████████████████ 100%
  crosses to exploring at curiosity ≈ 0.3

the same fork, four temperaments (curiosity derived, not authored):
  guarded   (curiosity 0.63): P(leave)  19% -> stay
  stoic     (curiosity 0.98): P(leave)  42% -> stay
  anxious   (curiosity 1.07): P(leave)  49% -> stay
  tender    (curiosity 4.25): P(leave) 100% -> leave
```


The first study holds two options fixed — a safe known road and an uncertain one
that actually *pays less* — and sweeps curiosity. At curiosity 0 the character
takes the safe road (30% chance of the unknown); by curiosity 1 they almost
always explore (98%), crossing over near 0.3. A pure reward-maximizer would never
touch the worse-paying road; the epistemic term explains why a real person
would.

The second study is the integration. **Curiosity is not authored; it is
derived** from each temperament's precision and conviction. The guarded person
(curiosity 0.63) stays; the tender person (4.25) leaves. The same two dials that
governed belief-update speed back in Part 1 now govern how a person chooses at a
fork, without a single new number being set by hand.

### 2.10 The other mind — recursion depth as a trait (0.21)

Social choice is harder than solo choice: the value of my move depends on what
you will do, which depends on what you think I will do. That regress — *I think
that you think that I think* — is **recursive theory of mind**, and its depth is
a character trait. A 0-level mind tracks what you *do*; a k-level mind simulates
you at every shallower depth and learns which you are. The library runs these
minds against each other.


```python
from soma.narrative import tournament, play, detect_depth

# 0.21: recursion depth ("I think that you think...") as a character trait
# (Devaine & Daunizeau's k-ToM). Competition rewards it; over-attributing it
# is a rout; and depth can be READ from moves alone.
t = tournament((0, 1, 2), rounds=40, reps=12)
print(t.render())
print()
strict = play(2, 0, infer_level=False, rounds=40, reps=12)
infer  = play(2, 0, infer_level=True,  rounds=40, reps=12)
print(f"over-mentalizing a NAIVE opponent: a strict 2-ToM earns "
      f"{strict.score_a:.2f},\nthe level-INFERRING 2-ToM earns {infer.score_a:.2f} "
      "-- seeing a simple person\nas a schemer hands them your pattern.")
print()
m = play(0, 1, rounds=120, reps=1, seed=4)
print(detect_depth(m.history, seat=1, candidates=(0, 1, 2)).render())
```

Output:

```
TOURNAMENT — hide_and_seek (cell = seat-0 payoff/round; 0.50 = even; ▲ seat-0 out-thinks, ▽ is out-thought)
            k=0   k=1   k=2
  seat0 k=0: 0.50   0.36▽  0.40▽
  seat0 k=1: 0.64▲  0.50   0.36▽
  seat0 k=2: 0.64▲  0.64▲  0.49
  (the ▲s live below the diagonal: one level of depth is one level of edge)

over-mentalizing a NAIVE opponent: a strict 2-ToM earns 0.06,
the level-INFERRING 2-ToM earns 0.64 -- seeing a simple person
as a schemer hands them your pattern.

DEPTH READING — whose mind fits the moves?
    0-ToM: logL =  -109.18
    1-ToM: logL =   -58.00   <- best account of their moves
    2-ToM: logL =   -64.20
```


The **tournament** shows the ladder: on the diagonal (equal depth) it is a
coin-flip, but a deeper seeker beats a shallower hider (0.64 vs the naive) and
vice-versa — every level of recursion converts into winnings. The
**over-mentalizing** result is the cautionary one: a *strict* 2-level mind that
insists its naive opponent is a schemer earns a catastrophic 0.06, because its
countermoves to an imagined scheme are themselves a pattern the simple opponent
reads. The level-*inferring* mind, which learns it faces someone naive, earns
0.64. Finally, **depth reading** inverts the problem (as in 2.8, but for minds):
from a move sequence alone, the best-fitting depth is recovered — here the true
1-level hider is correctly read as 1-ToM.

### 2.11 The tell — decisiveness is legibility, and the layers close (0.22)

The final instrument closes the loop between all the others. It asks: what makes
a mind *readable*? The answer is **decisiveness** — the sharper a mind converts
its model into action, the crisper (and so more legible) its pattern is to a
deeper mind. And decisiveness derives from **conviction**, the very dial that
armors a character's beliefs against evidence. So the conviction that protects
the interior *betrays the surface*.


```python
from soma.narrative import legibility, face_off, social_params_of
from soma.narrative import guarded, stoic, anxious, tender

# 0.22 closes the loop: the more decisively a mind acts on its model, the more
# legible its pattern is to a deeper mind -- and decisiveness derives from
# CONVICTION, the same dial that armors a character's beliefs. So the guarded
# are read. One trait, both fates.
print(legibility(betas=(2, 5, 12), rounds=40, reps=12).render())
print()
print("a 2-ToM reader vs 1-ToM hiders of each temperament")
print("(alpha, beta derived from precision and conviction):")
for t in (guarded, stoic, anxious, tender):
    m = face_off(stoic, t, k_a=2, k_b=1, rounds=40, reps=12)
    a, b = social_params_of(t)
    print(f"  {t.name:<9} (alpha={a}, beta={b:>4}): loses {m.score_a:.2f}")
print()
print("Conviction protects the interior and betrays the surface.")
```

Output:

```
THE TELL — a 2-ToM reader vs a 1-ToM of varying decisiveness
    their decisiveness β= 2.0: the deeper mind takes █████████████ 0.53
    their decisiveness β= 5.0: the deeper mind takes ███████████████ 0.64
    their decisiveness β=12.0: the deeper mind takes ██████████████████ 0.73

a 2-ToM reader vs 1-ToM hiders of each temperament
(alpha, beta derived from precision and conviction):
  guarded   (alpha=0.235, beta= 6.8): loses 0.71
  stoic     (alpha=0.28, beta= 6.5): loses 0.73
  anxious   (alpha=0.265, beta= 6.2): loses 0.71
  tender    (alpha=0.364, beta= 3.2): loses 0.61

Conviction protects the interior and betrays the surface.
```


The first study holds a deep reader fixed and sweeps the shallower mind's own
decisiveness (β): at β=2 it nearly escapes (loses 0.53), at β=12 it is read like
a book (0.73). The second study ties the layers together. Deriving each mind's
parameters from its temperament — α from precision, β from conviction, the same
dials as everywhere else — a 2-level reader takes **0.71–0.73** from the
high-conviction temperaments (guarded, stoic, anxious) and only **0.61** from
the loose-gripped tender one. The person hardest to change from the inside is
the easiest to read from the outside. The same conviction did both jobs, and no
one authored the second: it fell out of the first. That is the sense in which
these instruments describe one character and not eleven.

---

### 2.12 Legitimacy — the belief that holds the holder (0.25)

The instruments so far predict what a character feels, chooses, and reveals.
This one predicts something harder: why a character *defends the very thing that
injures them*. It is the psychology of system justification — Jost and Banaji's
observation that people, including the disadvantaged, are motivated to see the
social order they live under as fair, because the belief itself does work: it
quiets anxiety (Jost and Hunyady's *palliative function*), at a cost to
self-regard for those it disadvantages (Jost and Thompson), while dampening the
outrage that would move them to act (Wakslak and colleagues). Three contextual
antecedents raise the motive — how much you **depend** on the system, how
**inescapable** it is, and how **threatened** it is (Friesen and colleagues) —
and the strongest single lever is inescapability: Laurin, Shepherd and Kay
showed that making a system harder to leave makes people defend it *more*.

The layer's move is that the conviction is not authored. You give a character
their context, and `justifies` **derives** how hard they hold the belief from
the three antecedents — and derives, inversely, how much they let the evidence
of harm count at all (motivated ignorance). Everything downstream follows.

```python
from soma.narrative import Story, guarded, stoic
from soma.narrative import justifies, palliative_tradeoff, antecedent_dose

# 0.25 -- SYSTEM JUSTIFICATION: why the people a system injures defend it. A
# legitimizing belief's conviction is DERIVED from three antecedents
# (dependence, inescapability, threat); while it holds, injury buys quiet at
# the price of self-worth. Nobody authors the conviction -- the context does.

# Neva, a pillar-diver's widow: dependent on the system, and it is the only
# world there is. She nails the lord's condolence-feather over her door.
def widow():
    s = Story("the_feather", span="16s", step="1s", about="acute distress")
    neva = s.character("Neva", temperament=guarded)
    justifies(neva, "perch", dependence=0.9, inescapability=0.9)
    return s

print(palliative_tradeoff(widow, "Neva", harm=6.0).render())
print()

# The exodus curve: hold everything fixed but the thinkability of leaving.
def drifter(inescapability):
    s = Story("the_quarter", span="16s", step="1s", about="acute distress")
    d = s.character("Drifter", temperament=stoic)
    justifies(d, "perch", dependence=0.85, inescapability=inescapability)
    return s

print(antecedent_dose(drifter, "Drifter", levels=(0.95, 0.5, 0.1)).render())
```

Output:

```
THE TRADE — Neva, the same injury, with and without the belief:
  anxiety  with belief  █████···············  25.2
           without      █████████████████···  86.1
  worth    with belief  ██████··············  31.1
           without      ████████████········  60.0
  the belief buys 60.9 points of quiet and charges 28.9 points of worth.
  'Let me have the luck' is not a delusion; it is a priced purchase.

THE EXODUS CURVE — Drifter: tipping point of the belief as inescapability falls
                        conviction                breaking harm  0        9
  inescapability 0.95  0.824 ████████████··  |·······▲··| breaks at harm >= 7
  inescapability 0.50  0.671 █████████·····  |····▲·····| breaks at harm >= 4
  inescapability 0.10  0.535 ███████·······  |···▲······| breaks at harm >= 3
  An exit is not a destination. It is a solvent.
```

**What the output means.** The first study *prices* the belief. Neva, a
pillar-diver's widow, is maximally dependent on the perch-lords' order and has
nowhere to go; her derived conviction is high. Staged against the same injury
with and without that belief, the model shows the trade in two channels at once:
with the belief her anxiety sits at **25** against **86** without it — the belief
buys about **61 points of quiet** — but her self-worth sits at **31** against
**60** — it *charges* about **29 points of worth**. That is the palliative
function and its price, both real, neither a delusion. (Read the two rows as two
women: Neva, who nails the feather over her door, and the narrator's mother, who
*would never look at it* — the same widowing, one belief apart.)

The second study is the novel's engine, and the theory's sharpest claim. It
holds dependence and the injuries fixed and moves only **inescapability**. At
0.95 — no way out — the belief holds against harm all the way to 7, more than
the system ordinarily deals, so in practice it never breaks. Lower it to 0.10 —
an exit becomes thinkable — and the *same* injuries, now at a harm of 3, are
enough to break it. Nobody's suffering changed. What changed is what the
suffering was allowed to mean. Laurin, Shepherd and Kay, run in reverse: an exit
is not a destination, it is a solvent. (The companion instrument `conscientize`
doses the same lever the other way — each session of Freire-style dialogue
lowers *felt* inescapability, and the tipping point falls with it.)

This is the layer at its most characterizing: it takes the one thing that most
resists a psychological account — a person's loyalty to what harms them — and
makes it fall out of their circumstances rather than their character. Change the
circumstances and the loyalty changes, on a curve you can read.

---

## How the instruments relate

Every instrument in Part 2 reads a different prediction off the *same* small
machine introduced in Part 1 — a character as a set of arbitration dials
(precision, conviction, learn) wired to senses and appraisals:

- **Signature, self-guides, density** (2.1–2.3) predict one person's responses
  across situations — the profile, the emotion-family, the distribution.
- **Landscape and ensemble** (2.4–2.5) predict the *space* of a relationship's
  trajectories and which dial the ending pivots on.
- **Intrapersonal landscape** (2.6) predicts a single psyche's multiple stable
  states, and reappraisal as a bifurcation.
- **Network and inverse problem** (2.7–2.8) make a person emergent from a
  symptom network, then recover that network from behaviour alone.
- **Choice, the other mind, the tell** (2.9–2.11) predict decisions, social
  play against other minds, and readability. These layers add new parameters —
  curiosity, decisiveness — but derive them from the *same* precision and
  conviction that drove the feeling layers, so the character stays one coherent
  object rather than a stack of unrelated models.
- **Legitimacy** (2.12) predicts why a character defends what injures them, and
  derives the conviction behind that defense from their circumstances —
  dependence, inescapability, threat — so that loyalty to a harmful system
  becomes a curve you can move rather than a fixed trait.

The through-line is the definition we began with. Each instrument stakes a claim
about what a described person will do in a situation you have not yet shown them,
and each claim is one you can check: run the code and it either holds or it does
not. That is the whole difference between a character you have described and a
character you can predict.

---

## Running these yourself

Every snippet above runs unmodified in the SOMA playground's **Library** mode
(`soma_playground.html`), or from Python once the `soma` package is importable:

```python
# each block is self-contained; paste and run
from soma.narrative import Story, tender    # ... etc.
```

In the playground you can also save a character as a `.soma` file and drive it
from library code on the same page (`run_file("my_character.soma")`), and read
the SOMA any library character compiles to with `print(story.source())` — the
bridge between the convenient high-level description and the transparent
machine underneath.
