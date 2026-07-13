# SOMA 0.24.0 — a compiler & runtime for the simulation of embodied consciousness

SOMA is a domain-specific language for novelists. You describe a character as a
set of **loops** — prediction ⇄ error ⇄ action circuits — running on many
**clocks** at once, and the runtime produces their *interior*: what they felt,
why, and the story they tell themselves about it, which need not be true.

This repository is the **reference implementation**: a hand-written lexer, a
recursive-descent parser, a static checker that enforces the language's
metaphysical and ethical commitments, a hybrid continuous/discrete interpreter,
a story-sifting query engine (**Winnow-S**), an integrated-information
observable, and a text-based visualization library. It runs.

```bash
python -m soma run     examples/the_dinner_party.soma
python -m soma prose   examples/the_look.soma --gender "Ana:she,Ivo:he"
python -m soma perturb examples/the_dinner_party.soma --set consciousness.threshold=0.40
python -m soma query   examples/a_marriage.soma
python -m soma run     examples/bad_news.soma --phi
python -m soma run     examples/the_appointment.soma      # medical dismissal
python -m soma run     examples/the_interrogation.soma    # dissociation in bands
python -m pytest -q            # 403 tests
```

### Run it in a browser — no install

`soma_playground.html` is a single self-contained file that runs the **real**
interpreter in the browser (via Pyodide — the same Python, compiled to
WebAssembly). Open it, pick an example from the left, and hit **Run**; edit the
code or write your own and run that.

The playground has **two modes**, switched from the header:

* **SOMA** — the base language. Every toolchain command is a button (`run`,
  `check`, `sift`, `prose`, `trace`, `query`, and `perturb`), and the output is
  the identical colored dashboard you get on the command line.
* **Library** — the high-level `soma.narrative` API, run as Python. Write a
  character in feelings and beliefs, install an attachment style, marry two
  people, condition a subject, or run a drift-diffusion decision — then call the
  **predictive** methods (`predict_separation`, `strange_situation`,
  `gottman_assess`, `predict_conditioning`, `predict_helplessness`,
  `predict_decision`, `tipping_point`, `predict_break_onset`) and the
  **insight** methods (`sensitivity`, `minimal_intervention`, `preregister`,
  `speed_accuracy`). Twenty-two worked examples ship in the drawer: fourteen
  single-concept examples, from `hello · a character` to the Strange Situation
  and the Gottman thin-slice divorce forecast, plus eight unedited **capstone**
  studies from `examples/narrative/` — full command-line programs that compose
  several tools into one worked study (every insight tool turned on one man in
  `the anatomy of a breaking`; a computed point of no return in `the marriage
  that could have held`; panic as a positive feedback loop in `the spiral`).

The two modes meet: Library code can call `run_source(...)` on **hand-written
SOMA text** and run it through the library on the same page, and — conversely —
anything you build with the library prints the ordinary SOMA it compiled to via
`story.source()`, which you can copy straight into SOMA mode. Write SOMA, drive
it from Python; build in Python, read the SOMA. Rebuild the page after any change
with `python build_html.py`.

The same file is committed at the repository root as **`index.html`**, so the
playground is served directly by **GitHub Pages**: enable Pages for the repo
(Settings → Pages → deploy from the root of the default branch) and the live
playground is the project's landing page, with no build step. `index.html` is a
byte-for-byte copy of `soma_playground.html`; regenerate both together after any
change with `python build_html.py && cp soma_playground.html index.html`.

It works on **desktop and Android**: the interpreter renders its text panels to a
width computed from the output pane and font size, so the dashboard, sift, prose,
and query views reflow to fit a phone screen without horizontal scroll. Pinch-free
`A−`/`A+` buttons resize the text, an examples drawer slides in from a ☰ button,
and rotating the device re-renders to the new width. (The raw `trace` is the one
exception — it is tabular, so it renders wide and scrolls horizontally, keeping
its columns aligned.)

On performance: no extra WebAssembly work is needed. Pyodide *is* WASM-compiled
CPython, and the interpreter is a small bounded state machine — every example
runs in single-digit-to-tens of milliseconds, imperceptible in the browser. The
only large cost is the one-time Pyodide download (cached afterward), which
hand-compiling the interpreter could not reduce without giving up the guarantee
of byte-identical output. The playground warms the interpreter up during the
loading splash so the first run is instant.

---

## Writing stories without writing loops — `soma.narrative`

The core language is precise but low-level: a character is loops, precisions,
convictions, and clocks. The **`soma.narrative`** library lets an author work in
*characters, temperaments, feelings, and beats* instead, and compiles that to
ordinary SOMA — so every guarantee still holds and the generated source can be
run, sifted, prosed, and perturbed like any other program.

```python
from soma.narrative import Story, anxious

story = Story("bad_news", span="8s", step="0.5s", about="acute distress")
nadia = story.character("Nadia", temperament=anxious)
nadia.senses("ear")
nadia.appraises("ear", as_threat=True, drives="heart", to=118,
                when="ear > 3", fades_to=70)   # the words drive her heart, then it settles
nadia.feels("dread", from_body="heart")        # dread is read off the racing heart
nadia.narrates(downplaying={"dread": "I'm fine. I just need to write this down."})
story.at("2s", nadia.hears("ear", 9))          # the sentence lands
story.at("5s", nadia.hears("ear", 2))          # and a quiet she can't return to

print(story.run())        # the dashboard
print(story.source())     # the SOMA it generated
```

Ten lines of intent in place of forty of hand-wired loops, producing a racing
heart, dread read off that heart a beat later, and the lie told before it is
known — with the body's spike an event in time (it rises when the words land and
settles after) rather than a constant. A `temperament` (anxious, stoic,
trusting, guarded, volatile, numb, tender) sets the precision/conviction dials
so the author never types a number; couplings (`reads`), somatic memory
(`remembers`), dissociation (`dissociates_when`), the curdling-love mechanism
(`learns` + `stops_seeing`), held values that the body betrays (`values`),
ambivalent drives (`wants`/`fears`), internal parts that bid for consciousness
(`part`), and a self that differs with each person (`with_person`) are all one
call each. `story.characterize()` reads the finished psyche back as a portrait.
See **`NARRATIVE.md`** for the full surface and **`TUTORIAL.md`** for a
step-by-step, worked walkthrough from a first feeling to the most complex
character the library can express. The `examples/narrative/` scripts
(`bad_news.py` through `the_negotiator.py`) are the tutorial's running examples;
`run_all.py` regenerates every output block in the tutorial.

