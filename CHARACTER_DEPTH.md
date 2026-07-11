# Deepening the character models — research, and what it changed in SOMA

*This note records (1) what the craft of fiction and the psychology literature say
"character depth" actually is, (2) the gap that opened between that and what SOMA
could express, and (3) the changes made to close it — a new core primitive, three
new narrative verbs, four new sift patterns, a richer portrait, and the deepened
cast models. Everything below is implemented and tested.*

---

## 1. What the research says depth is

Reading across screenwriting craft, novel craft, and the psychology of
self-deception, four ideas recur, and they are strikingly consistent:

- **Dimension = contradiction.** Robert McKee's *Story* puts it flatly: "Dimension
  means contradiction." A round (three-dimensional) character is not a pile of
  traits but a person wrestling opposed forces inside themselves. Everyone from
  ScreenCraft to Reedsy to Katherine Cowley repeats this: the capacity to
  *surprise convincingly* is the mark of roundness (E. M. Forster's original
  test), and surprise-that-is-inevitable comes from hidden contradiction.

- **Want vs. Need.** The conscious **Want** (an external plot goal, pursued
  because the character believes it will make them whole) sits in tension with an
  unconscious **Need** (the psychological or moral change they must actually
  undergo). "The dramatic tension in most stories comes from the collision between
  want and need"; the climax forces a choice, and getting the want never satisfies
  the need. (iWrity; Stage 32; September C. Fawkes.)

- **Ghost → Wound → Lie → Weakness.** John Truby's *The Anatomy of Story* and K. M.
  Weiland's widely-used gloss: a formative past event (the **Ghost**) inflicts a
  **Wound**, from which the character adopts a false belief (the **Lie**) — *"I
  don't deserve love," "vulnerability is weakness"* — that was adaptive once and is
  now a cage. The Lie produces the **Weakness**, which Truby splits into
  **psychological** (harms mainly the self) and **moral** (harms others). The Want
  is generated *by* the Lie.

- **Arc = what happens to the Lie.** A **positive** arc = the character sees and
  abandons the Lie (self-revelation → the Need met). A **negative/tragic** arc =
  they double down and the Lie hardens. A **flat/steadfast** arc = they already
  hold the truth and change the world instead. (Weiland; Fawkes.)

And the psychology underneath the Lie is precise and, it turns out, mechanistic:
**self-deception is a *motivated false belief maintained despite disconfirming
evidence*, by selectively suppressing or discounting that evidence** — "part of
the mind recognises the truth while another endorses the deception," and the
belief breaks only when the evidence becomes *undeniable*. (Stanford Encyclopedia
of Philosophy; ScienceDirect; multiple reviews.)

---

## 2. The gap in SOMA

SOMA already modelled a great deal of this without naming it. Its whole engine is
the gap between a narrator and a body (contradiction); it has ambivalence
(`wants`+`fears` on one channel), internal `part`s (a divided psyche), the
relational self (`with_person`), and `craves` (the Want, in three fates). What it
could **not** express was the spine the craft literature is most insistent about:

- no formal **Need** distinct from the Want;
- no **Lie** — a false belief that *suppresses its own disconfirming evidence* and
  generates the want;
- no **Wound → Lie** origin;
- and, most importantly, **no arc**: SOMA's arbitration rule was
  `perceive if pi_s ≥ pi_p else act`, which means a high-conviction belief
  suppresses disconfirming evidence *forever, no matter how overwhelming*. That is
  true to self-deception up to a point — but it made **self-revelation mechanically
  impossible**, and self-revelation is the hinge of a positive arc.

---

## 3. What changed

### Core language (`soma`): a breaking point for a defended belief

A new, opt-in loop field, **`overwhelm`**, gives a belief a breaking point. While a
loop suppresses disconfirming evidence (routes to `act`), the *disconfirming*
surprise it is refusing to look at (evidence reading higher than the held belief)
accumulates; once the debt crosses a threshold, the loop is forced to `perceive`
for that tick, updates toward the truth, and logs a `revelation` event. This is the
mechanistic **self-revelation** — the lie broken not by argument but by the sheer
weight of what it would not look at. It is fully backward-compatible (`overwhelm`
defaults to 0 = never breaks), is a soft keyword, and is perturbable.

**The threshold can now be automatic.** `overwhelm: auto` (surfaced as
`believes(breakable=True)`, the default) derives the breaking point from the
belief's own strengths rather than an author's number:

> the accumulated disconfirming surprise must exceed **`BREAK_K · conviction /
> trust-in-evidence`** (`BREAK_K · pi_p / pi_s`).

