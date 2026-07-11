# From modelling characters to predicting them

*The ask was pointed: engineer the library to make **positive predictions**, not
just mathematically model characters. This note records what the science says the
difference is, and the three capabilities added to close it — all implemented and
tested (162 passing).*

---

## 1. The distinction, as cognitive science draws it

A recurring theme in computational cognitive science is the line between a model
that **fits/replays** its inputs and one that **predicts**:

- **Simulation vs. prediction.** *"The Importance of Falsification in Computational
  Cognitive Modeling"* (Trends in Cognitive Sciences) separates **model
  simulations** — which reproduce data using best-fit parameters — from **model
  predictions**, and argues that a model's ability to *generate the effect of
  interest* under conditions it was not fit to is an **absolute falsification
  criterion**. A theory earns its keep by predicting the not-yet-observed.
- **Descriptive vs. predictive modelling.** Descriptive models *fit* the data and
  risk over-fitting; predictive models use **fewer free parameters**, **generalize
  to unseen conditions**, and come with **out-of-sample** error estimates. The move
  is: *specify less, derive more, and be tested on inputs you did not author.*
- **Depth, on the reader's side, is prediction.** Writers report that a character
  becomes autonomous exactly when they can *"automatically predict the character's
  responses to situations"* (Watkins & Fernyhough and related work on characters'
  voices), and craft advice insists a character's actions must be *"an inevitable
  consequence of their nature"* — predictable in retrospect. A deep character *is*
  a predictive model in the reader's head; suspense and surprise are prediction
  error (Wilmot's *Great Expectations*; fMRI of suspense and predictive inference).

SOMA up to v0.6 was, by this standard, a **simulator**: you specified a wound, a
lie, a need, a conviction, and an evidence schedule, and it computed the arc. True
to life, but it mostly gave back what it was given. v0.7 adds three ways for the
library to make claims that are *not* in the specification.

---

## 2. The mechanism that licenses prediction: schema therapy × predictive coding

The bridge is a literature that unifies **Young's schema therapy** with
**predictive processing** (e.g. *"Early maladaptive schemas from child
maltreatment … a predictive coding framework"*, PMC12069367). Its causal chain:

    unmet core need  ->  early maladaptive schema (a core self-belief)
                     ->  coping style (surrender / avoidance / overcompensation)
                     ->  a characteristic lie, want, and behaviour

and its mechanism is *already* SOMA's: schemas persist through **"an attention/memory
bias away from schema-incongruent information that generates prediction errors"**
(the lie loop suppressing disconfirming evidence), and therapy works by **"diminishing
prediction errors"** until the schema revises (SOMA's `overwhelm`/self-revelation).
That correspondence is what lets the library *predict* the belief a wound will
produce, rather than needing to be told.

---

## 3. Three capabilities

### (a) Predict the lie from the wound — `predict_lie`, `adopts`

A schema knowledge base (`soma/narrative/schema.py`) encodes the wound→schema→coping
map for five core needs (worth, belonging, safety, connection, autonomy). Given an
unmet need and a coping style, it forecasts the **claim, feeling, want, whom it
harms, the behaviour to expect, and the dynamics** (how hard it is held, how much
disconfirming evidence the coping lets in — which sets whether and when it can
break).

The load-bearing prediction is that **the same wound, coped three ways, is three
different people**:

| coping | predicted lie (unmet need: worth) | harms |
|--------|-----------------------------------|-------|
| surrender | "I am the one who can be done without." | self |
| avoidance | "If I never test it, no one can find me wanting." | self |
| overcompensation | "If I am not ranked above them, I am the surplus again." | others |

`Character.adopts("worth", "overcompensation", disconfirmed_by=...)` installs the
predicted lie and its need. Run against the novel's own cast, the overcompensation
branch reproduces **Blade's** lie word-for-word (so `build_derived()` rebuilds his
tragic arc from the wound alone), while the surrender and avoidance branches predict
the *unwritten* brothers he might have been. Structure derived, not asserted.

### (b) Forecast an unscripted response — `predict`

`story.predict(who, {channel: value})` runs the character's own model on a situation
**not in the timeline** (every authored stimulus is stripped; the character faces
only the probe), and reports what their arbitration does with it — *suppress* it,
*take it in*, or *break* — restricted to the loops that actually read that channel.
This is the counterfactual a novelist runs (*"what would she do if…"*), made
falsifiable: the model must produce the effect.

It **discriminates** the cast on input none of them was scripted to meet:

- Blade, faced with full equal regard (9): **suppresses** it — the lie holds.
- Ink, shown he is kept for nothing (9): **breaks** — a self-revelation.
- The Coat, given an act that is his own (9): **breaks**.

Telling a breakable character apart from an unbreakable one on unseen input is
generalization — the mark of a predictive, not merely descriptive, model.

### (c) Predict the threshold — `tipping_point`

`story.tipping_point(who, channel)` sweeps evidence strength and returns the **least
sustained evidence that turns the lie** — a sharp, quantitative, falsifiable claim:

| character | channel | prediction |
|-----------|---------|------------|
| Ink | kept_for_nothing | breaks once evidence ≥ 3 |
| Coat | his_own_act | breaks once evidence ≥ 3 |
| Selm | the_margin | breaks once evidence ≥ 6 (held hardest) |
| Blade | equal_regard | **never**, in [0, 9] — the lie is kept |

None of these numbers is written anywhere; each falls out of the conviction dial
via the automatic breaking rule, and any of them could be shown wrong by running
the model. Blade's *"never"* is the strongest falsification target of all.

---

## 4. What this changes

SOMA can now (1) **derive** a character's belief-structure from a minimal wound +
coping (fewer inputs, more output), (2) **forecast** behaviour in situations the
author never wrote, and (3) state **quantitative, falsifiable** thresholds. Those
are the three things the cognitive-science literature names when it distinguishes a
predictive model from a descriptive one. The `predictions` view collects them for
the novel's cast:

```bash
python3 examples/narrative/the_unmooring.py predictions
python3 examples/narrative/the_unmooring.py derived --character   # Blade, lie derived
```

The novel itself is untouched: as in every prior pass, the instrument is what
improved, and — now that it can *predict* the cast rather than only replay them — it
goes on validating the finished book rather than turning up edits in it.

*Version: SOMA 0.7.0. Tests: 162 passing. Tutorial gains §5.6 on prediction.*
