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

## 5. The 0.8 layers: engineering for positive prediction

The philosophy of science is specific about what separates a prediction from an
accommodation (Popper's risky forecasts; Lipton on fudging; Hitchcock & Sober on
overfitting; the preregistration literature that operationalized all three): the
claim must be staked **before** the run, on input **not used** to build the model,
be **sharp enough to fail**, and any hand-tuning toward the desired outcome must be
**disclosed**. Version 0.8 turns those four requirements into library mechanics,
and adds three more independently-grounded psychological theories whose mappings —
like the schema-therapy engine of §2 — pay for their inputs with forecasts the
author never typed:

**Appraisal → emotion** (`soma.narrative.appraisal`). Scherer's Component Process
Model, Smith & Ellsworth's dimensions, Roseman, and the OCC model converge on one
claim: a pattern of appraisal predicts a discrete emotion. `appraises_event()`
takes only the pattern — goal-congruence, agency, certainty, coping potential,
norm-compatibility — and *derives* the feeling and its Frijda action tendency.
Other-blame with power forecasts anger; the same loss without power, resentment;
certain uncontrollable loss, grief; a good outcome still uncertain, hope. The
emotion term never appears in the author's input, and the compiled story must then
produce it in the Chronicle, or the model is wrong.

**Attachment → separation behaviour** (`soma.narrative.attachment`).
`attaches("avoidant")` installs Mikulincer & Shaver's deactivating policy as a
parameter bundle and stakes a forecast that `predict_separation()` then tests
against a separation the author never scripted: secure settles on reunion; anxious
protests and stays braced (the alarm re-arms above rest); disorganized wants and
fears the same figure; and avoidant produces the sharpest claim in the library —
**narrated calm over a real somatic spike**, Ainsworth's A-pattern and Diamond et
al.'s repressive coping, measurable here because SOMA keeps the narrator's account
and the body's record as separate instruments. Four styles, one probe, four
distinguishable signatures — that is what makes the typology predictive rather
than decorative.

**Circumplex → the space between** (`soma.narrative.circumplex`). The
complementarity principle (Kiesler; Sadler & Woody; contemporary integrative
interpersonal theory) is the first layer to predict a *dyad* rather than a skull:
warmth invites warmth (robust), dominance invites its reciprocal (weaker,
context-moderated — and the forecast says so). `stance()` + `meet()` compile two
characters into mutually-read manner surfaces through the couple/lag machinery;
`predict_dyad()` forecasts from the two stances alone whether the exchange settles
or strains, that hostile correspondence sustains itself (structurally
complementary, affectively corrosive), and **who gives ground** — the self held
with lower conviction drifts further from its opening manner, because
susceptibility to the pull is `(1 − conviction)`, the same dial as every prior in
the language.

**Preregistration** (`soma.narrative.preregister`). `story.preregister()` seals
claims — `expect_feeling`, `expect_gap`, `expect_break`/`expect_no_break`,
`expect_mood`, `expect_peak` — *before* the story runs; `check()` runs it once and
returns CONFIRMED/FALSIFIED per claim with Chronicle evidence. Adding a claim
after checking raises: that is the line between prediction and postdiction,
enforced. The report also discloses **accommodations** — every place a
theory-derived default was overridden by hand (`adopts(conviction=…)`,
`attaches(style, arousal_to=…)`) — because a run that matches a hand-set dial
describes; it does not predict. And the standing caveat holds everywhere: every
verdict is a claim about a *model* of a character, never a measurement of a
person.

```bash
python3 examples/narrative/four_ways_of_leaving.py    # the 0.8 layers, end to end
```

## 6. The 0.9 study layer: insight into the predictions themselves

Making a prediction and understanding it are different acts. The 0.9 layer adds
four instruments that operate ON predictive characterizations — each ported from
a methodology whose business is extracting insight from models, and each checked
against actual runs rather than asserted:

**Sensitivity** (`soma.narrative.sensitivity`, `story.sensitivity()`).
Variance-based Sobol indices over any dials the perturb grammar can reach: the
first-order index is the outcome variance a dial explains alone, the total index
adds its interactions. The gap between them is the insight — a trait vs. a
contingency. Validation from inside: given only runs of a breaking lie, the study
recovers that conviction and precision act through interaction, which is SOMA's
own auto-break threshold `6·conviction/precision` — a ratio the study found blind.

**Discrimination** (`soma.narrative.discriminate`, `story.discriminate()`).
Adaptive-design-optimization for characters: given two readings of the same
person (two parameterizations that fit everything written so far), find the probe
under which their outcomes diverge most — the scene to write. Divergence 1.0 is
qualitative: one reading breaks, the other never does. The instrument routinely
finds that the *weak* dose discriminates best (at full strength every reading
breaks — a ceiling effect), and that "never breaks" splits into two different
people: armored forever, or open enough to revise without shattering.

**Early warning** (`soma.narrative.earlywarning`, `story.predict_break_onset()`).
The critical-transitions toolkit pointed at self-revelations. The interpreter now
logs each defended belief's overwhelm-debt and its bound; the instrument reads
only the PRE-transition stretch, extrapolates the debt's slope against the bound,
and issues a quantitative forecast — "crossing predicted at ≈11s" against an
actual break at 10s — plus the classical detrended-fluctuation indicators (rising
variance, rising lag-1 autocorrelation), each labeled with the confidence the
literature supports. A debt climbing too slowly to reach its bound before the
horizon is forecast stable: approach is not arrival.

**Counterfactual** (`soma.narrative.counterfactual`,
`story.minimal_intervention()`). The interventionist question: the smallest
single-dial change, measured from the character as written and normalized to each
dial's range, that flips a target outcome. The minimal sufficient change is what
the ending actually turned on; when no dial in range flips it, that is reported
as over-determination — a finding, not a failure.

All four stand on one substrate (`soma.narrative.insight`): `run_with(story,
overrides)` — compile once, mutate dials through the perturb grammar, interpret —
and a shared outcome vocabulary (`break`, `break_time`, `peak`, `gap`,
`mood_drift`, `feel`, `perceive_frac`, …). The substrate is the API; the
instruments are its most common compositions, and the example studies compose new
ones inline — `the_marriage_that_could_have_held.py` computes a point of no
return (the latest year one extraordinary day still routes to `perceive`) in a
dozen lines of substrate calls, and finds it agrees with the route-flip year the
plain run shows.

```bash
python3 examples/narrative/the_anatomy_of_a_breaking.py      # all six studies, one man
python3 examples/narrative/the_marriage_that_could_have_held.py
```

*Version: SOMA 0.9.0. Tests: 221 passing. New: insight substrate, sensitivity,
discrimination, early warning, counterfactual; `perceive_frac` outcome; the
interpreter logs overwhelm debt and bound.*