So a belief held harder (higher conviction — *and* the hardening that `learn` adds
on every suppression) resists longer; a belief that trusts its disconfirming
channel less resists longer still; and *when* a lie breaks **emerges** from how
strongly it is held against how strong and trusted the evidence gets, rather than
from a hand-set moment. This is the predictive-processing account made literal:
entrenched high-precision priors down-weight prediction error, and change comes
only as precision-weighted evidence accumulates past what conviction can hold.

### Narrative library (`soma.narrative`): three new verbs

- **`wounded_by(ghost, teaches=, cued_by=, evokes=)`** — the Ghost/Wound, and the
  lie it installed; optionally plants a somatic memory so the wound can fire
  wordlessly.
- **`believes(lie, claim=, disconfirmed_by=, feeling=, harms=, conviction=, breakable=, …)`** —
  the Lie: compiles to a high-conviction loop that reads its disconfirming evidence
  and suppresses it, hardening with each denial. `harms="self"|"others"` marks a
  psychological vs. moral weakness. **`breakable=True`** (the default) makes it break
  *automatically*, the moment emerging from conviction vs. evidence (above);
  `breakable=<number>` pins an absolute threshold; `breakable=None` means it only
  hardens (it is *kept*). The lie is spoken by the narrator — so it automatically
  produces a confabulation gap against the need aching underneath.
- **`needs(truth, opposes=, feeling=, fed_feeling=)`** — the Need: a loop that
  aches the whole time the lie holds and is met *only when the lie is seen* (its
  relief is wired to the lie's own revelation), never by getting the want.

### Four new sift patterns

- **the lie seen** — a breakable lie, overwhelmed at last: the self-revelation, a
  positive arc.
- **the lie kept** — an unbreakable lie that suppressed the evidence to the end and
  only hardened: the tragic arc, the self that doubles down.
- **the need met** — the need answered once the lie broke ("what the want could
  never feed, the truth did").
- **a need the want never feeds** — the want/need collision made explicit: a need
  that ached under everything the want reached for and was never met.

### A richer portrait

`characterize()` now reads the deepest layer straight off the record: *Wounded
by…*, *The lie he believes: "…" (a moral/psychological weakness)*, *Arc: the lie is
seen / kept*, and *Needs (and reaches / never reaches)…*.

---

## 4. The deepened cast — four arcs, measured

The novel's principals were re-modelled with the wound/lie/need layer, and — with
the automatic breaking point — the **timing** of each self-revelation now emerges
from one dial, how hard the lie is held (`conviction`), against when its evidence
arrives. Nothing is hand-set:

| Character | The lie | conviction | Break emerges | Arc |
|-----------|---------|-----------|---------------|-----|
| **Ink** (`fleet`) | "I matter only as the indispensable hand — the one who holds the pen." | 0.95 | **the founding** (~10s) | seen; need *to be kept for nothing* met |
| **Blade** (`ring`) | "If I'm not ranked above them, I'm the surplus again." | held hard (`None`) | **never** | kept; need *to matter as an equal* never met |
| **The Coat** (`coat`) | "I am the number in the collar; the coat is what stops me being surplus." | 0.85 | **the gate** (~18s, when his own acts arrive) | seen; need *to matter as himself* met |
| **The Provost** (`selm`) | "The doctrine is a roof, and a roof need not be true." | 1.5 (hardest) | **last** (~12s, despite early evidence) | seen too late — the pencil |

Ink and Blade are now, precisely, the same wound with conviction thrown two ways —
and `perturb` proves it: raising Ink's lie-conviction alone (`0.95 → 3.0`) lifts the
automatic threshold past what the evidence can reach, flipping his arc from
*seen*/*need met* to *kept*/*need starved*, i.e. turning Ink into Blade. The dial is
load-bearing.

```bash
python3 examples/narrative/the_unmooring.py fleet --character   # Ink: the lie seen
python3 examples/narrative/the_unmooring.py ring  --character    # Blade: the lie kept
python3 -c "import sys; sys.path[:0]=['.','examples/narrative']; import the_unmooring as u; \
print(u.build().perturb('Ink.the_lie_only_the_needed_matter.conviction=3.0'))"
```

---

## 5. On the novel

The novel itself was **not** edited this round. The deepened models were run
against it and they *confirm* its arcs — Ink refuses the pen (seen), Blade takes
the ladder (kept), the Coat holds the gate (seen), the Provost's pencil (seen too
late). As before, the models validate the finished text rather than turning up
work to do in it; the value this round is in the instrument, which is now able to
express — and detect — the deepest layer of character the craft is built on.

*Version at time of writing: SOMA 0.6.0 (current release 0.14.2). This note
records a specific development round; the mechanisms it introduced remain in
place and are documented in their current form in `NARRATIVE.md` and
`PREDICTION.md`. Tutorial has a §5.5 on the wound/lie/need/arc.*
