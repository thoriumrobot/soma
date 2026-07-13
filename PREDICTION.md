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

## 13. 0.14.3 — the capstone studies, bundled

Eight full command-line programs from `examples/narrative/` — each a complete
study composing several prediction and insight tools on one character, couple,
or small group — are now bundled into the playground's Library rail and taught
in `TUTORIAL_PREDICTIVE.md` as a new Part 5. They were already in the repo and
already correct; what changed is that they're now reachable without a
terminal, and each has a full explanation of what its composition reveals that
no single tool would show alone: every insight tool turned on one man (`the
anatomy of a breaking`), a computed point of no return in a marriage's slow
curdling, panic modeled as a positive-feedback loop with genuine hysteresis (a
mechanism this tutorial had not shown elsewhere), and a jury's accuracy
staying flat under a deadline while its *coverage* of hard cases collapses.

**A quoting bug, found while bundling.** Embedding a capstone's raw source
(which itself contains nested docstrings and f-string escape sequences like
`\n`) inside the manifest's own triple-quoted Python string literal is
syntactically valid at every layer but silently wrong at runtime: the *outer*
string literal interprets escape sequences meant for the *inner*, not-yet-
executed code, corrupting it before it ever reaches the browser. The fix is to
declare the manifest's code arguments as raw strings (`r"""..."""`). A new
test (`TestLibraryManifest`) now runs every bundled example end-to-end and
checks the capstones produce substantial output, specifically to catch this
class of bug — syntactically valid, semantically wrong, and invisible without
execution — should it recur.

*Version: SOMA 0.14.3. Tests: 283 passing. New: 8 capstone studies bundled
into the Library rail and the tutorial; manifest execution guard tests.*

---

## 0.15 — Predictive characterization: the profile, the guide, the distribution

The prediction layer so far forecasts single outcomes: a lie's breaking point, a
feeling from an appraisal, a decision's speed. Personality science's own answer
to "what would predict a *person*" converges on three structures that are none
of them a single number, and 0.15 adds one module for each. They share the new
`Story.probe(who, stimulus, beats)` — the raw substrate under `predict`
(scripted timeline stripped, one unseen input, full `Result` back) — so every
study rests on one definition of "facing an unseen situation."

### (d) The if...then behavioral signature — `soma.narrative.signature`