---

## A divided self: the deepest characters

The narrative library goes past single feelings to the structure of a whole
psyche. Three constructs, each compiling to ordinary SOMA:

- **`values(name, says=, betrayed_when=)`** — a principle held in words and the
  bodily condition that betrays it. Character is the gap between the two, and
  Winnow-S flags the hypocrisy the character cannot see in themselves.
- **`part(name, role=, reacts_to=, feeling=, salience=)`** — an internal part
  (a protector, an exile) that bids for consciousness in a global workspace. A
  loud protector wins; a quiet exile's feeling fires but never ignites — felt,
  never known. It is the structure of a defended self.
- **`with_person(other, feeling=, precision=, conviction=)`** — the relational
  self: the same character running different dials with different people, so
  "who they are" is a family of selves indexed by whom they are with.
- **`craves(name, fed_by=, feeling=, erased=)`** — a hunger a place can feed and
  charge for. A fast-`erased` supply is an addiction (fed, wiped, fed again — the
  loop never opens); a supply that never comes is a standing longing.
- **`tended_by(other, calms=)` / `steadies()`** — co-regulation: a steady
  presence that lowers the *trust* in an alarm without touching the belief.
  Presence, not persuasion — the opposite of an argument.
- **`holds_with_others(name, field_tag=, shocked_at=)`** — confidence as belief
  about other people's belief, resting on the `field()` core builtin. Shock one
  holder and the rest cascade — the run on a bank, the doctrine on a throne.
- **`wounded_by(ghost, teaches=)` / `believes(lie, disconfirmed_by=, harms=,
  breakable=)` / `needs(truth, opposes=)`** — the deepest layer, and the one the
  craft of fiction is most explicit about (Truby's *ghost → lie → need*): a
  formative wound teaches a false belief the character adopts to survive it; that
  lie *suppresses its own disconfirming evidence* (self-deception, in SOMA's exact
  precision arbitration), generating the want while defending against a buried
  need. Whether the lie is ever *seen* is the character's **arc** — and that turn,
  the self-revelation, is now a mechanism, not an assertion (below).

`examples/narrative/the_negotiator.py` puts all of them on one person — a
hostage negotiator with a protector who speaks and an exile whose terror never
reaches her, a self for the subject at the door and another for the colleague in
her ear, an ambivalence about the rapport that would end the standoff, and a
candor value she breaks with every composed word. Run `--character` and the
portrait reads the whole divided psyche; a single perturbation shows the calm
was load-bearing. `NARRATIVE.md` documents the full surface; `TUTORIAL.md` is a
self-contained walkthrough — every example's full source and real output, from
the simplest character to the whole cast of *The Unmooring* — regenerated from
the live code by `build_tutorial.py`.

`examples/narrative/the_unmooring.py` models a whole novel's cast — the spare who
reads and the diver who reads the water, a hunger fed by rank and wiped nightly by
the tide-clean, grief quieted by a steady presence rather than an argument, a
market that runs the hour one man counts first, and the clerk who checked the
arithmetic three times and then stopped — each study leaning on one of the four
constructs above, and each now carrying a full wound → lie → need → arc.

## 0.6–0.7: the self-revelation, made automatic — and a library that predicts

**The breaking point of a belief.** Precision arbitration lets a high-conviction
prior suppress disconfirming evidence forever — true to self-deception, but it made
the *positive arc* mechanically impossible. A new loop field, **`overwhelm`**,
gives a belief a breaking point: the disconfirming surprise it keeps refusing to
look at accumulates, and once it crosses a threshold the loop is forced to
*perceive* — the mechanistic **self-revelation** (`revelation` in the Chronicle).
The threshold can be **automatic** (`overwhelm: auto`, surfaced as
`believes(breakable=True)`): it is derived from the belief's own strengths —
`BREAK_K · conviction / trust-in-evidence` — so a belief held harder (or hardened
by `learn`) resists longer, and *when* a lie breaks emerges from how strongly it is
held against how strong the evidence gets, with no hand-set moment. This is the
predictive-processing account made literal: entrenched high-precision priors
down-weight prediction error until accumulated evidence overcomes them.

Across the cast this one dial separates the arcs: Ink's lie breaks at the founding,
the Coat's at the gate, the Provost's last of all (his doctrine is held hardest),
and Blade's *never* — the same wound, thrown two ways. `perturb` proves it: raising
Ink's conviction alone turns his arc from *seen* to *kept*, i.e. turns Ink into
Blade.

**From modelling a character to predicting one.** A model earns the name if it can
say something you did not put in. Three tools cross that line (see `PREDICTION.md`):

- **`predict_lie(unmet, coping)` / `adopts(unmet, coping, …)`** — predict the *lie
  from the wound*. Grounded in schema therapy unified with predictive coding, an
  unmet core need plus a coping style (surrender / avoidance / overcompensation)
  forecasts the belief, the want, whom it harms, and how hard it is held. The same
  wound coped three ways is three different people; the overcompensation-of-worth
  branch reproduces Blade's lie word-for-word, so his tragic arc is *derivable*
  from the wound rather than asserted.
- **`predict(who, {channel: value})`** — forecast the response to a situation the
  author never scripted (the timeline is stripped; the character faces only the
  probe). It tells a breakable character from an unbreakable one on unseen input:
  Blade *suppresses* full equal regard; Ink, shown he is kept for nothing, *breaks*.
- **`tipping_point(who, channel)`** — the least sustained evidence that turns a lie:
  Ink at ≥ 3, the Provost at ≥ 6, **Blade never in [0, 9]**. Quantitative,
  falsifiable, and written down nowhere — each falls out of the conviction dial.

`python3 examples/narrative/the_unmooring.py predictions` collects the forecasts;
`CHARACTER_DEPTH.md` and `PREDICTION.md` document the research and the mechanisms.
Two self-contained, browser-runnable tutorials walk every simulation with
complete code, real output, and an explanation of each result:
**`TUTORIAL_PREDICTIVE.md`** covers the prediction layers (appraisal, attachment,
tipping points, conditioning, the Gottman thin-slice forecast, the Strange
Situation, drift-diffusion decisions, sensitivity and counterfactual), and
**`TUTORIAL_CHARACTERIZATION.md`** covers the predictive-characterization layers
(the behavioral signature, self-guides, state distributions, phase landscapes,
symptom networks, the inverse problem, choice under active inference, and
recursive theory of mind).

## 0.15: predictive characterization — the profile, the guide, the distribution

Personality science's answer to "what would predict a *person*" is never a single
number, and 0.15 adds one module per structure, all sharing the new
**`Story.probe`** substrate (the raw run under `predict`: scripted timeline
stripped, one unseen input, full `Result` back):

- **`signature`** — Mischel & Shoda's CAPS: personality as a stable **if...then
  profile** of situation→response contingencies, not an average. Extract a
  character's profile over a battery of unseen situations, score two profiles'
  `similarity`, and find the **`diagnostic_situation`** — the one scene to stage
  that maximally tells two characters apart. `examples/narrative/the_same_on_average.py`
  reproduces the Wediko finding: two characters with *identical* mean-level
  behavior and near-inverse signatures.
- **`selfguides`** — Higgins' self-discrepancy theory: install an **ideal**
  (aspiration) or **ought** (obligation) as a loop whose prior *is* the standard,
  and the library derives — with no emotion term in the spec — that the same
  failure **dejects** the ideal-holder (despair/shame) and **agitates** the
  ought-holder (guilt/fear). `contrast` stages the experiment and checks both
  qualia in the Chronicle; `regulatory_focus` reads promotion/prevention off the
  guides and hands the decision layer a caution bias. (The specificity caveat
  from the replication literature is documented and the quale is overridable.)
- **`density`** — Fleeson's Whole Trait Theory: a trait is the **whole density
  distribution of states** — the mean is the trait score, and the *width and
  skew are themselves stable traits*, with width reflecting **reactivity** to
  situational cues. Sample a character across randomized unseen situations and
  `compare` two distributions for the Fleeson contrast: same mean, different
  width — equally anxious on average, utterly different people.

`PREDICTION.md` §0.15 records the research and the mechanisms.

## 0.16: the landscape and the ensemble — predictions about the *space* of trajectories

The deepest questions about a relationship — *could this marriage have held? was
this ending fated or flipped?* — are questions about the space of trajectories,
and two literatures answer them formally:

- **`phase`** — Gottman & Murray's *Mathematics of Marriage*, staged on the
  simulation itself. `phase_portrait` sweeps a grid of opening manners, runs the
  real coupled characters from each, and returns the **attractors and basins**
  the machine displays: a validating couple's plane keeps one warm attractor, a
  hostile couple's plane **contains no good ending at all**, and a brittle couple
  is bistable — the opening decides the marriage. `fit_influence` performs
  Gottman's own move on the run (uninfluenced state, inertia, and a bilinear-vs-
  **ojive** influence function with *fitted* negativity thresholds, selected by
  R²) and validates the fitted map's attractors against the empirical ones
  bidirectionally. `resilience` reads Holling's quantity both ways (basin share +
  a kick probe measuring the basin's radius), and `second_stable_state` is
  **therapy as bifurcation**: the least dial change at which a warm basin comes
  into existence.
