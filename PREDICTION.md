# From modelling characters to predicting them

*The ask was pointed: engineer the library to make **positive predictions**, not
just mathematically model characters. This note records what the science says the
difference is, and the capabilities added to close it — all implemented and
tested. Per-section version footers below record the state at each release.*

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

## 7. The 0.10 protocols: the canonical experiments, run whole

The most complex predictive character simulations in the literature are not
models but PROTOCOLS — standardized situations with staked, coded, falsifiable
predictions. Version 0.10 implements the two most consequential:

**The Strange Situation** (`soma.narrative.strange_situation`). Ainsworth's
eight episodes — play, a stranger, two separations, two reunions — compiled onto
the attachment machinery, with the four interactive scales (proximity seeking,
contact maintaining, avoidance, resistance) coded from the two reunion windows
the way an observer codes the tape: from behavior alone. The attachment styles
gained two theory-staked expressive parameters (`seeks_contact` — deactivation
is precisely the inhibition of the proximity bid; `resists_soothing` — protest
continuing INTO contact, Ainsworth's C signature), and the reunion wiring is
identical for every child, so pattern differences are generated, not scripted.
The instrument's central claim is then testable as PARAMETER RECOVERY:
`validate_instrument()` installs each style, runs the protocol, classifies
blind — and recovers all four. A hand-built child with no style label
classifies honestly from tape, which is what the instrument is for.

**The Gottman-Murray marriage model** (`soma.narrative.gottman`). The most
famous predictive character simulation there is, rebuilt from SOMA's own parts:
influence functions are couple/lag readings; the NEGATIVE THRESHOLD (lower in
divorcing couples) is a guard level; emotional inertia is conviction; repair is
an interoceptive bid (my own distress climbing triggers a warm reach through
the relationship — which is why stonewalling reads on the heart record). The
five couple types are staked as parameter bundles; `assess()` runs one
contentious conversation (the grievance arrives on its own channel, through one
partner) and checks each type's forecast: the regulated types hold, the hostile
types cascade, negative-affect reciprocity separates them 96% to 0%, and the
THIN SLICE — the first quarter of the conversation alone — calls every ending,
with the mechanism visible: the slice carries the couple's thresholds, and the
thresholds are the ending.

And a third canonical simulation composed from nothing but existing verbs and
the insight substrate — **Clark's panic spiral** (`examples/narrative/
the_spiral.py`): one appraisal that reads the heart and drives the heart. From
that single circle fall four predictions, each checked by sweep: the
all-or-nothing tipping flutter (two attractors, not a dial), HYSTERESIS (the
attack outlives its trigger and yields only to a down-driver the spiral cannot
supply — Cramer & Borsboom's path-out-longer-than-path-in), and a computable
exposure margin: the tolerance that prevents the attack is exactly the
trigger's peak, a quantitative, per-person therapy target.

```bash
python3 examples/narrative/the_strange_situation.py
python3 examples/narrative/five_marriages.py
python3 examples/narrative/the_spiral.py
```

## 8. The 0.11 learning layer: prediction error, run as learning

SOMA's loop is a prediction-error engine — its settle event's `error` term is
literally a prediction error — so the two most quantitatively validated
predictive models of learning fall straight out of it, each staked with the
signature prediction a simpler account cannot make.

**Reward prediction error / conditioning** (`soma.narrative.conditioning`,
`story.conditions()` + `story.predict_conditioning()`). A value loop whose
belief IS the value estimate and whose error IS the RPE. Acquisition climbs;
the RPE is largest at the first unpredicted reward and falls toward zero as the
reward becomes predicted (Schultz's dopamine signature); extinction lowers the
value. The honest complication the literature insists on: plain Rescorla-Wagner
treats extinction as unlearning, but animals show SPONTANEOUS RECOVERY, proving
extinction is new learning over an intact trace, not erasure. So each
association gets two traces — a slow acquired value and a fast context
correction that decays back during rest — and recovery becomes a prediction the
single-trace model cannot make. Reacquisition then shows savings (a running
start from the trace that was never erased).

**Reformulated learned helplessness** (`soma.narrative.helplessness`,
`story.learns_control()` + `story.predict_helplessness()` +
`triadic_design()`). The classic triadic design built from SOMA: controllability
is mechanized as whether an escape action's efference actually cancels the
aversive signal, and the subject learns a control-belief. The reformulation's
three dimensions enter as the SCOPE of that belief: a GLOBAL style is one
control-belief shared across every situation, a SPECIFIC style keeps a separate
belief per situation. From that single design choice falls the full,
theory-exact pattern — deficit only after uncontrollable pretreatment
(controllable and none immunize), and the transfer asymmetry that is the
reformulation's sharpest claim: global style carries the helplessness into a
dissimilar task, specific style confines it to similar ones (Abramson, Seligman
& Teasdale 1978; Alloy et al. 1984).

```bash
python3 examples/narrative/what_the_body_learns.py   # both, end to end
```

## 9. The 0.12 decision layer: how long a choice takes, and how often it errs

Every layer so far predicts what a character feels or becomes. This one predicts
something orthogonal, and in the lab more precisely measured than any of them:
the TIME a decision takes and the RATE at which it is wrong. The drift-diffusion
model (Ratcliff 1978; Ratcliff & McKoon 2008; Gold & Shadlen) is the dominant
account of speeded two-choice decisions — a noisy accumulation of evidence to a
boundary — and it makes DISTRIBUTIONAL predictions no deterministic or
single-number model can: right-skewed reaction-time distributions, error
responses shaped differently from correct ones, and the speed-accuracy tradeoff
traced from one dial.

`soma.narrative.decision` (`story.decides()`, `story.predict_decision()`,
`story.speed_accuracy()`) gives a character a decision temperament from the four
DDM parameters — drift (evidence quality), boundary (the caution / speed-accuracy
dial), start bias (prior lean), non-decision time — or a named style (impulsive,
deliberate, keen, muddled, prejudiced). Each style makes a checkable claim: the
deliberate juror is slow and accurate where the impulsive one is fast and
error-prone (same drift, opposite boundary — caution, not ability); the keen one
is fast AND accurate (high drift, the one combination caution can't buy); and the
prejudiced one shows the biased-start signature — fast correct responses but SLOW
errors, the fingerprint of a mind that leaned before it looked, which a symmetric
model cannot produce. `speed_accuracy()` traces the DDM's most famous prediction:
sweeping the boundary alone yields a monotone accuracy-up, RT-up tradeoff,
dissociating caution from acuity.

This is also where SOMA gains a faculty it lacked by design: STOCHASTICITY. The
base interpreter is deterministic, and every earlier layer relies on that, so the
noise lives entirely in a seeded per-trial driver — the same seed reproduces the
same RT distribution, and the deterministic core is provably untouched (a
regression test confirms an ordinary belief story still runs identically).

```bash
python3 examples/narrative/twelve_seconds_in_a_jury_room.py
```

## 10. The 0.13 pass: sharpening the results, and a fixed confabulation bug

This release strengthens simulations whose results were thinner than the rest,
and fixes a real bug the strengthening exposed.

**Appraisal gains construct validity.** The forward map (appraisal → emotion)
is only a genuine prediction if it is IDENTIFIABLE — if the inverse (emotion →
appraisal) recovers the same emotion for every one in the vocabulary.
`check_identifiability()` confirms all 14 emotions round-trip, the same
blind-recovery standard the Strange Situation meets; `recover_appraisal()` and
`explain_emotion()` run the map backward, from an observed feeling to the reading
of the world behind it and its Frijda action tendency.

**Three descriptive portraits became predictive simulations.** `the_negotiator`,
`two_sisters`, and `the_diplomat` — rich characters previously used only for a
static portrait — gained `--predict` modes with staked, checked forecasts: the
tipping pressure at which each breakable value becomes a lie, preregistered
accounts of the feelings that are felt-but-never-known (the exile's terror, the
diplomat's defended longing, one sister's resentment behind a composed face), and
an honest early-warning analysis showing the negotiator's breach is a SHARP
threshold transition whose driver — not whose face — is the readable warning.

**A confabulation-gap bug, found and fixed.** `expect_gap` matched narrate
events by the `<Name>.` loop prefix, but the interpreter logs narration under the
narrator's name `self_<Name>` — so every multi-character gap prediction was
silently falsified. Now fixed and regression-tested; two_sisters' preregistered
"resentment behind grace" claim confirms as it always should have.

*Version: SOMA 0.13.0. Tests: 265 passing. New: appraisal identifiability +
inverse inference; --predict modes for negotiator / two_sisters / diplomat; fix
for multi-character confabulation-gap matching.*

## 11. The 0.14.1 audit: correctness, honesty, and a new diagnostic

A systematic pass for errors, inaccuracies, inconsistencies, and undone work,
fixing what it found:

**A checker gap that swallowed typos.** A loop whose `sense:` named a channel
that didn't exist used to fire never and report nothing — the story simply came
out empty, the single most confusing failure mode in the language. The checker
now validates every loop's sense against the declared channels (plus stimulus
targets and coupled channels) and raises a clear `SomaTypeError` naming the
likely typo, exactly as it already did for clock names.

**Sobol indices could exceed 1.** The Jansen total-order estimator can overshoot
on interaction-heavy outcomes with small samples; the sensitivity report now
clamps total-order to its definitional range [0, 1], so a dial can no longer be
reported as writing 170% of an outcome's variance.

**The DDM hid heavy censoring.** When a weak drift or wide boundary left most
walks undecided within the time limit, accuracy was computed on the decided
minority with no warning. The decision report now flags when ≥5% of trials fail
to reach a bound, so a 75%-accuracy figure over 12 of 500 trials can't mislead.
`speed_accuracy` also had its temporary-state swap made exception-safe.

**A missing valence.** `belonging` — the relief-feeling of a met "to-matter"
need — was absent from the interpreter's valence table and so defaulted to
negative, miscoloring mood. It is now correctly positive.

**Docstrings that oversold their mechanism.** The learned-helplessness module
claimed controllability was mechanized through motor "efference reafference" and
an "escape action" that the code does not contain; the conditioning module
claimed its dual trace was "two ordinary SOMA loops" when one trace lives in a
thin Python driver. Both now describe honestly what they actually do — faithful
abstractions, not simulations of machinery that isn't there.

**A leaked stack frame.** The browser library-mode error banner included the
bridge's own `exec(compile(...))` frame in user tracebacks; it now shows only
the user's own frames.

Stale test counts across the docs were corrected to the current total.

*Version: SOMA 0.14.1. Tests: 280 passing. Fixes: sense-channel checker
validation, Sobol index clamping, DDM censoring disclosure + exception-safe
sweep, `belonging` valence, honest helplessness/conditioning docstrings,
clean library-mode tracebacks.*

## 12. The 0.14.2 audit: public API, docstrings, and stale counts

A second consistency pass, after the tutorial reorder:

**`__all__` was badly incomplete.** The package exported only 18 names — the
original authoring surface — while the whole prediction and insight layer
(`predict_feeling`, `strange_situation`, `gottman_assess`, `predict_decision`,
`sensitivity`, `minimal_intervention`, and two dozen more) was reachable by
direct import but absent from `__all__`, so `from soma.narrative import *` did
not bring it in and tools reading `__all__` saw a fraction of the real API. It
now lists all 65 public names, and a test locks it in so it cannot silently rot
again as new layers are added.

**A docstring taught a method that does not exist.** `arc.py` showed
`story.at_arc(mira.face_events(...))`; the real API is `story.over(arc, fn)`. The
example is corrected and runs.

**Stale test count in the README.** Two lines still said 276 after the count had
grown to 280; both fixed.

Everything else checked clean: all 28 SOMA and 14 library examples run and (where
applicable) type-check; every library example is deterministic across reruns; no
Python warnings are raised anywhere in the prediction or insight paths under
`-W error`; there are no TODO/FIXME/NotImplementedError markers or stray debug
prints; and all 14 tutorial code blocks still reproduce their printed output
through the exact browser execution path.

*Version: SOMA 0.14.2. Tests: 281 passing. Fixes: complete `__all__` (+ a
guard test), corrected `arc` docstring, README test counts.*