Mischel & Shoda's CAPS (Psychological Review, 1995) resolved the
person–situation debate by relocating personality from average traits to a
**stable profile of situation→behavior contingencies**. The decisive evidence
(Shoda, Mischel & Wright, 1994 — the Wediko camp study) is that people with
indistinguishable average scores have wildly different, highly stable if...then
profiles: the *profile* is the fingerprint, and cross-situation variability is
the trait's structure, not noise around it. A SOMA character already *is* what
CAPS says a person is — a stable network of cognitive-affective units a
situation activates differentially — so `signature(story, who, battery)`
extracts the profile the network implies, one `Story.predict` probe per
situation, none of them authored. `similarity(a, b)` scores two profiles over a
shared battery; `mean_level()` exposes the trait-score view of the same runs so
a study can assert both halves of the Wediko result (equal averages, crossed
profiles — `examples/narrative/the_same_on_average.py` stages it); and
`diagnostic_situation(story, a, b, battery)` names the single probe that
maximally separates two characters — the scene an author should stage to make
the difference visible. Falsifiable twice: the profile must reproduce on re-run
(CAPS's core stability claim — a test asserts similarity 1.0), and any staged
cell must appear in the Chronicle.

### (e) Which suffering — `soma.narrative.selfguides`

Higgins' Self-Discrepancy Theory (Psychological Review, 1987): the self has
three domains — actual, **ideal** (aspirations), **ought** (obligations) — and
the *emotion family* a shortfall produces is decided by which guide it violates.
Actual-below-ideal is the absence of a hoped-for positive → the **dejection**
family (despair; shame when the ideal is held from another's standpoint);
actual-below-ought is the presence of a threatened negative → the **agitation**
family (guilt; fear when the duty is another's to enforce). `ideal(char,
domain)` / `ought(char, domain)` install a guide as what SOMA already believes a
standard is — a loop whose *prior is the guide*, sensing the actual-self
channel — and the emitted quale is **derived from (guide, standpoint), never
typed by the author**. `contrast(story, a, b)` stages the theory's signature
experiment: the *same* failure, presented to two characters whose guides differ
only in kind, must deject one and agitate the other in the Chronicle, or the
encoding is wrong. Honesty note, inherited from the replication literature: the
emotion-*specificity* claim is the contested part (ought→agitation is the
cleaner unique link; several studies find both gaps predicting depressed
affect — Tangney et al. 1998; Boldero & Francis 2005), so the module predicts
the family as the primary claim and the quale as an overridable default —
schema.py's stance exactly. Higgins' surviving practical translation,
Regulatory Focus Theory (1997), is exposed as `regulatory_focus(char)`:
ideal-dominant → promotion (eager; `boundary_bias` < 1 for the decision layer),
ought-dominant → prevention (vigilant; > 1) — a disposition `speed_accuracy`
can consume.

### (f) The distribution is the person — `soma.narrative.density`

Fleeson's experience-sampling result (JPSP 2001; Whole Trait Theory, Fleeson &
Jayawickreme 2015): within-person variability is enormous; the **mean** of a
person's distribution of states is almost perfectly stable (that mean is the
classical trait score); and the **variability and skew are themselves stable
individual differences**, with the amount of within-person variability
reflecting **reactivity to trait-relevant situational cues**. A trait is the
whole density distribution of states. `density(story, who, probe_channel)`
samples the distribution the model implies — `samples` randomized unseen
situations through `Story.probe`, one state read per run (`"arousal"`: peak
elevation of a body channel; `"defense"`: fraction of firing settles routed
`act`) — and reports mean, sd, skew, range, histogram, and `reactivity` (the
cue-strength/state correlation). `compare(a, b)` looks for the Fleeson
contrast: *same mean, different width* — two people identical as trait scores
and different as people, with the reactive one wider. Tests assert the
distribution's parameters reproduce under a fresh seed (stability of the
density — the finding itself) and that the engineered reactive character is the
wide one.

*Version: SOMA 0.15.0. Tests: 296 passing. New: `Story.probe`;
`signature`/`similarity`/`diagnostic_situation`; `selfguides`
(`ideal`/`ought`/`contrast`/`regulatory_focus`); `density`/`compare`;
`examples/narrative/the_same_on_average.py`; 13 characterization tests.*

---

## 0.16 — The landscape and the ensemble: predictions about the *space* of trajectories

Every prediction so far concerns one trajectory: a threshold, a feeling, a
break. The deepest questions a novelist asks about a relationship — *could
this marriage have held? was this ending fated or flipped? what is the
smallest change that would put a good ending within reach?* — are questions
about the **space** of trajectories, and two literatures answer them formally.
0.16 adds one module for each.

### (g) The phase portrait — `soma.narrative.phase`

Gottman & Murray's *The Mathematics of Marriage* (2002) predicted divorce from
a **phase portrait**: fit each partner's uninfluenced steady state, emotional
inertia, and influence function from minutes of conversation; the plane of
(his affect, her affect) then partitions into **basins of attraction** around
stable steady states, separated by unstable ones, and where a conversation
ends is decided by which basin it starts in. The couples headed for divorce
were those whose landscape had **lost its positive attractor**, and the formal
content of therapy is a change to the landscape. Holling's and Scheffer's
resilience work completes the picture: **resilience is the size of the
basin**, readable as recovery from perturbation.

The module is two-layered, and honest about which is which.
`phase_portrait(story)` is **empirical**: sweep a grid of opening manners, run
the actual coupled SOMA characters from each (scripted stimuli stripped),
cluster the endpoints → attractors; map opening → endpoint → basins; render
the plane. The staked findings reproduce Gottman's typology as properties of
the plane: a validating couple's landscape has one warm attractor holding the
whole plane; a hostile couple's landscape **contains no good ending at all**;
and a brittle couple is **bistable** — warm and cold basins, two
pursue–withdraw states, a separatrix — so which marriage they have is decided
by where the evening starts. `fit_influence(portrait)` is **Gottman's own move
performed on the simulation**: regress, from the portrait's trajectories, each
partner's next manner on their own last (inertia, uninfluenced state) and
their partner's last, trying *both* of the book's influence forms — bilinear
(two slopes) and **ojive** (two plateaus past thresholds), with the ojive
thresholds themselves fitted (Gottman's negativity-threshold estimation, which
matters because the couple's gain shifts where the partner's shown manner
crosses the guard) — keeping whichever fits better per partner, and
`validate()` requires the fitted map's own attractors to reproduce the
empirical ones **bidirectionally** (so a degenerate quasi-fixed fit cannot
pass by accident). `resilience(story)` gives Holling's two readings of one
quantity — the warm basin's share of the plane, and a kick probe measuring the
basin's radius and recovery times. And `second_stable_state(story, dials,
values)` is **therapy as bifurcation**: sweep a dial (or several in lockstep)
and find where a warm basin comes into *existence* — a stronger object than a
counterfactual ending, since it asserts the presence or absence of a region of
openings from which the marriage holds.

### (h) Ensemble futures — `soma.narrative.futures`

A counterfactual asks what one change turns *this* ending; ensemble
forecasting (the settled practice of weather and climate prediction) asks the
deeper question: across the cloud of **nearby worlds** — the same people, each
dial drawn from its plausible range through the perturb grammar — what is the
**distribution over endings**? `futures(story, dials, classify)` returns
P(each ending), the modal fate, and normalized **entropy**: 0 is destiny, 1 is
a coin, and the difference between a fate that holds in 95% of nearby worlds
and one that holds in 55% is invisible to any single run. `pivotal(report)`
names the dial that decides the fate as a standardized effect size (Cohen's d
between the dial's values in modal-ending worlds and the rest). For Soren's
marriage the ensemble finds a contested fate (curdles in ~2/3 of worlds,
entropy ≈ 0.9) whose hinge is the learning rate (d ≈ +3.2) while trust in her
face barely moves the odds (d ≈ +0.1) — the sensitivity study's conclusion,
recovered as probability. `dose_response(factory, doses, ...)` is the
probabilistic deepening of "the smallest change that would have saved it":
P(target ending) as a function of an intervention's dose, with
`minimal_dose` the least dose clearing a probability floor and `classify_at`
allowing dose-relative endings. Two honest findings fall out for the
marriage: the extraordinary day's **intensity is not a dose at all**
(precision arbitration is magnitude-blind — past the hardening, no loudness
of world reaches him), and the true dose is **timing**: the original "last
good year" becomes a curve, near-certain at year 4, contested in the middle
years, zero by year 12.

`examples/narrative/the_shape_of_a_marriage.py` runs all seven studies;
`tests/test_landscape_layers.py` stakes each claim.

*Version: SOMA 0.16.0. Tests: 312 passing. New: `phase`
(`phase_portrait`/`fit_influence`/`resilience`/`second_stable_state`);
`futures` (`futures`/`pivotal`/`dose_response`/`by_outcome`/`by_break`);
`examples/narrative/the_shape_of_a_marriage.py`; 16 landscape tests.*

---

## 0.17 — The intrapersonal landscape: a disorder as an attractor, a poet as a cycle

The most elaborated formal character simulations in the literature are
intrapersonal: a *person* as a system of interlocking feedback loops whose
stable configurations — not whose momentary levels — are the phenomena. Two
were implemented end-to-end, and staging them forced improvements at every
layer of the stack, core language included.

### The simulations — `examples/narrative/the_vicious_cycle.py`

**Panic** (Robinaugh et al., *A Computational Model of Panic Disorder*,
2019/2024). The theory's engine is a vicious cycle — bodily arousal is read as
evidence of catastrophe (the **arousal schema**), perceived threat drives
arousal higher, and at high schema the loop runs away into an attack — with
escape behavior as the dampening arc and a homeostatic ceiling bounding it. In
SOMA this is three appraisals wired mouth-to-tail; the schema is the
misinterpretation guard. Six studies, each producing a claim the machine had
to generate: (I) the same stressor pulse is shrugged off at low schema and
ignites a self-sustaining attack at high schema; (II) the **state portrait**
of arousal × perceived threat shows two attractors — calm and panic — and the
panic basin's share of the plane (64% at schema 0.85) *is* the person's
vulnerability, drawn as a region; (III) **hysteresis**: the stressor that
triggers the attack (level 5) never releases it — loop width ∞, the clinical
fact that you cannot reassure someone out of a panic at the level that started
it; (IV) **burnout**: with a finite metabolic budget the runaway attack
terminates *itself* — exhaustion, not insight, ends it; (V) **reappraisal as
bifurcation**: sweeping the schema shrinks the panic basin until the attractor
ceases to exist (gone at 0.2), while the safety-behavior row shows why escape
is so powerfully reinforced — it abolishes the acute attack — with the honest
note that its maintenance cost (blocked schema disconfirmation) is a slow arc
this study does not model; (VI) the ensemble over 40 nearby days finds
P(attack)=72% with the **schema** (d≈+2.3) separating attack-days from calm
ones far more than the day's severity (d≈+0.5): this person's panic is carried
in how they read their body, not in how hard the world pushes.

**The poet** (Rinaldi, *Laura and Petrarch: An Intriguing Case of Cyclical
Love Dynamics*, SIAM J. Appl. Math 1998 — the model whose limit cycle
reproduced Petrarch's twenty-year emotional cycle, independently confirmed by
Jones' dating of the Canzoniere). A relaxation oscillator in two appraisals:
ardour feeds inspiration (fast), inspiration crashes ardour (the poem written,
the longing spent), and the crucial tuning is that ardour *rests above the
rapture line*, so every recovery re-crosses the trigger. Nudged once, the poet
oscillates forever; the state portrait detects a single **cyclic attractor**
holding 100% of the plane, swing ±29, period ≈ 8 beats — the steady state *is*
the oscillation, and it is error-gated: at perfect rest nothing fires, one
sight of Laura starts twenty years.

### What implementing them changed in the stack

**Core language.** (1) *Chained comparisons*: `3 < x < 7` now has Python
semantics — `(3<x) and (x<7)` — instead of folding left; band guards
("flattered by moderate ardour, antagonized by excess") are now expressible.
(2) *The affine commitment, enforced at the act*: a failed `spend` halts the
remainder of that loop's act block for the frame — an action the body cannot
fund does not happen. Previously insolvency only logged; now "the body cannot
conjure" has teeth, and it is what lets a panic burn out. All prior tests pass
unchanged.

**Narrative layer.** `appraises(..., spend_first=True)` orders the budget
spend *before* the drive, so insolvency starves a self-amplifying loop's push
on the body (Robinaugh's homeostatic ceiling as an affine resource rather than
a subtracted term).

**Phase layer.** (1) `state_portrait(story, who, (ch_a, ch_b))` — the phase
portrait of a *single psyche*: two channels of one character, swept from a
grid of initial states, with per-portrait axis ranges, healthy-pole
declaration (`healthy_is="low"|"high"|None`), and subject-aware rendering.
(2) **Cyclic attractors**: `Attractor` now carries `kind`
(`"fixed"|"cycle"`), `amplitude`, and `period`; tail-motion analysis
distinguishes a settled trajectory from a sustained oscillation, so a limit
cycle is one attractor with a swing, not a smear of false fixed points.
(3) `hysteresis(story, who, stimulus, response)` — sweep a stimulus up and
back down in one continuous run and compare the trigger with the release; the
instrument extends the probe's duration to fit its own sweep, and `bistable`
requires the loop width to exceed the sweep's own resolution, so quantization
cannot masquerade as a trap.

A mechanism note discovered en route and used deliberately: loops settle in
declaration order within a frame, so *where a safety loop is declared* decides
whether it intercepts the alarm before the alarm feeds back to the body —
order as reflex latency. And one emergent nicety: a loop that cuts its own
sensed channel erases its own emit guard before the emit re-checks, so the
safety behavior never registers in the feeling record — habitual and unfelt,
which is exactly what safety behaviors are.

*Version: SOMA 0.17.0. Tests: 324 passing. New: chained-comparison guards;
affine act-halting; `spend_first`; `state_portrait`; `hysteresis`; cyclic
attractors; `examples/narrative/the_vicious_cycle.py`; 12 intrapersonal
tests.*

---

## 0.18 — The network: a person as a system of symptoms, and the slow arc

Every character before this one was assembled from loops an author wired by
hand. `soma.narrative.network` builds a character whose behaviour is
**emergent**: a network of symptoms, each activating its neighbours, whose
collective dynamics — two stable states, a catastrophe between them, a memory,
a slow worsening over a life — no single node contains. This is the network
theory of mental disorders made runnable (Cramer, van Borkulo, Giltay, van der
Maas, Kendler, Scheffer & Borsboom, *Major Depression as a Complex Dynamic
System*, PLoS ONE 2016), extended with Post's kindling hypothesis (1992) for
the slow arc the panic study named and could not yet model.

### The model, faithfully

Nine DSM symptoms are directly connected (insomnia → fatigue → poor
concentration → loss of interest → low mood → worthlessness → …). Each
symptom's activation relaxes toward a **logistic** function of its active
neighbours, the external stress, and its own threshold —
`s_i → sigmoid(C · Σ w_ij s_j + stress − θ_i)` — which compiles to N neural
`flow`s, one per symptom. The load-bearing parameter is **connectivity** C: not
a symptom, not stress, but the *strength of the coupling*.

### The simulation — `examples/narrative/the_weight.py`

Five studies, each a generated prediction: (I) **vulnerability is
connectivity** — the same stress tips a strongly-connected person into
depression at a lower level than a weakly-connected one, differing in no
symptom and no stressor, only in the wiring (`tipping_stress`: vulnerable tips
around 2.5, resilient around 3.0); (II) **spontaneous non-recovery** —
`hysteresis_loop` ramps stress up and back down in one run: the resilient
network's symptoms clear when the stress does, but the vulnerable network's
depression *outlives its cause* (removing the stressor leaves it holding itself
down — worthlessness feeds low mood feeds poor sleep, a cycle that no longer
needs the world); (III) **well or depressed, rarely between** —
`equilibrium_modes` samples across the transition band and finds the strongly
connected person settles at an extreme far more often (depressed-share climbs
from ~23% to ~62% with connectivity, same stress distribution — the cusp
catastrophe's bimodality, with a genuine forbidden zone at intermediate
symptom counts); (IV) **kindling** — `kindling` runs a life-course in which
each episode permanently lowers the threshold for the next, so the stressor
required falls with every episode until, around episode 7, the illness becomes
**autonomous** and recurs with no stressor at all (Post's endpoint: the first
heartbreak takes a divorce, the tenth a rainy Tuesday); (V) **what to treat** —
`target_symptom` disables each symptom in turn and finds that the
most-connected node (`mood`, in-degree 4) most collapses the rest, network
theory's practical claim that treatment should target the hub, not the loudest
symptom.

### What implementing it changed in the stack

The network layer is compiled from ordinary SOMA `flow`s, so it needed no new
core primitive — evidence that the 0.17 dynamics substrate was the right shape.
One robustness fix surfaced: kindling drives thresholds negative, and a naive
`stress - θ` renders `- -0.4` (two tokens the lexer rejects), so `source()` now
renders a negative threshold as `+ |θ|`. The module reuses the phase layer's
duration helper and the same parse/perturb/interpret path as `insight.run_with`,
so a network's connectivity and thresholds are perturbable dials like any
other, and every study is falsifiable in the repository's usual sense (the
equilibria are deterministic given a start; re-running reproduces the curves).

*Version: SOMA 0.18.0. Tests: 339 passing. New: `network` (`symptom_network`/
`depression_network`/`stress_response`/`hysteresis_loop`/`equilibrium_modes`/
`kindling`/`target_symptom`); negative-threshold source safety;
`examples/narrative/the_weight.py`; 15 network tests.*

---

## 0.19 — The inverse problem: recovering a person's wiring from their diary

Every layer to here runs the model FORWARD: given a character, predict what
they do. `soma.narrative.idiographic` runs it BACKWARD, which is the deepest
predictive-characterization object in the library and the frontier of clinical
network science (Bringmann, *Person-specific networks in psychopathology: past,
present, and future*, Curr Opin Psychol 2021; Epskamp, van Borkulo et al.,
*Personalized Network Modeling in Psychopathology*, Clinical Psychological
Science 2018). Given a time-series of one person's symptoms — an
experience-sampling diary — it estimates the network of couplings that
generated it, so a character's structure is **recovered rather than authored**.

### The loop, closed and checked

`simulate_diary(net)` drives a `SymptomNetwork` with a fluctuating daily
stressor and logs each symptom over ~200 days — an ESM diary, except the
ground-truth wiring is known. `estimate_network(diary)` fits the field's
standard model, a lag-1 **vector autoregression** (each symptom's next value
regressed on all symptoms' current values, ridge-regularized), whose
coefficient matrix `A[target][source]` *is* the person-specific temporal
network. `out_strength` centrality names the hub. And because the truth is
known here (it never is in a clinic), `recovery(diary)` scores the estimate
against it — the falsification a simulator can perform and a clinic cannot.

### The simulation — `examples/narrative/the_diary.py`

Five studies: (I & II) an authored patient lives 220 days, is observed only
through their diary, and their hub is recovered from it alone — `mood`,
correct, at ~55–64% edge recall (edges noisy, hub robust, exactly the field's
reliability finding); (III) **two patients, same nine symptoms, different
wiring** — Ana's depression organized around low mood, Bo's around insomnia —
whose diaries run through the same estimator yield *different correct hubs* and
therefore different treatment targets, which a symptom checklist could never
distinguish (the clinical case for person-specific networks: the average
patient does not exist); (IV) **the identifiability floor**, staked rather than
hidden — a hub can only be recovered if it *varies*; Bo's insomnia is
recoverable when it fluctuates and invisible when held constant, because a
cause that never moves leaves no trace in the record it causes (`Diary.variances`
and `Diary.estimable` expose this); (V) **closing the loop** — the recovered
network is rebuilt into a runnable character (`rebuild_network`) and simulated
forward, and the re-derived patient's stress response matches the original's:
author → live → observe → estimate → re-run, the full circle.

### What implementing it changed in the stack

The inverse problem needed no new core primitive — it reads the per-symptom
time-series the `flow`-compiled network already logs — which is further
evidence the 0.17 dynamics substrate was the right shape. Two additions to the
network layer proved necessary and generally useful: `SymptomNetwork.out_degree`
(the *dynamic* hub — how much a symptom drives the rest — as distinct from
`degree`'s in-degree, and the correct ground truth for a temporal-VAR
out-strength estimate), and the honest diagnostics `Diary.variances` /
`Diary.estimable` that make the identifiability floor a first-class,
inspectable fact rather than a silent failure. A subtlety discovered en route
and documented: raw VAR coefficients favour high-variance *receivers* over
low-variance *drivers* as hubs, so a purely upstream root cause is hard to
recover unless it varies — matching the reliability caveats in Epskamp,
Borsboom & Kruis, *Estimating psychopathological networks: be careful what you
wish for* (2017), and reproduced here as a staked limit rather than papered
over.

*Version: SOMA 0.19.0. Tests: 351 passing. New: `idiographic` (`simulate_diary`/
`estimate_network`/`recovery`/`rebuild_network`/`compare_hubs`);
`SymptomNetwork.out_degree`; `Diary.variances`/`estimable`;
`examples/narrative/the_diary.py`; 12 idiographic tests.*

---

## 0.20 — Choice: the space of a character's decisions under active inference

Every layer to here predicts what a character FEELS or BECOMES or was WIRED to
be. `soma.narrative.choice` predicts what they DO at a fork -- and does it with
the one account of choice that captures a deep thing about people: that they
want two incompatible things at once, to get what they prefer AND to find out
what they don't yet know. Under active inference (Friston, FitzGerald, Rigoli,
Schwartenbeck, O'Doherty & Pezzulo, *Active inference and learning*, 2016;
Friston et al., *Active inference and epistemic value*, 2015) an agent selects
the policy that minimizes **expected free energy**, which decomposes into
exactly two terms:

    choiceworthiness  =  pragmatic value  (closeness to what I prefer)
                      +  curiosity × epistemic value  (how much I'd learn)

so a chooser is never a pure reward-maximizer nor a pure novelty-seeker but
both, traded off by a single coefficient the literature ties to
precision/dopamine — confident agents exploit, uncertain agents explore.

### What this activated

The dormant machinery finally lifted: `epistemic_value`, `pragmatic_value` and
`sigmoid` have shipped in `soma.mathlib` (ported from ilion's
`activeinference.ili`) since the first commit, callable inside any SOMA
expression but never surfaced to the narrative layer. `choice` is that lift,
and it needed one substantive correction to the physics: the raw
`epistemic_value` log-ratio is invariant to absolute uncertainty, so
`Option.posterior_uncertainty` now does proper Gaussian belief-updating against
a fixed observation-noise floor — a vague option collapses further when chosen
and therefore genuinely offers more information than a sharp one, which is what
makes exploration meaningfully different from exploitation.

### The simulation — `examples/narrative/the_fork.py`

Four studies: (I) **explore or exploit** — the same fork (a safe known bet vs
an uncertain, information-rich one believed to pay *less*) put to choosers of
rising curiosity, who cross from taking the sure thing to gambling on the
unknown at a curiosity that is theirs alone — the exploration/exploitation
dilemma dissolved into one dial; (II) **preference is a target, not a ceiling**
— active inference's humane correction to reward maximization: pragmatic value
is *closeness* to preference, so the modest character who wants 7 has their
appetite peak at 7 and *fall* toward 10, declining an overshoot a
reward-maximizer cannot even represent; (III) **the choice is in the
temperament** — `curiosity_of` derives the trait from the same arbitration
dials that drive a character's feelings (openness = sensory precision × loose
priors), so the guarded, convinced temperaments hold the known road and the
open, trusting one leaves, with no choice authored; (IV) **the space of a
life's forks** — one character mapped across forks of rising stakes and rising
uncertainty, a 2-D surface of where they hold and where they leap (high stakes
+ low mystery is where even a curious person holds), which is not one prediction
but the whole shape of a person's daring before any fork arrives.

### Why it fits the arc

The layers now span a full account of a person: predict their responses (0.15),
map their trajectory space (0.16–0.17), make them emergent from a network
(0.18), infer that network from behaviour (0.19), and now predict their choices
(0.20) — with the load-bearing point that the *same two temperament dials*
(trust in the senses, grip on beliefs) that produce a character's feelings also
produce how they choose, which is what it means for a character to be whole
rather than a bag of independent modules.

*Version: SOMA 0.20.0. Tests: 364 passing. New: `choice` (`Option`/`decide`/
`expected_free_energy`/`explore_exploit`/`temptation`/`curiosity_of`),
activating the dormant `soma.mathlib` active-inference builtins;
`Option.posterior_uncertainty` Gaussian belief-update; `examples/narrative/the_fork.py`;
13 choice tests.*

---

## 0.21 — The other mind: recursive theory of mind and the depth of a character

Every fork in 0.20 had fixed outcomes. The social fork does not: the value of
my move depends on what you will do, and what you will do depends on what you
believe about me. `soma.narrative.mentalizing` implements that regress — "I
think that you think that I think..." — as the recursive theory-of-mind
(k-ToM) framework of Devaine, Hollard & Daunizeau (*The Social Bayesian
Brain*, PLoS Comput Biol 2014; *Theory of Mind: Did Evolution Fool Us?*, PLoS
ONE 2014; cf. Camerer's cognitive hierarchy and the tomsup package). A 0-ToM
mind attributes no mind at all: it tracks what the other tends to DO and
best-responds. A k-ToM mind attributes one: it holds simulations of the other
at every lower depth, learns from their moves WHICH it is facing, and
best-responds to the mixture — mentalizing as literally running a smaller
model of the other person and inverting it from behaviour. This is SOMA's
oldest metaphysical commitment made computational: other minds arrive only as
surfaces, as moves, and a k-ToM mind is what
modelling-an-interior-from-surfaces IS.

### Design decisions the results forced

Two failures of the naive implementation became features. **Strict level-k is
kept as a mode** (`infer_level=False`): a mind that insists its opponent is
exactly one level below it is catastrophically wrong about a naive one
(earning 0.22 where the level-inferring mind earns 0.55) — the paranoia cost,
worth staging rather than hiding. **The hypothesis set includes a coin**:
without a "there is no mind here, only a bias" hypothesis, a 1-ToM *loses* to
a biased coin (≈0.49 vs the naive tracker's 0.66), attributing strategy to
habit; with it, mentalizers exploit the bias (0.60–0.66). Knowing when NOT to
attribute a mind is part of having one. And `detect_depth` carries an Occam
penalty because deeper minds nest shallower ones — raw likelihood can never
prefer the shallower truth.

### The simulation — `examples/narrative/the_other_mind.py`

Five studies: (I) **the ladder** — in competitive hide-and-seek the deeper
mind exploits the shallower at every rung (one-step advantage 0.54–0.58,
diagonal at chance); (II) **the arms race and the handshake** — the same minds
in a coordination game gain from the FIRST level of mentalizing (0.74→0.80)
and then saturate: depth 2 and 3 add nothing, because once both are trying to
meet there is no one left to outwit — the asymmetry behind Devaine's
conclusion that rivalry, not friendship, would have paid for the evolution of
deep recursion; (III) **the cost of over-mentalizing** — the strict 2-ToM's
countermoves to an imagined scheme are themselves systematic, and the naive
hider's plain frequency-tracking routs it 0.78 to 0.22; (IV) **the coin** —
against pure noise every depth earns chance (sophistication needs structure to
bite), and against a mindless bias the coin hypothesis is what saves the
mentalizer; (V) **reading depth from moves** — the inverse problem for minds:
an opponent's recursion depth inferred from their move sequence alone, correct
for depths 0 and 1, and *wrong in a lawful way* for depth 2 against a naive
opponent: the 2-ToM never needs its second level there, behaves as a 1-ToM,
and is read as one, while against a 1-ToM its depth is exercised and becomes
visible. The same identifiability law 0.19 found for symptom hubs (a hub must
vary to be seen), now for minds: a character's sophistication is a fact about
them, but its visibility is a fact about their circumstances.

### Why it fits the arc

0.19 read a person's hidden wiring from their diary; 0.21 reads a mind's
hidden depth from its moves — and both find the same law, that hidden
structure is only legible where the world exercises it. And where 0.20 made a
character's choices fall out of the same temperament dials as their feelings,
0.21 makes their *social* choices fall out of a single new trait — recursion
depth — whose payoff profile (an edge in rivalry, worthless past level one in
friendship, a liability when over-applied to the simple) is itself a
characterization: what kind of company a mind is built for.

*(Figures in this section were measured at the 0.21 defaults, β=3; 0.22
re-baselines the library to β=5 and restates them.)*

*Version: SOMA 0.21.0. Tests: 380 passing. New: `mentalizing` (`Mind`/
`RandomMind`/`play`/`tournament`/`depth_advantage`/`detect_depth`,
hide-and-seek + coordination games, coin hypothesis, strict vs level-inferring
modes, Occam-penalized depth reading);
`examples/narrative/the_other_mind.py`; 16 mentalizing tests.*

---

## 0.22 — The tell: decisiveness is legibility, and the layers close into one character

This release began as an audit — find the simulations whose results
under-deliver, and improve them — and the audit itself produced the release's
discovery. The 0.21 competitive ladder was real but modest (one-step
advantages of 0.54–0.55). Sweeping the softmax decisiveness β to strengthen it
revealed that the advantage is not a constant of the game but a function of the
*shallower* mind's own β: at β=2 the shallow mind nearly escapes the deeper one
(0.51); at β=12 it hands over 0.73, monotonically. **Decisiveness is
legibility**: a mind that converts its model into action crisply presents a
crisp — readable — pattern to a mind one level deeper. Wavering is armor;
conviction is a tell. The new `legibility` instrument stages the sweep, and the
library default moved to β=5 (validated across the whole 0.21 battery: ladder
0.61–0.63, the over-mentalizing rout deepening from 0.22 to 0.05, coins and the
depth-legibility law intact; the coordination study alone pins gentle β=3,
where the building of a handshake is visible before it locks in).

### The integration: one temperament, three fates

The discovery closed the last gap between the layers. `social_params_of`
derives a Mind's parameters from the same two temperament dials that drive
everything else: α (how fast the model of the other updates from moves) from
PRECISION, β (how decisively the model becomes action) from CONVICTION.
`mind_of(character, k)` and `face_off(char_a, char_b)` then let Story
characters meet in repeated play with no adapters — and the emergent,
unauthored consequence is the cross-layer theorem of the release: **the same
conviction that armors a character's beliefs against evidence (0.15's
arbitration, 0.17's hysteresis) exposes their behaviour to a deeper mind** —
a fixed 2-ToM reader takes 0.70–0.72 from guarded, stoic and anxious 1-ToM
hiders and only 0.61 from the tender one. Conviction protects the interior and
betrays the surface: one trait, both fates. `tests/test_integration.py` stakes
the coherence itself — the open temperament is simultaneously the most curious
chooser (0.20) and the least legible opponent (0.22), from one authored
disposition.

### Also improved

The fork's daring map (0.20, study IV) had two of three rows saturated; at
stakes 6/7/8 and gentler decisiveness every cell is informative — including
the new best cell in it: even at the highest stake, enough mystery tips her
(70%). `play` accepts per-seat `alpha_a/beta_a/alpha_b/beta_b`, so
differently-tempered minds can meet. Flagship texts and quoted figures were
refreshed to the new defaults, and study VI (THE TELL) was added to
`the_other_mind.py`.

*Version: SOMA 0.22.0. Tests: 389 passing. New: `legibility`/`LegibilityReport`,
`social_params_of`/`mind_of`/`face_off`, per-seat parameters in `play`, default
β 3→5, sharper daring map, study VI in `the_other_mind.py`; 4 new mentalizing
tests + `tests/test_integration.py` (5 cross-layer tests).*

---

## 0.23 — The playground closes the loop: files, both editors, every layer

This release brings the whole predictive-characterization arc into the
browser, and closes the last workflow gap in the playground: a user can now
WRITE a SOMA file on the page and USE it through the library on the same page.

### What the audit found

The playground already ran the real toolchain via Pyodide with two modes — a
SOMA editor (run/check/sift/prose/trace/query/perturb) and a Library editor
(user Python over `soma.narrative`) — but its 22 library examples stopped
before 0.15, hand-written SOMA could reach the library only as an inline
string, no file could be named, saved, or reopened, and switching modes
*destroyed* the user's buffer.

### The workspace

`web_bridge` gains a workspace (`ws_save`/`ws_list`/`ws_read`/`ws_delete`,
sanitized names, `/work` on the virtual filesystem with a native fallback);
library code runs with the workspace as its cwd, so `open("my_story.soma")`
just works, and the namespace gains `run_file(name)` (backed by the new
`soma.run_file`, the file twin of `run_source`) and `workspace()`. The page
gains a **Save ▸ file** button in both editors, a **Your files** rail section
(click to reopen — a .soma file opens in the SOMA editor, a .py in the Library
editor; ✕ deletes), persistence of files AND both editors' buffers across
reloads via localStorage, restoration into the virtual FS at boot, and a
post-run sync so files *written by the user's Python* appear in the rail.
Mode-switching now stashes and restores per-mode buffers — work is never lost.

### The eight new library examples (each verified through the shipped payload)

`lib/pc_signature` (0.15 — trait-identical, profile-different, similarity
0.33 with equal means, plus the diagnostic situation), `lib/pc_portrait`
(0.17 — calm and panic as attractors; the reappraisal sweep ends in "panic
attractor GONE"), `lib/pc_network` (0.18 — vulnerable wiring tips at stress
2.5, resilient at 3), `lib/pc_diary` (0.19 — Ana's and Bo's hubs both
recovered from diaries alone), `lib/pc_choice` (0.20 — the explore/exploit
crossover and the temperament-decided fork), `lib/pc_other_mind` (0.21 — the
ladder, the 0.06-vs-0.64 over-mentalizing rout, depth read from moves),
`lib/pc_tell` (0.22 — decisiveness is legibility; the guarded are read), and
`lib/pc_files` (the file loop: write a .soma from Python, `run_file` it, turn
one dial — precision 0.9→0.05 — and the same heart goes unfelt).

`tests/test_playground.py` (13 tests) stakes the workspace contract
(roundtrip, traversal containment, cwd restoration, Python-written files
listed) and executes every shipped pc example exactly as the browser would,
asserting their key results ("mean levels equal: True", "GONE", both hubs
"OK", "unfelt").

*Version: SOMA 0.23.0. Tests: 402 passing. New: `soma.run_file`; `web_bridge`
workspace API + workspace-cwd `run_python` with `run_file`/`workspace()`;
playground Save ▸ file, Your files rail, per-mode buffer preservation,
post-run file sync, boot restore; 8 predictive-characterization library
examples (30 total); `tests/test_playground.py` (13 tests).*

---

## 0.24 — The audit: a semantic correction, a plumbing fix, and honest renders

A full-repo audit (every flagship executed, every shipped payload example run
through the bridge, every recently-touched API inspected) found and fixed the
following.

**The one real inaccuracy — `spontaneous_nonrecovery` conflated two claims.**
`NetworkHysteresis.spontaneous_nonrecovery` was `width > 0 or releases_at is
None`, so any hysteresis at all printed "removing the stressor does NOT lift
the depression". That over-claimed: the vulnerable network (conn 1.4) in fact
releases at stress 1.0 — its depression *outlives its cause* (the weaker,
still-striking claim) but does lift when the stress falls far enough. Worse,
the RESILIENT network also has width 2, so the old render printed the
non-recovery line directly above the flagship's own narration that "lifting
the stressor lifts the depression". The corrected semantics: spontaneous
non-recovery is `releases_at is None` — the network holds itself down at zero
stress — and it is real: at severe connectivity (3.2) the down-sweep ends with
five symptoms still active at stress 0. `render()` now reports three honest
regimes (reversible / hysteretic, releasing only at X / spontaneous
non-recovery), `the_weight.py` study II shows all three (resilient,
vulnerable, severe), the `lib/pc_network` playground example *demonstrates*
the recovery claims it makes instead of asserting them, and the tests pin the
corrected semantics (the vulnerable network is hysteretic-but-recovers; the
severe one never releases). §0.18's summary phrasing, which used the same
conflation, is corrected by this section.

**The one real bug — `decide()` ignored supplied decisiveness.** The keyword
default `decisiveness=3.0` always overrode whatever a dict first-argument
carried, so `decide({"decisiveness": 0.1}, ...)` and
`decide({"decisiveness": 99}, ...)` produced identical distributions. Default
is now `None`, falling back to the resolved value (itself defaulting to 3.0);
explicit keywords still win.

**Smaller fixes and improvements.** `PortraitReport.healthy_share` is now a
public property (studies and the shipped portrait example previously reached
for the private `_healthy_share`; all call sites migrated). `somac --version`
exists. The fair-coin line in `the_other_mind.py` says "at chance" rather than
quoting 0.50 against a printed 0.48. The `lib/handwritten_soma` example prints
clean quale names instead of `Qualia<...>`. `web_bridge.run_python`'s
docstring documents the file workflow it actually provides. §0.21's figures
carry a note that they were measured at the 0.21 defaults (β=3) that 0.22
re-baselined. A `.gitignore` keeps test scratch (`.soma_work/`, caches) out of
future patches. The audit also confirmed non-issues: the ✗ marks in
`the_diary.py` and `the_other_mind.py` outputs are intentional
(identifiability results), `run_all.py` is correctly scoped to TUTORIAL.md's
build()-style stories, and no name collision exists between `choice.Decision`
and the drift-diffusion `decision` module.

*Version: SOMA 0.24.0. Tests: 403 passing. Fixed: `spontaneous_nonrecovery`
semantics + three-regime render; `decide()` decisiveness plumbing. New:
`PortraitReport.healthy_share`, `somac --version`, severe-regime study in
`the_weight.py`, demonstrated recovery claims in `lib/pc_network`,
`.gitignore`.*

---

## 0.25 — Legitimacy: the belief that holds the holder

The layer models system justification — why the people a system injures so
often defend it — grounded in Jost & Banaji (1994), Jost & Hunyady (2002, the
palliative function), Jost & Thompson (2000, the self-worth cost to the
disadvantaged), Wakslak et al. (2007, the dampening of moral outrage), Laurin,
Shepherd & Kay (2010, inescapability raises defense of the status quo), and
Friesen et al. (2019, the three antecedents: threat, dependence,
inescapability — and "motivated ignorance").

`justifies(char, system, dependence=, inescapability=, threat=)` wires a
legitimizing belief as an ordinary `believes(...)` lie whose **conviction is
derived from the three antecedents** and whose **trust in the disconfirming
evidence is derived inversely** (motivated ignorance — a new `evidence_trust`
parameter on `believes()`, default unchanged at 0.35). The palliative trade is
wired into the body and *gated on the belief itself* via the lie's `_seen`
channel: while the belief holds, injury buys quiet (anxiety driven down) at
the price of self-regard (worth driven down, disadvantaged only), with outrage
dampened; the moment it breaks — the standard overwhelm revelation — the
palliation stops, the grief arrives whole, and the outrage becomes available.

Because both dials are derived, the predictions are too. `palliative_tradeoff`
prices the belief (with it: anxiety 25, worth 31; without: anxiety 86, worth
60 — the belief buys ~60 points of quiet and charges ~29 of worth).
`antecedent_dose` produces the **exodus curve**: at inescapability 0.95 the
belief breaks only at harm ≥ 7 (holding against everything the system
ordinarily deals); at 0.25, harm ≥ 3 suffices — nobody's injuries changed, the
thinkability of an exit changed what they were allowed to mean. `conscientize`
doses Freire's critical consciousness: each session of dialogic challenge
lowers *felt* inescapability, and the tipping point falls from 6 to 3 over
eight sessions. The flagship `examples/narrative/the_feather.py` stages all of
it on THE UNMOORING's cast — Neva's condolence-feather priced as the purchase
she says it is, the homeland legend as a solvent, the Mender's year as a dose,
and the dark-of-moon night as a quarter's beliefs breaking together.

*Version: SOMA 0.25.0. Tests: 416 passing. New: `soma/narrative/legitimacy.py`
(justifies, derived_conviction, derived_evidence_trust, palliative_tradeoff,
antecedent_dose, conscientize); `evidence_trust` on `believes()`;
`examples/narrative/the_feather.py`; `tests/test_legitimacy.py` (13).*

---

## 0.26 — The legible release: every study output, drawn

Every report renderer was audited for the question "does the text show the
finding, or only state it?" and upgraded where the answer was the latter. No
mechanism changed; 416 tests still pass; every number is the same. What
changed is that the outputs now carry their own visual argument:

* **Phase portraits** letter each basin by its *temperature* (`w`arm, `c`old,
  `m`ixed, or the psyche's labels such as `p`anic) instead of by attractor
  index — so two landscapes that differ only in what their single attractor
  *is* draw visibly different planes (`wwww` vs `cccc`, where both previously
  rendered `aaaa`), and a split landscape draws its own boundary. Duplicate
  temperatures fall back to index letters, so basins stay distinguishable.
* **Dose–response and hysteresis** (network layer) render as aligned bar
  tracks: the stress sweep shows the jump at the tipping point, and the
  hysteresis loop is visible as the asymmetry between the up and down columns
  at the same stress level (1 symptom up, 6 down — the loop, as a shape).
  Equilibrium-mode histograms carry counts; kindling shows the falling
  threshold as a shrinking bar.
* **The legitimacy reports** draw the trade as paired anxiety/worth bars
  (with vs. without the belief), and the exodus and conscientization curves
  carry a `|···▲······|` harm-scale track per row, so the tipping point is a
  marker that visibly walks left as inescapability falls.
* **Tournaments** (theory of mind) mark each cell ▲/▽ for who is being
  out-thought, making the below-diagonal ladder pop; **signatures** open each
  if–then line with a route glyph (▼ suppress, ▲ take in, ◆ breaks), so two
  trait-identical people with crossed profiles read as `▼▲` vs `▲▼` at a
  glance; **temporal networks** put magnitude bars on edges and out-strength
  bars on the hub ranking; **density** anchors its histogram with the range.
* **Second batch, from the follow-up audit:** **early warning** draws its
  overwhelm accumulator as a progress bar against the bound; **sensitivity**
  puts a variance bar on each dial's total effect; **discrimination** bars the
  divergence column and marks the winning probe `<- here` in the table
  itself; **learned helplessness** shows pretreatment vs. novel-task
  initiations as paired bars; and the **speed–accuracy tradeoff** carries
  accuracy and RT bars, so the boundary sweep reads as two opposing ramps.
* A shared `track(pos, lo, hi)` scale-with-marker primitive joined
  `soma/viz.py` alongside the existing `bar` and `sparkline`.
* The audit also closed an undone item from 0.25: the legitimacy layer now
  has its playground library example (`lib/pc_legitimacy` — the trade priced
  and the exodus curve, 31 library examples total), matching the pattern
  every other layer follows.
* **Documentation brought fully current.** The predictive-characterization
  family (0.15–0.22) and the legitimacy layer (0.25) are now indexed in
  NARRATIVE.md's API reference (previously it stopped at the 0.6–0.7
  prediction models); `TUTORIAL_CHARACTERIZATION.md` gained **§2.12 Legitimacy**,
  built from a live-verified snippet through the same pipeline as every other
  section, with the roadmap and "how the instruments relate" summary extended
  to match; both WordPress exports regenerated (130 and 302 balanced blocks);
  the assembled `TUTORIAL_PREDICTIVE_CHARACTERIZATION.md` rebuilt (1091 lines);
  and README's example section now documents the narrative-flagship and
  playground-library catalogs alongside the seventeen core `.soma` files.

Both tutorials' output blocks were regenerated from live runs against the new
renderers — TUTORIAL_CHARACTERIZATION.md via its snippet pipeline (all 14
pass) and TUTORIAL_PREDICTIVE.md via a block-by-block re-run of every fenced
example (22 blocks: 14 bit-identical, 8 regenerated, 0 errors; two previously
hand-abbreviated output blocks are now literal). Both WordPress exports
re-emitted; §2.4's prose now explains the temperature glyphs. The audit also
fixed stale version stamps (README, GRAMMAR.md, CHARACTER_DEPTH.md), corrected
two `legitimacy` docstrings whose "never breaks" claims overstated the
calibrated behavior (the never-regime exists but requires all three
antecedents near ceiling), documented `evidence_trust` in `believes()`'s
docstring and NARRATIVE.md, and repaired a tutorial sentence that attributed a
split basin to the volatile couple (whose plane is single-warm; split
landscapes are described generically now).

*Version: SOMA 0.26.0. Tests: 416 passing. Changed: `soma/viz.py` (track),
`soma/narrative/{phase,network,legitimacy,mentalizing,signature,idiographic,
density,earlywarning,sensitivity,discriminate,helplessness,decision}.py`
(render methods only), both tutorials + WordPress exports, NARRATIVE.md,
README.md, GRAMMAR.md, CHARACTER_DEPTH.md.*
