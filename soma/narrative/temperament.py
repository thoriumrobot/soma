"""
Temperaments: named psychological dispositions that set the low-level dials.

The two numbers that decide a SOMA character's whole behavior are `precision`
(trust in the senses) and `conviction` (trust in the prior). Every difference
between a person who *takes in* the world and one who *imposes on* it is a
setting of those two dials -- but no novelist should have to think in those
terms. A temperament is a name for a point in that space, plus a couple of
related defaults (how fast a prior hardens, how much a feeling costs the body).

    anxious   -- a strong prior that the world is threatening; slow to be reassured
    stoic     -- high trust in the prior of composure; feels, but does not show
    trusting  -- believes the senses; updates readily; easily surprised (well)
    guarded   -- holds the prior tightly; slow to update; defends the model
    volatile  -- swings: high precision AND reactive; the world moves it hard
    numb      -- attenuated precision; the signal arrives but lands softly
    tender    -- low conviction, high precision: open, moved, unhardened

These are starting points. Any field can be overridden per character or per
loop, and `Temperament.tuned(...)` returns a modified copy.
"""
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Temperament:
    """A named disposition. The fields are the dials every loop needs, expressed
    once so the author can name a personality instead of tuning numbers."""
    name: str
    # trust in the senses vs. trust in the prior -- the core arbitration dials
    precision: float = 0.85       # pi_s: how much the senses are believed
    conviction: float = 0.35      # pi_p: how much the prior is believed
    # how quickly a confirmed prior hardens (0 = never; the marriage dial)
    learn: float = 0.0
    # what a strong feeling costs the body's budget, per firing
    feeling_cost: float = 40.0
    # a baseline prediction: what this person expects the world to be
    baseline_expectation: float = 0.0
    # how strongly this person's appraisal reaches down into the body
    somatic_gain: float = 1.0

    def tuned(self, **over):
        """Return a copy with some fields overridden.

            anxious.tuned(learn=0.05, conviction=0.5)
        """
        return replace(self, **over)

    # allow `anxious("Vera")`-style call to feel natural, though characters are
    # usually made via Story.character(...). Returns (self) for fluent use.
    def __call__(self, *_a, **_k):
        return self


# --- the presets -----------------------------------------------------------
# Values are chosen so that, run against a moderate threat stimulus, each
# produces the behavior its name promises. They are documented, not magic:
# `precision >= conviction` perceives (takes the world in); otherwise acts
# (imposes the prior). `learn` slowly raises conviction with each firing.

anxious = Temperament(
    "anxious",
    precision=0.55,          # the senses are heard, but...
    conviction=0.7,          # ...the prior ("something is wrong") usually wins
    learn=0.03,              # and every alarm makes the next one easier
    feeling_cost=55.0,
    baseline_expectation=6.0,  # expects the world to be threatening
    somatic_gain=1.3,
)

stoic = Temperament(
    "stoic",
    precision=0.6,
    conviction=0.75,         # composure is a strong prior
    learn=0.0,
    feeling_cost=30.0,       # feels, cheaply -- it does not flood
    baseline_expectation=0.0,
    somatic_gain=0.7,
)

trusting = Temperament(
    "trusting",
    precision=0.9,           # believes what it senses
    conviction=0.25,         # holds its own model loosely
    learn=0.0,               # and does not harden
    feeling_cost=40.0,
    baseline_expectation=0.0,
    somatic_gain=1.0,
)

guarded = Temperament(
    "guarded",
    precision=0.45,
    conviction=0.8,          # defends the model; slow to update
    learn=0.06,              # and hardens with use
    feeling_cost=45.0,
    baseline_expectation=3.0,
    somatic_gain=1.0,
)

volatile = Temperament(
    "volatile",
    precision=0.95,          # the world hits hard...
    conviction=0.4,          # ...and the prior is not strong enough to damp it
    learn=0.0,
    feeling_cost=65.0,       # and the feelings are expensive
    baseline_expectation=2.0,
    somatic_gain=1.6,
)

numb = Temperament(
    "numb",
    precision=0.18,          # the signal is attenuated near the floor
    conviction=0.4,
    learn=0.0,
    feeling_cost=15.0,
    baseline_expectation=0.0,
    somatic_gain=0.4,
)

tender = Temperament(
    "tender",
    precision=0.88,
    conviction=0.2,          # open, unhardened
    learn=0.0,
    feeling_cost=40.0,
    baseline_expectation=0.0,
    somatic_gain=1.1,
)

hollowed = Temperament(
    "hollowed",
    # both dials near the floor: the world barely lands (low precision) and
    # nothing is firmly held (low conviction). This is the subtracted self --
    # the one the world has slowly emptied: the keeper of names worn down to
    # her rounds, the captain in the mist who can no longer tell the shown from
    # the so, the wax-dead who were tired and said yes. Not numb (numb still
    # holds a prior); hollowed holds almost nothing, and almost nothing reaches
    # it, so it neither floods nor defends -- it simply thins.
    precision=0.15,
    conviction=0.12,
    learn=0.0,
    feeling_cost=12.0,
    baseline_expectation=0.0,
    somatic_gain=0.5,
)

TEMPERAMENTS = {
    t.name: t for t in (anxious, stoic, trusting, guarded, volatile, numb,
                        tender, hollowed)
}
