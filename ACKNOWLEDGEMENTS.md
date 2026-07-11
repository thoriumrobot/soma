# Acknowledgements

## ilion

Four components of SOMA are adapted from
[**thoriumrobot/ilion**](https://github.com/thoriumrobot/ilion) — *Interacting
Levels In Ongoing Networks*, a language for simulating circular causality
between consciousness and body. Where its work overlapped SOMA's, it was
acquired and modified rather than reinvented:

| ilion | SOMA | modification |
|---|---|---|
| `ilion/observables.py` | `soma/observables.py` | intervention-based EI and φ at the MIP, with Hoel's determinism/degeneracy decomposition. Rewritten to intervene on SOMA's loop network and to step SOMA's real dynamics (flows → settle → allostasis); the interpreter's Chronicle is swapped for a scratch log so counterfactuals never enter a character's history. ilion's honesty caveat about `phi_approx` is inherited and surfaced in the rendering. |
| `ilion/viz.py` (`Canvas`, `plot_series`) | `soma/viz.py` | braille line plots, powering `soma plot`. Falls back to sparklines under `--ascii`. |
| `ilion/stdlib/*.ili` | `soma/mathlib.py` | the theory-bearing equations of `interoception.ili`, `workspace.ili`, `attentionschema.ili`, and `activeinference.ili`, reexpressed as Python scalars callable from any SOMA expression. |
| ilion's `transparent` / `introspect` rule | `soma/checker.py` | ilion makes `introspect(schema)` a static error, so an attention schema may be used but not seen as a model. SOMA adopts this wholesale for its `awareness` declaration, unifying it with `Qualia` opacity under a single principle. |

Deliberately **not** taken: ilion's Pantelides index reduction, dummy
derivatives, BLT decomposition, interval-arithmetic contraction certificates,
and forward-mode autodiff. Those serve ilion's goal of certifying algebraic
loops in a Modelica-class DAE solver. SOMA's loops are discrete and its `flow`
blocks are explicit ODEs; a Heun integrator is the honest amount of machinery.

Thanks are due to ilion for the `transparent` rule in particular, which named
something SOMA had only half-articulated.

## 0.4 lineage

The intersubjective additions rest on Sartre (*Being and Nothingness*, the look),
Levinas (the face of the other), Merleau-Ponty (intercorporeity), and the
predictive-processing literature on social inference. The `learn` dial is a
scalar caricature of precision learning in the free-energy framework; the claim
it makes about long marriages is a novelist's claim, not a scientific one.

## 0.5 lineage

Dynamic precision — affect and authority setting the gain on perception — is the
core of Barrett's *theory of constructed emotion* and of active-inference
accounts of interoception (Seth, Feldman & Friston). Dissociation as a scoped
supervision-tree crash follows the Erlang "let it crash" model applied to Putnam
and van der Kolk's clinical descriptions of structural dissociation; the claim
that the interpreter narrates continuously across the split is Gazzaniga's. As
before, the trauma models draw on contested literatures, and SOMA renders the
phenomena without asserting the mechanisms are settled science.

## 0.6–0.7 lineage: character depth, the arc, and prediction

The wound/lie/need layer follows the craft of fiction where it is most explicit
about interiority: Robert McKee's *Story* ("dimension means contradiction"), John
Truby's *The Anatomy of Story* (the ghost → wound → lie → weakness → need chain,
and the psychological-vs-moral distinction), and K. M. Weiland's widely-used gloss
on the positive, negative, and flat arcs. The Lie is implemented as **motivated
self-deception** in the philosophical/psychological sense — a false belief
maintained despite disconfirming evidence by suppressing that evidence (Mele; the
*Stanford Encyclopedia of Philosophy*; Deweese-Boyd) — which SOMA already had as a
high-conviction loop that *acts* rather than perceives. The automatic breaking
point (`overwhelm: auto`) is the predictive-processing account of belief revision:
entrenched high-precision priors down-weight prediction error, and change comes as
precision-weighted evidence accumulates past a threshold.

The 0.7 prediction layer draws its wound → belief mapping from **Jeffrey Young's
schema therapy** (early maladaptive schemas from unmet core needs, and the
surrender / avoidance / overcompensation coping styles), unified with predictive
coding after the framework of Hoffart and colleagues (*"Early maladaptive schemas
from child maltreatment … a predictive coding framework"*). The
descriptive-vs-predictive distinction, and the use of *generating an effect under
unseen conditions* as a falsification criterion, follow Palminteri, Wyart & Koechlin
(*"The Importance of Falsification in Computational Cognitive Modeling"*, TICS) and
the broader literature on generalization in computational modelling. That a deep
character *is* a predictive model a reader runs — theory of mind, and actions that
must be "an inevitable consequence of their nature" — rests on work on readers'
mental models of characters and on narrative suspense as predictive inference
(Kidd & Castano; Wilmot; and fMRI studies of suspense and social cognition).

These are, as ever, a novelist's uses of the science: the mappings are typologies
of useful defaults, not laws, and every prediction the library makes can be
overridden by the person the author actually has in mind.

## Research lineage

The design rests on Friston (free energy, active inference), Seth (*Being You*),
Barrett (constructed emotion, allostasis), Damasio (somatic markers),
Merleau-Ponty (body schema vs body image), Husserl (retention/protention),
Gazzaniga (the left-brain interpreter), Graziano (attention schema),
Dehaene & Baars (global workspace), Melzack (neuromatrix), Ehrsson & Blanke
(body-ownership illusions), Carhart-Harris & Friston (REBUS), Tononi and Hoel
(integrated information, causal emergence), and Kreminski (Winnow story sifting).

Polyvagal theory and "the body keeps the score" are modelled but flagged: they
are scientifically contested, and SOMA never presents them as consensus.
