# soma.narrative — writing stories without writing loops

The base language asks you to think in loops, precisions, convictions, and
clocks. `soma.narrative` lets you think in **characters, temperaments, feelings,
and beats**, and compiles that down to ordinary SOMA — so every guarantee of the
core language (qualia opacity, affine body budgets, `@consent`) still holds, and
you can inspect, run, sift, prose, and perturb the result exactly as before.

```python
from soma.narrative import Story, anxious

story = Story("bad_news", span="8s", step="0.5s", about="acute distress")

nadia = story.character("Nadia", temperament=anxious)
nadia.senses("ear")                                    # a channel onto the world
nadia.appraises("ear", as_threat=True, drives="heart", to=118,
                when="ear > 3", fades_to=70)           # words drive the heart, which settles
nadia.feels("dread", from_body="heart")                # dread is read off the racing heart
nadia.narrates(downplaying={"dread": "I'm fine. I just need to write this down."})

story.at("2s", nadia.hears("ear", 9))                  # the sentence lands
story.at("5s", nadia.hears("ear", 2))                  # and a quiet she can't return to

print(story.run())        # the dashboard, as text
print(story.source())     # the SOMA it generated (readable, editable)
```

That is a dozen lines of intent in place of forty lines of hand-wired loops, and
it produces the whole scene: the racing heart, the dread that follows it a beat
later (the body knew first), and the lie told before it is known — with the
heart rising when the words land and settling once they pass.

## The whole surface

**`Story(title, span, step, about=None, cadence=False)`** — the container.
- `.character(name, temperament=trusting, clock="body")` → a `Character`
- `.scene(title, frm=, to=)` — a narrative beat spanning a time range
- `.at(t, *events)` — schedule world-events (from `character.hears(...)` / `.shows(...)`)
- `.over(arc, event_fn)` — spread an Arc across the timeline (no hand-written stimulus tables)
- `.consent(note)` — set the distress note (auto-added when a distress feeling is present)
- `.source()` / `.run()` / `.sift()` / `.prose()` / `.perturb(expr)` / `.result()`
- `.predict(who, {channel: value})` — **forecast** a character's response to a
  situation never scripted (suppress / take-in / break); `.tipping_point(who,
  channel)` gives the least evidence that turns their lie. Positive, falsifiable
  predictions, not replays of the timeline (see *Predicting the character*)
- `.characterize()` — a synthesized **portrait**: not what happened, but *who this
  person is* — disposition, what they want and fear, the wound, the lie (and whether
  it is a moral or psychological weakness), which way the arc runs, the need (and
  whether it is reached), the value they break, the feeling they defend against.
  The project's answer to "who is this character," drawn entirely from the record

**`Character`** — verb-methods, each returning `self` so they chain:
- `.senses(channel)` — an exteroceptive channel (a thing heard or seen)
- `.has_body_signal(channel)` — an interoceptive channel (heart, gut)
- `.appraises(channel, as_threat=, drives=, to=, feeling=, when=, updates=, stops_seeing=, effortful=, shows_on=, fades_to=, …)`
  — a loop that reads a channel and reacts; can push the body (`drives`), emit a
  `feeling`, cost the attention spotlight (`effortful`), and surface the feeling
  as a readable tell (`shows_on`, with `fades_to` giving it a resting value)
- `.feels(quale, from_body=, cost=)` — read the body's own state and produce a feeling
- `.reads(other, surface="face", gain=, lag=)` — read another's *surface* (a coupling; never their interior)
- `.remembers(name, cued_by=, when_above=, evokes=)` — a somatic memory (the flashback mechanism)
- `.dissociates_when(appraisal=, exceeds=, detaching=, repair_after=)` — a supervisor that detaches under overload
- `.learns(rate)` — make appraisals harden with use (love curdling, fear compounding)
- `.has_mood(name, fed_by=, relieved_by=, decay=)` — a slow variable that integrates
  feelings and decays: the emotional weather that outlasts any single feeling