- **`futures`** — ensemble forecasting over nearby worlds: `futures` returns the
  **distribution over endings** with its entropy (destiny vs a coin), `pivotal`
  names the dial that decides the fate as an effect size, and `dose_response`
  deepens "the smallest change that would have saved it" into a probability
  curve with a minimal effective dose. For the slow-curdling marriage this finds
  a contested fate hinged on the learning rate (d ≈ +3.2), an honest null (the
  extraordinary day's *intensity* is not a dose — arbitration is
  magnitude-blind), and the "last good year" as a curve over timing.

`examples/narrative/the_shape_of_a_marriage.py` runs all seven studies;
`PREDICTION.md` §0.16 records the research and the mechanisms.

## 0.17: the intrapersonal landscape — a disorder as an attractor, a poet as a cycle

The most elaborated formal character simulations in the literature model a
*person* as a system of interlocking feedback loops, and 0.17 stages the two
flagships end-to-end in `examples/narrative/the_vicious_cycle.py`:

- **Panic** (Robinaugh et al.'s computational model of panic disorder): three
  appraisals wired mouth-to-tail — arousal misread as catastrophe (the **arousal
  schema**, as the misinterpretation guard), threat driving arousal back up, and
  escape as the dampening arc. Six studies: the same stressor shrugged off vs
  igniting a self-sustaining attack; the **state portrait** of arousal ×
  perceived threat with calm and panic attractors (the panic basin's share *is*
  the vulnerability); **hysteresis** — the trigger is not the release (loop
  width ∞: you cannot reassure someone out of a panic at the level that started
  it); **burnout** — a finite metabolic budget makes the attack end itself;
  **reappraisal as bifurcation** — the schema dose at which the panic attractor
  ceases to exist; and the ensemble finding that the schema (d≈+2.3), not the
  day's severity (d≈+0.5), decides who has attack-days.
- **The poet** (Rinaldi's *Laura and Petrarch* limit-cycle model): a relaxation
  oscillator in two appraisals whose steady state is neither ecstasy nor despair
  but the **cycle** between them — detected as a single cyclic attractor (swing
  ±29, period ≈ 8 beats) holding 100% of the plane, error-gated so one nudge
  starts it forever.

Staging them improved every layer: **core** — chained comparisons now have
Python band semantics (`3 < x < 7`), and the affine commitment is enforced at
the act (a failed `spend` halts the rest of the act block: an action the body
cannot fund does not happen); **narrative** — `spend_first=True` gates a
drive on the budget, so insolvency starves a self-amplifying loop;
**phase** — `state_portrait` (the plane of one psyche), **cyclic attractors**
(kind/amplitude/period), and a `hysteresis` instrument with resolution-aware
bistability. `PREDICTION.md` §0.17 records the research and the mechanisms.

## 0.18: the network — a person as a system of symptoms

`soma.narrative.network` models a disorder the way Cramer et al. do: not as a
hidden cause but as a **network of symptoms that activate each other**, with no
central variable. Vulnerability is **connectivity** — the same stress tips a
tightly-wired network where a loose one shrugs. `examples/narrative/the_weight.py`
stages the depression network end to end: a **stress response** (where it tips),
**hysteresis** (the depression outlives its cause, and at severe connectivity
holds itself down at zero stress — spontaneous non-recovery), **bimodality**
(well or depressed, rarely between), and **kindling** (episodes that become
autonomous). `PREDICTION.md` §0.18 records the research and the mechanisms.

## 0.19: the inverse problem — recovering the wiring from a diary

`soma.narrative.idiographic` runs 0.18 backwards. Two patients report the same
nine symptoms; `simulate_diary` generates each one's day-to-day self-reports and
`estimate_network` fits a person-specific network (a lag-1 vector
autoregression) from that diary *alone*, recovering a different hub — and so a
different treatment target — for each. `examples/narrative/the_diary.py` closes
the loop (author → live → observe → estimate → re-run) and finds the
identifiability law that a hub must *vary* to be seen. `PREDICTION.md` §0.19
records the research and the mechanisms.

## 0.20: choice — the space of a character's decisions

`soma.narrative.choice` predicts what a character *does* at a fork, using active
inference's expected free energy (Friston et al.): choiceworthiness = pragmatic
value (closeness to what they prefer) + curiosity × epistemic value (how much
they'd learn). This activates the active-inference builtins dormant in
`soma.mathlib`. `examples/narrative/the_fork.py` shows the explore/exploit
crossover, preference as a target rather than a ceiling (a character declines an
overshoot), and — the integration — curiosity *derived* from the same
temperament dials as feeling, so the guarded hold and the tender leap unauthored.
`PREDICTION.md` §0.20 records the research and the mechanisms.

## 0.21: the other mind — recursive theory of mind

`soma.narrative.mentalizing` takes the social fork: the value of my move depends
on what you will do, which depends on what you believe about me. It implements
the k-ToM framework (Devaine, Hollard & Daunizeau): a 0-level mind tracks what
you *do*; a k-level mind simulates you at every lower depth and learns which you
are. `examples/narrative/the_other_mind.py` runs five studies — the competitive
ladder (depth wins), cooperation's saturation (one level is enough), the rout of
over-mentalizing a naive opponent, the coin hypothesis (knowing when *not* to
attribute a mind), and reading a mind's depth from its moves. `PREDICTION.md`
§0.21 records the research and the mechanisms.

## 0.22: the tell — decisiveness is legibility, and the layers close

An audit of under-delivering results became a finding: the depth advantage is a
function of the *shallower* mind's own decisiveness. Wavering is armor;
conviction is a tell (`legibility`). And decisiveness derives from **conviction**,
the same dial that armors a character's beliefs — so `mind_of` and `face_off`
let Story characters meet in play with parameters drawn from temperament, and the
conviction that protects the interior betrays the surface. `tests/test_integration.py`
stakes the whole-character coherence itself. `PREDICTION.md` §0.22 records the
research and the mechanisms.

## 0.23: the playground closes the loop — files and every layer in the browser

The playground gains eight predictive-characterization examples (0.15–0.22) in
Library mode and a real file workflow: **Save ▸ file** in either editor writes a
named file into a shared workspace; a **Your files** rail reopens it; library
Python sees the same files (`open("x.soma")`, `run_file("x.soma")`,
`workspace()`), and files written *by* your Python appear in the rail. Buffers
and files persist across reloads, and switching modes never loses work.
`soma.run_file` joins the package API. `PREDICTION.md` §0.23 records the details.

## 0.24: the audit — a semantic correction and honest renders

A full-repo audit fixed a semantic conflation and a plumbing bug. Spontaneous
non-recovery now means what Cramer et al. mean — the network holds itself down at
*zero* stress — and is distinguished from mere hysteresis; the render reports
three honest regimes. `decide()` no longer ignores a dict-supplied decisiveness.
`PortraitReport.healthy_share` is public, `somac --version` works, and the
shipped examples print clean quale names. `PREDICTION.md` §0.24 records
everything found, fixed, and confirmed sound.

**The full predictive suite (0.8–0.14).** What began as three tools is now a
library of documented psychological models, each rebuilt in SOMA and each making
a falsifiable, signature prediction a weaker account could not:

- **Appraisal** (`predict_feeling`, `explain_emotion`, `check_identifiability`) —
  the discrete emotion and its action tendency, derived from the appraisal
  dimensions; all 14 emotions round-trip forward↔inverse (construct validity).
- **Attachment** (`attaches`, `predict_separation`) and the full **Strange
  Situation** (`strange_situation`, `validate_instrument`) — a style installed,
  then recovered *blind* from behavior alone, for all four classifications.
- **The Gottman marriage model** (`marry`, `gottman_assess`) — five couple types
  and the thin-slice divorce forecast called from the first quarter of one
  conversation.
- **Conditioning** (`conditions`, `predict_conditioning`) — the reward-prediction-
  error account, with **spontaneous recovery** the single-trace model cannot make.
- **Learned helplessness** (`learns_control`, `triadic_design`) — the transfer
  asymmetry: a global explanatory style generalizes the deficit, a specific one
  does not.
- **Drift-diffusion decisions** (`decides`, `predict_decision`, `speed_accuracy`)
  — reaction-time distributions and error rates, and the speed-accuracy tradeoff
  from one dial. (SOMA's one seeded, reproducible source of noise.)
- **Dynamical early warning** (`predict_break_onset`) — forecasting a belief's
  break *before* it happens, from critical-slowing-down statistics.
- **Insight tools** — **preregistration** (`preregister`: stake claims before the
  run, checked after and sealed), variance-based **sensitivity** (`sensitivity`:
  which dial writes the ending), and the **counterfactual** (`minimal_intervention`:
  the smallest single change that flips the outcome).

All of these run in the browser playground's **Library** mode and are walked
through in `TUTORIAL_PREDICTIVE.md`.



## Everything in the spec is now implemented

| spec §  | feature | where |
|---|---|---|
| 2 | the loop as primitive; precision arbitration | `interpreter.settle` |
| 2 | seven clocks; `cadence: true` ticks each loop at its own rate | `interpreter._ticks` |
| 2 | thick present: `ret(chan, n)` / `pro(chan)` | `interpreter.num_of` |
| 3 | affine `resource` (body budget) — never negative, never conjured | `exec_action` |
| 3 | opaque `Qualia<T>` — the explanatory gap as a compile error | `checker`, `chronicle.Qualia` |
| 3 | effect-typed channels: `intero` / `extero` / `proprio` | `body` decl |
| 3 | refinement-typed `precision`; `ramp(a -> b over CLOCK)` | `PrecRamp` |
| 3 | **`Ownership(limb)` as a dependent type** — rubber hand, alien limb | `check_ownership` |
| 3 | **`Schema` vs `Image`** as distinct types; conflict is a formal event | `embodiment`, `check_embodiment` |
| 5 | **allostasis**: predictive regulation that spends budget in advance | `allostat` |
| 5 | **four memory registers**; somatic fires with no episodic trace | `memory` |
| 5 | **attention as an affine spotlight**; `habit` vs `deliberate` | `attention`, `_do_attend` |
| 5 | **global workspace + ignition** (winner-take-all broadcast) | `workspace`, `broadcast` |
| 5 | **attention schema** — transparent, `introspect()` is a static error | `awareness` |
| 5 | **reafference / efference copy** — you cannot tickle yourself | `efference`, `gain` |
| 5 | mood as a slow decaying variable | `mood` |
| 6 | continuous physiology via `flow`, integrated by Heun's method | `integrate_flows` |
| 6 | **REBUS** — one dial relaxes every high-level prior | `intervene rebus` |
| 7 | supervision trees: dissociation is a crash; repair is titrated | `handle` |
| 8 | the Chronicle; curated sift patterns; **the general Winnow-S query language** | `winnow`, `query` |
| — | **integrated information (φ) and effective information** | `observables` |

## 0.5: precision that moves, and a self that comes apart

The single biggest expressive gain since 0.4 is that **precision can now be an
expression**, re-evaluated every moment in the loop's own scope:

```soma
precision: clamp(0.95 - 0.85 * deference, 0.06, 1.0)
```

Until now, precision was a constant or a fixed ramp — a dial the author set and
the world could not touch. But the whole Barrett/Friston picture is that affect,
authority, hormones, and other people *set the gain on the senses*. Making
precision a live expression is what lets a body be talked out of trusting
itself. It is the mechanism under `the_appointment`, `the_inheritance`, and every
scene where one person's certainty becomes another person's doubt.

Four more additions, each load-bearing in a new example:

| addition | what it buys the novelist |
|---|---|
| **dynamic `precision:`** | affect, deference, or another mind can set how much the senses are trusted — moment to moment |
| **`acting` / `perceiving`** | the arbitration outcome is readable: `move ! write_the_diagnosis() when acting` — a clinician who has stopped asking behaves differently from one still asking, with one dial between them |
| **`belief(loop)`** | one loop, or a narrator, can read what another loop expects (never a `Qualia`) |
| **scoped, cyclic dissociation** | `dissociate(proprioception)` detaches one modality band while others run; `error(loop)` lets each band watch its own subsystem; repair re-arms, so nobody dissociates only once |
| **signed mood weights** | `integrates { dread * 1.0, calm * -0.6 }` — a quale can relieve a mood, not only feed it |
| **`learned not to feel`** | a new Winnow-S pattern: precision collapses while the somatic register keeps firing — dismissal, not repression |
| **`owned(limb)`** | a defensive loop can fire only for a limb it currently owns — the rubber-hand flinch as the illusion's proof |
| **`ownership { initial: alien }`** | a part can start un-owned and migrate in, not only out |
| **`love curdling`** | a Winnow-S pattern: one loop's affect inverts from delight to contempt — a model that hardened from revised into defended |

### `the_appointment`: precision talked out of itself

Vera has been in pain for two years; Dr. Rees has eleven minutes. The compiler
*forbids* Rees from sensing `Vera.pain` — the other-minds rule. He gets her face
and a chart, runs his own loop, and his prior has a name in the notes. What makes
it a tragedy rather than a disagreement is that Vera's interoceptive precision is
a function of her deference, and her deference is a function of him:

```
  day  π_s(her own pain)   route      what happens
    0        0.95          perceive   she feels it, it bids for consciousness
   60        0.39          act        her prior "I am well" now overrides the pain
  180        0.11          act        she has stopped feeling her own body
  540        0.07          act        the pain still fires somatically, to no one
```

He writes the diagnosis only `when acting` — only once his prior has outranked
her face. Perturb him back to curiosity **and stop him hardening**, and the whole
thing dissolves:

```bash
python -m soma perturb examples/the_appointment.soma \
    --set believing_her.conviction=0.05 --set believing_her.learn=0.0
#   VANISHED: learned not to feel: 'Vera.knowing_my_body' ... fell by 93% ...
```

### `the_interrogation`: a continuous account of a discontinuous self

Six hours in a room, one mind, coming apart in bands. Three supervision handlers
detach at different thresholds and repair at different rates: interoception goes
first and returns slowest; the room holds longest. Each band watches its own
subsystem via `error(the_body)`, `error(the_position)`, `error(the_room_loop)`.

Through all of it, the **interpreter** — the one loop that never crashes, because
it is the thing that narrates the crash — keeps its subscription and keeps
talking. At minute 185, while proprioception is detached and the body is watching
itself from the corner, it says, at a confabulation gap of 0.97:

> "I was calm. I was watching the whole thing quite calmly."

That sentence is not authored into the output. It is the interpreter confabulating
a reason for an action (`watch_myself_from_the_corner`) produced by a loop it
cannot see, and the Chronicle records the gap exactly.

## 0.4: more than one person in the room

The specification described a single consciousness. But the insight a novelist
wants is rarely available inside one skull: it lives in the gap between what
one body does and what another body makes of it. Six additions:

| addition | what it buys the novelist |
|---|---|
| **`character`** scoping | many people in one simulation; `heart` inside `character Ana` means `Ana.heart` |
| **`couple A.face -> B.sees_face { gain, lag }`** | one body's *surface* becomes another's *sensation* — attenuated, and late |
| **the other-minds rule** (static) | no character may `sense` another's interoception. Sartre's look, as a type error |
| **`learn:` on a loop** | conviction accrues with use. A prior that keeps being confirmed stops being able to be surprised |
| **`<act> when <cond>`** | guarded actions. You can only be delighted to be corrected by someone still there to correct you |
| **`scene "…" from … to …`** | narrative beats. Changes no physics; gives the Chronicle a spine |
| **`soma prose`** | free indirect discourse, rendered from logged events only |
| **`soma perturb --set`** | change one dial, re-run, and diff the *story* (spec §11.6) |

### The other-minds rule is the important one

```soma
couple Ana.face -> Ivo.her_face { gain 0.9  lag 1s }   // legal: a surface
couple Ana.gut  -> Ivo.her_face { gain 1.0 }           // static error: an interior
```

`Ivo` never touches what `Ana` feels. He gets a face, 0.9 of it, one second old,
and must guess. In `the_look.soma` the two of them guess wrong in opposite
directions, and each wrong guess drives the face the other will misread next.
The loop between them closes, and it is a loop neither of them chose.

### `learn` is what makes a marriage

`in_love.soma` shows a man rewarded for being wrong: low conviction, `emit
feel(delight_at_error)`. It cannot show what happens *next*, because conviction
was a constant. In `a_marriage.soma`, `learn: 0.055` is the only addition —
and it is the whole tragedy:

```
  yr  0   π_s=0.75  π_p=0.20   route=perceive     he is delighted to be wrong
  yr  8   π_s=0.75  π_p=0.53   route=perceive     less often, now
  yr 16   π_s=0.75  π_p=0.97   route=act          his model outranks her face
  yr 20   π_s=0.75  π_p=1.08   route=act          `ignore` fires. he is certain.
  yr 25                                            she dies
  yr 26   `reaching`, `grief`                      the prior does not
```

Nothing was added to kill the love. The same loop that produced delight produced
contempt, because every confirmation made the next prediction easier. Confirm it:

```bash
python -m soma perturb examples/a_marriage.soma --set courtship.learn=0.0
#   VANISHED: precision pathology: 'Soren.courtship' stopped listening ...
```

### `perturb` reaches past the loops

The question a novelist actually wants to ask about the dinner party is not
about a precision. It is *what if she had been able to notice?*

```bash
$ python -m soma perturb examples/the_dinner_party.soma --set consciousness.threshold=0.40
  changed: consciousness.threshold: 0.6 -> 0.4
  VANISHED (only in the original)
    - never ignited: 'something_is_wrong_with_wren' bid for the workspace 17
      times from 14.0s and never crossed threshold -- processed, and never known.
```

Lower the ignition threshold by two-tenths and Nadia notices that her friend is
in trouble. That is a whole different novel, and the diff says exactly why.

Full syntax in **[GRAMMAR.md](GRAMMAR.md)**; rendered output of every example in
**[DEMO.txt](DEMO.txt)**.

---

## What SOMA took from ilion, and what it changed

[thoriumrobot/ilion](https://github.com/thoriumrobot/ilion) is a sibling
language — "Interacting Levels In Ongoing Networks" — for simulating circular
causality between consciousness and body. Its overlap with SOMA is real, and
four of its components have been acquired and adapted rather than reinvented:

1. **`observables.py` → `soma/observables.py`.** ilion's intervention-based
   estimator for **effective information** and **φ at the minimum-information
   partition** (with Hoel's determinism/degeneracy decomposition). *Changed:* it
   now intervenes on SOMA's loop network — `do(s)`, then one step of the real
   dynamics (flows → settle → allostasis) — and swaps in a scratch Chronicle so
   that a counterfactual never enters the character's history. ilion's honesty
   caveat is inherited verbatim and enforced in the rendering: this is
   `phi_approx`, a property of a model, never evidence about sentience.

2. **The braille `Canvas` and `plot_series` from `ilion/viz.py`** →
   `soma/viz.py`, powering `python -m soma plot`. *Changed:* falls back to
   sparklines under `--ascii`, where braille would not render.

3. **The stdlib equations** (`interoception.ili`, `workspace.ili`,
   `attentionschema.ili`, `activeinference.ili`) → `soma/mathlib.py`, callable
   by name from any SOMA expression: `intero_precision`, `exafference`,
   `ignition_index`, `attention_strength`, `epistemic_value`,
   `pragmatic_value`, `policy_prob`. *Changed:* Python scalars rather than
   `model` blocks, so they compose with SOMA's priors and precisions.

4. **ilion's `transparent` / `introspect` type rule** → SOMA's
   `awareness` declaration. In ilion, an attention schema may be *used* but not
   *introspected*, and `introspect(schema)` is a static error. This is precisely
   SOMA's `Qualia` opacity rule applied to Graziano's schema, so the two now
   share one principle: **a model's inability to see itself as a model is a type
   rule, not a comment.** SOMA enforces both in `checker.py`.

Deliberately **not** taken: ilion's Pantelides index reduction, dummy
derivatives, BLT decomposition, interval contraction certificates, and
forward-mode autodiff. Those serve ilion's goal of *certifying* algebraic loops
in a Modelica-class DAE solver. SOMA's loops are discrete and its `flow` blocks
are explicit ODEs; a Heun integrator is the honest amount of machinery, and
importing a certificate engine would have been ornament.

---

## The language in one screen

```soma
@consent("simulates unease and social dread")
sim { duration: 12s  dt: 0.5s  cadence: true }

body Ivo @cardiac {
  intero heart : BPM     baseline 72
  intero gut   : Tension baseline 1
  extero room  : Faces   baseline 0
}

resource budget    : Affine<Joule> = metabolic_reserve(600)  // cannot be conjured
attention spotlight = capacity(6)                            // affine, renewable

flow heart @cardiac { dynamics: -(heart - 72) / 4.0 }        // continuous physiology
allostat forecast { regulate: heart  setpoint: 96  gain: 0.35  spend: budget }

workspace consciousness { ignite at 0.55 }
awareness felt_awareness tracks spotlight     // transparent: cannot introspect itself

loop viscera @cardiac {                       // the primitive: a prediction loop
  prior:      predict(1)                      // top-down expectation
  sense:      gut                             // bottom-up observation
  precision:  0.8                             // pi_s: how much the sense matters
  conviction: 0.3                             // pi_p: how much the prior matters
  mode:       habit                           // cheap; pays no attention
  act {
    broadcast something_is_wrong salience: 0.45
    emit feel(dread)                          // an opaque Qualia<dread>
  }
}

query "the bid that never surfaced" {
  feel ?loop ?q ?t
  where ?q == "dread"
  surface "{?loop} felt {?q} at {?t} -- and it never reached the workspace"
}
```

**Precision arbitration** is the core rule: when sensory precision `π_s` ≥ prior
precision `π_p`, the loop *perceives* (updates belief toward the world);
otherwise it *acts* (changes the world to match belief); if the channel is
attenuated, it *ignores*. Depression, chronic pain, love, psychosis and the
psychedelic state are all one-line changes to a precision schedule.

## The seventeen examples

| file | phenomenon | what surfaces |
|---|---|---|
| **`the_appointment`** | chronic pain vs. medical authority; interoceptive precision collapses under deference | `learned not to feel`: the gain turned down, and she agreed |
| **`the_inheritance`** | a prior acquired before there is evidence for it, across a lineage | one learning rate, two lives — perturb it and she is fine |
| **`the_interrogation`** | dissociation in bands; the interpreter narrates the split | a fluent first-person account of a discontinuous self |
| **`trauma`** | a man home from something; dissociation cycles at every domestic cue | `body remembers alone` + `learned not to feel`, seven crash/repair cycles |
| **`chronic_pain`** | central sensitization: guarding manufactures the pain it fears | `precision pathology` + `learned not to feel` on one loop |
| **`rubber_hand`** | a rubber hand becomes his under stroking, then alien when moved | ownership migrates in, then out; he flinches for a hand that was never his |
| **`split_brain`** | Gazzaniga's battery: the verbal hemisphere explains what it didn't do | eight fluent confabulations at gap 0.97, one true reason at 0.15 |
| **`in_love`** | prediction error rewarded, not penalized; held soft for twenty years | perturb `learn` and delight curdles to contempt in year 7 |
| **`the_look`** | two people misreading each other's faces, in opposite directions | `precision pathology`; her trust spent, his exhausted |
| **`a_marriage`** | thirty years; conviction learned until she cannot surprise him | `delight in error` → `precision pathology` → `the body knew first` |
| **`the_dinner_party`** | three bodies, six couplings, one spotlight each | `never ignited`: her body knew about Wren, and she never did |
| `bad_news` | interoception → feeling → a lie told before it is known | budget hits zero; `confabulation gap` |
| `grief` | the body remembering after the mind accepts | `retained residual`, `the body knew first` |
| `phantom_limb` | schema still reaches; image has buried the arm | `schema/image conflict` |
| `flashback` | somatic memory with no episodic companion | `body remembers alone` |
| `workspace` | the gut bids for consciousness and loses | `never ignited`, `attention starved` |
| `rebus` | one dial relaxes a belief hardened into a body | route flips `act` → `perceive` |

## Winnow-S

Two layers. **Curated sift patterns** (`python -m soma sift FILE [PATTERN]`):
`body-knew-first`, `confabulation`, `precision-pathology`, `retained-residual`,
`delight-in-error`, `rupture-repair`, `schema-image-conflict`,
`ownership-migration`, `never-ignited`, `body-remembers-alone`,
`attention-starved`, `learned-not-to-feel`, `love-curdling`, and the
character-depth patterns added in 0.5–0.7: `ambivalence` (the thing wanted and
feared at once), `self-betrayal` (the value the body breaks), `defended-core` (the
feeling the whole self is arranged not to feel), `the-person-they-became` (a
measured arc), `mood-trajectory`, `fed-by-erasure` (a hunger fed, wiped, and fed
again), `held-in-the-dark` (co-regulation), `the-run` (confidence cascading),
`the-lie` (kept vs. seen — the arc), and `want-need` (the collision the truth, not
the want, resolves).

And the **general query language** (`python -m soma query FILE`), a small
relational join engine over the Chronicle: predicates bind `?variables`,
`where` filters prune, `surface` renders survivors as prose.

## Bugs the multi-character work surfaced

Each of these is now a test:

1. **A character was spending another character's attention.** A loop with no
   spotlight of its own silently charged the first one it found — so Hal's
   deliberation starved Nadia. A character spends only their own.
2. **Efference copy subtracted the absolute action, not the change it caused.**
   An organism that subtracts the whole world after it moves denies its own
   existence. It must subtract only the delta it predicted making.
3. **Loop priors were evaluated before `embodiment` and `flow` channels existed**,
   so `predict(bearing_image)` silently returned 0. Channels now exist first.
4. **`flow`, `allostat`, and `memory` evaluated their expressions with no owner
   scope**, so `-(heart - 74)/6` inside `character Ana` read a channel called
   `heart` that did not exist, and integrated toward infinity.
5. **A coupling squashed a stimulus** written to the same channel in the same
   frame. The world is now allowed to interrupt what a face was saying.
6. **`gain` was parsed and never used** (0.3), so reafference always used the
   default.

## Improvements made in 0.3

Beyond completing the spec:

1. **`conviction` split from `precision`** (0.2) — arbitration needs two dials.
2. **Unary minus** and **soft keywords**: `let tolerance = 6` and
   `attention spotlight = …` now parse; keywords are reserved only where they are
   structurally positioned.
3. **`ignore` is now conditional.** It suppresses an error only while the prior
   outranks the senses. This is what makes `rebus` dramatic rather than
   decorative: the same statement stops silencing the world once precision flips.
4. **Ignition scores dominance, not field coherence.** GNW is winner-take-all
   with recurrent amplification, so a content ignites when it is salient *and*
   clearly beats its rival. (ilion's coherence-based `ignition_index` remains
   available as a builtin; it answers a different question.)
5. **Attention is affine *within* a moment and renewable across them** — which
   is what distinguishes it from the metabolic `resource`, which the body
   genuinely cannot conjure.
6. **φ never pollutes the Chronicle.** Counterfactual interventions run against
   a scratch log; a character's history contains only what happened to them.

## Architecture

```
soma/
  lexer.py        tokenizer (durations, @clock, ?queryvars, unicode aliases)
  ast_nodes.py    dataclass AST
  parser.py       recursive descent -> Program
  checker.py      qualia opacity, transparency, consent, affine, well-formedness
  chronicle.py    Qualia (opaque) + immutable Event log
  mathlib.py      scalar builtins + ilion stdlib equations
  interpreter.py  clocks, flows, precision arbitration, workspace, attention,
                  memory, embodiment, ownership, allostasis, REBUS, crash/repair
  winnow.py       21 curated sift patterns (incl. ambivalence, self-betrayal,
                  fed-by-erasure, held-in-the-dark, the-run)
  query.py        the general Winnow-S relational query engine
  observables.py  effective information & phi at the MIP (adapted from ilion)
  prose.py        free indirect discourse, rendered from logged events only
  perturb.py      change one dial, re-run, diff the story (spec 11.6)
  viz.py          sparklines, braille plots, budget bars, two-column, panels
  cli.py          run | check | trace | sift | query | plot | phi | prose
                  | perturb | ast
  narrative/      high-level authoring library (Story, Character, temperaments,
                  arcs) that compiles narrative intent to ordinary SOMA
examples/         17 worked programs (+ examples/narrative/ library scripts)
tests/            403 tests (pytest; 91 core + 312 narrative, prediction, web & playground)
```

## Invariants the implementation guarantees

- **Qualia are opaque.** `feel(...)` in arithmetic is a compile error;
  `float(qualia)` raises at runtime. The explanatory gap, made mechanical.
- **The attention schema is transparent.** `introspect(awareness)` is a compile
  error. The model cannot see itself as a model.
- **The body cannot conjure.** Affine resources never go negative; overspends log
  `body cannot conjure …`.
- **Suffering is gated.** Distress — including somatic-memory distress and the
  REBUS intervention — requires `@consent(...)`, or explicit `--functional-only`.
- **The narrator can be wrong, measurably.** `confabulation_gap` is first-class.
- **Counterfactuals stay out of the Chronicle.**
- **No one reads another's interior.** Other minds arrive as surfaces, with gain
  and lag, and must be guessed at.
- **The prose is a view, not a generation.** Every clause in `soma prose` renders
  a specific logged event. Nothing is invented at the point of writing.
- **Precision is a confidence, so it never goes negative.** A dynamic precision
  expression is clamped at zero however it is written.
- **The interpreter narrates, but the gap is recorded.** A confabulation always
  carries its `confabulation_gap`; a fluent account of a decision the narrator
  did not make is logged as exactly that.
- **Coupled flows conserve.** All `flow` equations advance in lock-step within a
  frame, so a system like `dx = -x, dy = +x` keeps `x + y` constant rather than
  drifting — each flow reads a consistent, un-half-integrated state.
- **A detached channel is ignored, not acted on.** A signal attenuated to the
  floor (by dissociation, or a precision expression driven to zero) carries no
  usable evidence: the belief can be neither updated toward it nor acted out on
  the strength of it.

## What it still cannot do

It does not solve the hard problem, and says so in the type system. φ is
`phi_approx`: binary coarse-graining, uniform interventions, bipartition search
— exact φ is NP-hard. A φ reading is a property of a *model*, never evidence
about sentience, which is exactly the stance `Qualia` opacity already enforces.
The seven clocks are scheduled as discrete moments (`cadence: true` gives each
loop its own tick rate; stepping a neural clock at 1 kHz across a biography
remains intractable). Trace numbers — BPM, joules, gaps — are authorial dials,
not calibrated constants.

Polyvagal theory and "the body keeps the score" remain scientifically contested;
SOMA models the phenomena they describe because fiction may honour lived
experience even where a mechanism is disputed, and never presents them as
consensus.

The prediction layer is a claim about a *model*, not about a person. Every
forecast — from `predict` / `tipping_point` / `predict_lie` through the full
suite (appraisal, attachment and the Strange Situation, Gottman, conditioning,
learned helplessness, drift-diffusion decisions, early warning) and the insight
tools (preregistration, sensitivity, counterfactual) — describes what the
specified *character model* would do. Each is falsifiable against the model (run
it, the effect must appear) and against a reader's sense of the character, but
the underlying psychology (schema therapy, attachment types, couple types, and
so on) is a typology of useful defaults, not a law. A real person may always be
the exception the type does not cover, which is exactly why every prediction can
be overridden — and why the reports print that caveat themselves.