- `.has_attention(capacity=)` — a finite spotlight; `effortful` appraisals spend it
  and are *starved* when it runs out (the overwhelmed-can't-think dynamic)
- `.wants(channel, toward=, strength=)` / `.fears(channel, toward=, strength=)` — a
  drive that pulls a channel toward (or away from) a goal. Both on one channel =
  **ambivalence**: drawn and repelled at once, arriving nowhere
- `.values(name, says=, betrayed_when=, on_channel=)` — a principle the character
  holds and the condition under which the body **betrays** it. Character is the gap
- `.part(name, role=, reacts_to=, feeling=, salience=, when=)` — an **internal part**:
  a sub-agent of the psyche that reacts and bids for consciousness. A loud protector
  drowns out a quiet exile, so the exile's feeling is *felt but never known*
- `.with_person(other, feeling=, precision=, conviction=)` — the **relational self**:
  who this character becomes with a specific other. The same person runs different
  dials with different people — open with one, defended with another
- `.craves(name, fed_by=, feeling=, fed_feeling=, erased=, threshold=)` — a **hunger
  the world can feed and charge for**. While the `fed_by` supply is present the
  relief fills and the hunger quiets; but the relief drains at rate `erased`, so a
  hunger has three fates the sift tells apart: fed-and-wiped is an *addiction* (the
  rank the ring erases each night — the loop never opens), never-fed is a *standing
  longing* (the boat Sound is never allowed), and fed-by-a-supply-that-does-not-erase
  is simply *met* (the same hunger, quietly fed by reading — the loop opens)
- `.tended_by(other, calms=)` / `.steadies()` — **co-regulation**: a steady presence
  that turns down the *trust* placed in a distress signal without touching the
  belief. The tended one still sees what they see; they are simply no longer alone
  with it. Presence, not persuasion — the opposite of an argument. `steadies()`
  marks a character as a calm others can lean on (bring them into reach with
  `other.present()` inside `story.at`)
- `.holds_with_others(name, field_tag=, believing=, shocked_at=)` — **confidence as
  belief about other people's belief**. The holder's grip on the belief reads the
  shared field (how much of the group still holds); while the field is full it is
  unshakeable, and when one holder is shocked into letting go the rest cascade —
  far faster than any evidence could move them. The doctrine on the perches, the
  run on war-paper
- `.wounded_by(ghost, teaches=, cued_by=, evokes=)` — the **Ghost/Wound** (Truby): a
  formative past event that still governs the present, and the lie it installed.
  With `cued_by`/`evokes` it also plants a somatic memory, so the wound can fire
  wordlessly long after its story is forgotten
- `.believes(lie, claim=, disconfirmed_by=, feeling=, harms=, conviction=,
  breakable=, says=)` — the **Lie**: a high-conviction belief that reads the very
  evidence that would disconfirm it and suppresses it (self-deception, in SOMA's
  own precision arbitration), hardening with each denial. `harms="self"`
  (psychological weakness) or `"others"` (moral). `breakable=True` (default) lets
  it break, the moment derived automatically from conviction vs. evidence;
  `breakable=None` keeps it — the tragic arc. The lie is spoken, so it makes a
  confabulation gap against the need aching underneath
- `.needs(truth, opposes=, feeling=, fed_feeling=)` — the **Need**: the salve to the
  lie, the opposite of it, *not* fed by getting the want — met only when the lie is
  seen. The want/need collision is the engine of an inner story
- `.adopts(unmet, coping, disconfirmed_by=, conviction=, breakable=)` — instead of
  stating the lie, **predict it from the wound**: an unmet core need plus a coping
  style (`surrender` / `avoidance` / `overcompensation`) forecasts the belief and
  installs it (schema therapy; see *Predicting the character* below)
- `.narrates(voice={...})` or `narrates(downplaying={...})` — a confabulating self that speaks for the loops

## Temperaments set the dials for you

Every character difference is a setting of two numbers — `precision` (trust in
the senses) and `conviction` (trust in the prior). You never touch them directly;
you name a disposition:

| temperament | reads as | precision | conviction | learns |
|---|---|---|---|---|
| `anxious` | the prior of threat usually wins | 0.55 | 0.70 | 0.03 |
| `stoic` | composure is a strong prior; feels cheaply | 0.60 | 0.75 | — |
| `trusting` | believes the senses; easily (well) surprised | 0.90 | 0.25 | — |
| `guarded` | defends the model; slow to update | 0.45 | 0.80 | 0.06 |
| `volatile` | the world hits hard; feelings are expensive | 0.95 | 0.40 | — |
| `numb` | the signal arrives attenuated near the floor | 0.18 | 0.40 | — |
| `tender` | open, unhardened; low conviction | 0.88 | 0.20 | — |
| `hollowed` | the subtracted self: little lands, little is held | 0.15 | 0.12 | — |

Any dial can be overridden per character (`temperament=anxious.tuned(learn=0.05)`)
or per appraisal (`appraises(..., precision=0.33)`).

## Arcs shape a channel over time

Writing `at 1y: 9  at 3y: 2  at 5y: 8 …` by hand is exactly the bookkeeping this
library removes. An `arc` describes the *shape* of change and expands to beats:

```python
from soma.narrative import arc

# a face that varies for 24 years, then the chair is empty
face = arc.wobble(around=5, span="24y", every="2y") + arc.hold(0, at="25y")
for (t, v) in face:
    story.at(t, soren.hears("her_face", v))
```

`arc.wobble`, `arc.ramp`, `arc.fade`, and `arc.hold` compose with `+`.

## The marriage, in full

The `learns()` rate is the whole tragedy of `examples/narrative/a_marriage.py`:
set `updates=True, stops_seeing=True` and a learn rate, and every confirmation of
his model of her raises his conviction until it outranks his senses and the
`ignore` becomes live — he stops taking her in. Turn the learn rate off with a
one-line perturbation and you get two different lives:

```python
story.perturb("appraising_her_face.learn=0.0")
#   VANISHED (only in the original)
#     - precision pathology: 'appraising_her_face' stopped listening …
```

## Mood, attention, and the tell — the weather between the storms

Three additions make longer, subtler narratives possible:

**Mood** is a slow variable that integrates a feeling and decays — how a novel
says a character had *been low for weeks*. No single event; an accumulation.

```python
grandmother.has_mood("desolation", fed_by="dread", decay=0.9)
lover.has_mood("tenderness", fed_by="delight", relieved_by="contempt", decay=0.8)
```

**Attention** is a finite spotlight. Mark appraisals `effortful=True`; when the
spotlight is spent, the loser is *starved* — the "she was too overwhelmed to
think about both" dynamic.

```python
host.has_attention(capacity=3)
host.appraises("guest_a_face", as_threat=True, feeling="shame", effortful=True)
host.appraises("guest_b_face", as_threat=True, feeling="worry", effortful=True)
```

**The tell.** `shows_on` makes a feeling reach a surface another can read;
`fades_to` gives that surface a resting value it decays back toward, so the tell
is transient — a face that gives someone away and then composes itself. This is
what lets a feeling in one character become a signal a second character reads,
which is how the family saga transmits a fear down three generations.

```python
mother.appraises("her_mother's_face", as_threat=True, feeling="dread",
                 shows_on="face", shows_value=8, fades_to=1)
daughter.reads(mother, "face", gain=0.45, lag="1y")
```

## Reading a character, not an event log

The verbs above build a person; `.characterize()` reads one back out. It gathers
the drives that organize them, the value they hold and break, the feeling their
psyche defends against, and whether they changed — and writes it as prose:

```
╭─ CHARACTER ─────────────────────────────────────────────────────╮
│ THE DIPLOMAT
│ Disposition: guarded. Defends the model; slow to update.
│ Torn: wants and fears the same thing (being_known) — drawn and
│ repelled at once, arriving nowhere.
│ Holds: "I would never lie to her." — and breaks it.
│ Mostly felt: apprehension (16 times).
│ The story they told themselves: "It's a fair question. I'll
│ answer it in a moment."
╰─────────────────────────────────────────────────────────────────╯
```

Eight Winnow-S patterns power this, and can be sifted directly: **the thing they
both want and fear** (ambivalence), **the value the body broke** (a stated
principle violated), **the feeling the whole self defends against**, **a mood
that sours** (an emotional climate turning across the run), **the person they
became** (an arc measured, not asserted), **a hunger the world keeps wiping** (an
addiction — fed, erased, fed again), **held in the dark** (co-regulation working:
an alarm quieted by presence, not argument), and **the run** (confidence
collapsing once one holder is seen to let go).

## Worked examples

- `examples/narrative/bad_news.py` — feeling and confabulation (one character)
- `examples/narrative/the_look.py` — two people misreading each other (a coupling)
- `examples/narrative/a_marriage.py` — thirty years, and a prior that hardens (learning)
- `examples/narrative/the_house.py` — **a three-generation saga**: inherited
  trauma transmitted face-to-face down a lineage, with mood carrying a feeling
  across decades, dissociation crashing and repairing, and a single perturbation
  that asks whether the granddaughter can be freed of a fear she never understood
  (`story.perturb("Ada.face.gain=0.03")` makes her unease *vanish*).
- `examples/narrative/the_diplomat.py` — **a character study**: a man who wants
  and fears being known, holds a value about honesty and breaks it under
  pressure, and defends against his own longing. Run `--character` for the portrait.
- `examples/narrative/two_sisters.py` — **character is relational**: two sisters
  at the reading of a will; one composes her resentment, the other misreads the
  composed face. The dual `--character` portrait recovers the gap the plot never states.
- `examples/narrative/the_negotiator.py` — **the most complete character**: a
  hostage negotiator with an internal *protector* who speaks and an *exile* whose
  terror never reaches awareness, a different self with the subject at the door
  than with the colleague in her ear, ambivalence about the rapport that would end
  the standoff, and a candor value she breaks with every composed word. The
  `--character` portrait reads the whole divided psyche, and a single perturbation
  (`Cass.appraising_pressure.precision=0.05`) shows the self-deception was load-bearing.
- `examples/narrative/the_unmooring.py` — **a whole novel's cast**, in five
  studies drawn from *The Unmooring*, each leaning on a primitive the book needed:
  *Ink and Sound* (the spare who reads, and the diver who reads the water — a
  hunger the sift shows *kept fed* by reading, beside a longing the world *will not
  feed*); *Blade in the Blood* (a full divided self — the brave first-over-the-rail
  protector who speaks, the starved animal that never ignites, the rank the
  tide-clean wipes each night, and the fair share he swore and cannot live inside);
  *the Combs* (Topman's grief `tended_by` Rover — quieted by presence, not
  argument); *Greywater* (the run — confidence collapsing the hour one man, Venn,
  reads the paper instead of the crowd, while Quill reads the same rot and holds
  anyway because he is *so tired*); and *the Provost* (the clerk who checked the
  arithmetic three times and then stopped — a value broken, and the honest young
  self that never ignites again). Run any with
  `the_unmooring.py <study> --character|--sift|--source`.

## A divided self: internal parts and the relational self

Two constructs let a character be genuinely *deep* rather than merely reactive.

**Internal parts** are sub-agents that compete for consciousness. A loud protector
(high salience) wins the workspace; a quiet exile (low salience) feels real pain
that never ignites — felt, never known. It is the structure of a defended psyche:

```python
cass.part("the-professional", role="protector", reacts_to="pressure",
          feeling="resolve", salience=0.95, says="Work the problem.")
cass.part("the-child", role="exile", reacts_to="pressure",
          feeling="terror", salience=0.28)   # her fear, and no one hears it
```

**The relational self** makes one person several — a different self, with its own
precision and conviction, for each person they are with:

```python
cass.with_person(subject, feeling="wariness",   precision=0.85, conviction=0.3)
cass.with_person(partner, feeling="tenderness", precision=0.40, conviction=0.7)
```

`characterize()` reads both back: which part speaks and which is never heard, and
who she becomes with whom.

## Hungers, presence, and confidence

Three more constructs, added for *The Unmooring*, model the ways a world gets
inside a person — by feeding a hunger, by sitting beside them, or by making them
believe what everyone else is seen to believe.

**A hunger the world feeds and charges for.** `craves` gives a character a want a
place can supply and withdraw. The single dial `erased` decides whether it is an
addiction or a satisfaction — the same hunger, two fates:

```python
blade.craves("to-matter", fed_by="rank", feeling="worthlessness",
             fed_feeling="pride", erased=0.9)   # the ring wipes it nightly: addiction
ink.craves("to-matter",   fed_by="reading", feeling="worthlessness",
           fed_feeling="recognition", erased=0.0)  # reading does not erase: it quiets
```

**Co-regulation — presence, not persuasion.** `tended_by` turns down the *trust*
in an alarm while a steady other is near, without touching the belief. The tended
one still sees what they see; they are simply no longer alone with it:

```python
rover.steadies()                                     # a calm others can lean on
topman.tended_by(rover, calms="the_children", strength=0.85)
# ... then bring the presence into reach when he sits down:
story.at("8s", rover.present())
```

The grief floods while Topman is alone and goes quiet the moment Rover arrives —
and it is the loop's precision that fell, never its belief. The `held in the dark`
sift finds exactly this shape: an alarm believed, then carried.

**Confidence — belief about other people's belief.** `holds_with_others` gives a
belief whose whole strength is that everyone else is seen to hold it. Give several
characters the same field and shock one, and confidence collapses far faster than
any fact could move it — nothing, nothing, then everything at once:

```python
for who in creditors:
    who.holds_with_others("paper-is-sound", field_tag="holds", believing=10,
                          shocked_at=("5s" if who is venn else None))
```

Under the hood this rests on one small core builtin, `field(tag)`, which reads the
mean of every channel named `tag` across the whole cast — a population read, so a
loop's conviction can track how many others currently hold. The `the run` sift
recovers the cascade.

## The wound, the lie, and the arc

The deepest layer, and the one the craft of fiction is most explicit about
(Truby's *ghost → lie → need*): a formative **wound** teaches a false **lie** the
character adopts to survive it; the lie generates the conscious **want** while
defending against a buried **need**; and whether the lie is ever *seen* is the
**arc**. SOMA builds this on its own machinery — the lie is a high-conviction loop
that reads its own disconfirming evidence and suppresses it, which is exactly
self-deception, and precisely the shape the `precision-pathology` sift already
knew.

```python
blade.wounded_by("the injury-scale that priced him in advance",
                 teaches="only-rank-makes-me-real")
blade.believes("only-rank-makes-me-real",
               claim="If I'm not ranked above them, I'm the surplus again.",
               disconfirmed_by="equal_regard", feeling="worthlessness",
               harms="others", breakable=None,          # he doubles down
               says="Some of us need there to be an upstairs.")
blade.needs("to-matter-as-an-equal", opposes="only-rank-makes-me-real",
            feeling="worthlessness", fed_feeling="belonging")
```

What decides the arc is one core primitive, **`overwhelm`**. A high-conviction
prior can suppress disconfirming evidence forever — true to self-deception, but it
would make a positive arc impossible. `overwhelm` gives the belief a breaking
point: the disconfirming surprise it keeps refusing to look at accumulates, and
once it crosses a threshold the loop is forced to *perceive* — the mechanistic
**self-revelation** (logged as `revelation`). With `breakable=True` (the default)
the threshold is **automatic**, derived from the belief's own strengths
(`conviction / trust-in-evidence`), so a belief held harder resists longer and
*when* it breaks emerges rather than being hand-set. `breakable=None` keeps the lie
— the tragic arc. The `the-lie` sift reports *kept* vs. *seen*; `want-need` reports
whether the need the want could never feed was met.

## Predicting the character

Everything above *models* a character from a specification. `soma.narrative` can
also make **positive predictions** — say something you did not put in. (See
`PREDICTION.md` for the research; the short version: a model earns its name by
generating an effect under conditions it was never given, which is what makes it
falsifiable.)

**Predict the lie from the wound.** `predict_lie(unmet, coping)` (and
`character.adopts(unmet, coping, disconfirmed_by=…)`) forecast the belief a wound
will produce, grounded in schema therapy unified with predictive coding. An unmet
core need (`worth`, `belonging`, `safety`, `connection`, `autonomy`) plus a coping
style (`surrender` / `avoidance` / `overcompensation`) predicts the claim, the
want, whom it harms, and how hard it is held. The same wound, coped three ways, is
three different people:

```python
from soma.narrative import predict_lie
predict_lie("worth", "surrender").claim         # "I am the one who can be done without."
predict_lie("worth", "overcompensation").claim  # "If I am not ranked above them, I am the surplus again."
```

That last is, word for word, the lie the novel gives Blade — so
`blade.adopts("worth", "overcompensation", disconfirmed_by="equal_regard")` rebuilds
his tragic arc from the wound alone.

**Forecast an unscripted response.** `story.predict(who, {channel: value})` runs the
character's own model on a situation that is *not* in the timeline (every authored
stimulus is stripped; they face only the probe) and reports what their arbitration
does — suppress it, take it in, or break. It tells a breakable character from an
unbreakable one on unseen input:

```python
ring.predict("Blade", {"equal_regard": 9})   # -> SUPPRESSES it; the lie holds
fleet.predict("Ink",  {"kept_for_nothing": 9})  # -> BREAKS the lie; a self-revelation
ring.tipping_point("Blade", "equal_regard")   # -> never, in [0, 9] -- the lie is kept
fleet.tipping_point("Ink", "kept_for_nothing")  # -> breaks once evidence >= 3
```

`tipping_point` returns the least sustained evidence that turns a lie — a sharp,
quantitative, falsifiable claim written down nowhere; it falls out of the conviction
dial. `python examples/narrative/the_unmooring.py predictions` collects the cast's
forecasts.

Run any of them with `python examples/narrative/<name>.py`, or add `--source` to
see the SOMA it generated (`--prose` on the saga for free-indirect prose,
`--character` on the studies for the portrait, `predictions` for the forecasts).

