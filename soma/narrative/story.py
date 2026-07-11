"""
The Story/Character builder.

A `Story` is a container for characters, a timeline of events, and narrative
beats. A `Character` records what a person senses, appraises, feels, and says --
in dramatic terms -- and the builder turns all of it into ordinary SOMA source.

Nothing here re-implements the interpreter. `Story.source()` produces text that
`soma.parse` accepts, and `Story.run()` / `.sift()` / `.prose()` / `.perturb()`
call straight through to the base toolchain, so behavior is identical to a
hand-written program and every guarantee (qualia opacity, affine budgets,
@consent) still holds.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import re

from .temperament import Temperament, trusting


def _ident(s: str) -> str:
    """A safe SOMA identifier from a human name (hyphens, spaces -> underscore)."""
    return re.sub(r"\W+", "_", str(s)).strip("_")


def _num_probe(x):
    return str(int(x)) if isinstance(x, float) and x.is_integer() else str(x)


@dataclass
class Prediction:
    """A positive, falsifiable forecast of how a character meets a situation the
    author never scripted. `route` is what their arbitration does with it --
    `suppress` (defend the belief against it), `take-in` (let it update them),
    `unmoved` (it doesn't reach them); `breaks_lie` names a lie the situation
    overwhelms, if any. The claim is falsifiable in the strong sense: run the same
    situation and the model must produce this effect, or it is wrong."""
    who: str
    stimulus: dict
    route: str
    breaks_lie: Optional[str]
    break_time: Optional[float]
    feelings: list
    detail: dict

    def render(self) -> str:
        stim = ", ".join(f"{k} at {_num_probe(v)}" for k, v in self.stimulus.items())
        head = f"Prediction — {self.who} faced with {stim} (never scripted):"
        if self.breaks_lie:
            body = (f"  it BREAKS the lie '{self.breaks_lie.replace('the_lie_', '').replace('_', ' ')}'"
                    f" at ~{self.break_time:.0f}s — a self-revelation.")
        elif self.route == "suppress":
            body = ("  they SUPPRESS it — the belief holds, the evidence is defended "
                    "against. No change.")
        elif self.route == "take-in":
            body = "  they TAKE IT IN — it lands and moves them."
        elif self.route == "unmoved":
            body = "  it does not reach them — below what would move this person."
        else:
            body = f"  a mixed response ({self.detail})."
        feel = (f"\n  felt: {', '.join(self.feelings)}." if self.feelings else "")
        return head + "\n" + body + feel

    def __str__(self):
        return self.render()


# a sensible clock for each kind of process, so the author never types @cardiac
_CLOCK_FOR = {
    "instant": "neural", "body": "cardiac", "breath": "breath",
    "mood": "mood", "day": "circadian", "life": "biography",
    "generations": "lineage",
}


_TEMPERAMENT_GLOSS = {
    "anxious": "The prior that something is wrong usually outranks the evidence.",
    "stoic": "Composure is a strong prior; feels, but does not flood.",
    "trusting": "Believes the senses, holds its own model loosely, is well surprised.",
    "guarded": "Defends the model; slow to update; hardens with use.",
    "volatile": "The world hits hard, and the prior is not strong enough to damp it.",
    "numb": "The signal arrives attenuated, near the floor; it lands softly.",
    "tender": "Open and unhardened; low conviction, easily moved.",
}


def _temperament_gloss(name):
    return _TEMPERAMENT_GLOSS.get(name, "")


@dataclass
class _Sense:
    channel: str
    modality: str            # extero | intero | proprio
    baseline: float = 0.0
    kind: str = "Signal"


@dataclass
class _Appraisal:
    name: str
    sense: str
    threat: bool
    precision: float
    conviction: float
    learn: float
    drives_body: Optional[str]
    drives_to: float
    feeling: Optional[str]
    spends: bool
    when: Optional[str] = None
    updates: bool = False        # revise belief toward the sensed value
    stops_seeing: bool = False   # add `ignore` -- becomes active once conviction wins
    effortful: bool = False      # deliberate mode -- must spend the attention spotlight
    shows_on: Optional[str] = None   # a surface channel this appraisal drives (the tell)
    shows_value: float = 8.0
    expects: Optional[float] = None   # explicit prior; None -> temperament default


@dataclass
class _Feeling:
    quale: str
    from_channel: str
    precision: float
    conviction: float
    cost: float
    resting: float = 70.0    # the body's calm value for this channel
    threshold: float = 85.0  # the feeling only arises when the signal exceeds this


@dataclass
class _Reading:
    other: str
    their_surface: str
    my_channel: str
    gain: float
    lag: str


@dataclass
class _Memory:
    name: str
    cue: str
    threshold: float
    evokes: str


@dataclass
class _Dissociation:
    watches: str
    tolerance: float
    modality: str
    repair_after: str


@dataclass
class _Mood:
    name: str
    integrates: list        # list[(feeling_name, weight)]
    decay: float


@dataclass
class _Attention:
    name: str
    capacity: float


@dataclass
class _Drive:
    """A wanting or a fearing: an allostatic pull on a channel toward a goal (or
    away from a dreaded state). Two drives on one channel = ambivalence."""
    name: str
    channel: str
    toward: float
    gain: float
    kind: str               # "want" | "fear"


@dataclass
class _Value:
    """A principle the character holds, and the condition under which the body
    betrays it. Character is the gap between the two."""
    name: str
    stated: str             # the line they'd say ("I would never lie to her")
    betrayed_when: str      # a condition expression that, when true, is the betrayal
    on_channel: str         # the channel the condition reads


@dataclass
class _Part:
    """An internal part -- a sub-agent of the psyche (a protector, an exile, a
    critic). Each part bids for consciousness with a salience; a loud protector
    can drown out a quiet exile, so the exile's pain is felt but never known.
    Named for the structure of a divided self (IFS, ego-state theory)."""
    name: str
    role: str                # "protector" | "exile" | "critic" | free text
    channel: str             # what the part reacts to
    feeling: str             # what the part feels
    salience: float          # how loudly it bids for consciousness
    says: Optional[str]      # the part's voice, if it reaches awareness
    when: Optional[str] = None


@dataclass
class _Relation:
    """The relational self: who this character becomes with a specific other.
    The same person runs different precision/conviction with different people --
    open with one, guarded with another -- so 'who they are' is really a family
    of selves indexed by whom they are with."""
    other: str               # the name of the person this self is for
    channel: str             # the channel read from that person
    feeling: str
    precision: float
    conviction: float
    says: Optional[str] = None


@dataclass
class _Craving:
    """A hunger fed by an external supply, whose relief drains away -- so it
    must be fed again. This is the shape of every dependency a place can sell:
    a rank the ring erases each night, a coat that ends being surplus, a comb
    where the wage and the want are the same substance. The world supplies the
    relief; the relief decays; the hunger returns; the supplier is needed again.
    When `erased` is high the relief is wiped almost as fast as it is granted --
    an addiction rather than a satisfaction, because the loop never opens."""
    name: str
    supply: str              # the world-channel that, when present, feeds it
    feeling: str             # what the unfed hunger feels
    relief: str              # the satisfaction channel the supply fills
    fed_feeling: Optional[str]  # what being fed feels like (the hit), if named
    gain: float              # how fast the supply fills the relief
    erased: float            # how fast the relief drains back to empty (0..1)
    threshold: float         # relief below this -> the hunger is felt
    says: Optional[str] = None


@dataclass
class _Tending:
    """Co-regulation: a steady presence that quiets another's distress without
    arguing it away. The tended character still sees what they see (the belief
    is untouched); but while the steady partner is present and calm, the trust
    placed in the distress signal is turned down, so the alarm stops flooding.
    This is the book's whole thesis -- Rover's biscuit, the grip in the dark,
    'no one alone in the dark' -- presence, not persuasion. The opposite of an
    argument, which changes the belief and reaches only those not yet stuck."""
    other: str               # the steady partner
    channel: str             # the incoming calm-surface channel (a coupling)
    calms: str               # the distress loop whose precision is attenuated
    strength: float          # how much presence lowers the distress precision
    gain: float
    lag: str


@dataclass
class _Confidence:
    """A belief held not because the world shows it but because everyone else
    is seen to hold it -- confidence, in the book's exact sense: belief about
    other people's belief. Its conviction reads the *field*: how much of the
    group is currently holding. While the field is full the belief is
    unshakeable; but it is hollow, and when enough others are seen to let go it
    collapses far faster than any evidence could move it. The doctrine on the
    perches, the soundness of war-paper, the run on a bank: one animal."""
    name: str
    tag: str                 # the shared field all holders expose and read
    belief: float            # the value held (the 'sound' price, the doctrine)
    conviction_floor: float  # conviction when the field is empty (alone)
    conviction_ceil: float   # conviction when the field is full (everyone holds)
    shock_at: Optional[str] = None   # time an exogenous doubt hits this holder
    says: Optional[str] = None


@dataclass
class _Wound:
    """The Ghost, in the craft sense (Truby): a formative past event that still
    governs the present. It is not a live loop; it is the origin the Lie was
    adopted to survive. Optionally it plants a somatic memory, so the wound can
    fire wordlessly in the body long after the story that made it is forgotten."""
    ghost: str                 # the event that still runs the present
    teaches: Optional[str]     # the lie it installed (a _Lie name), if any


@dataclass
class _Lie:
    """The false belief a character adopts to survive the wound, and then can no
    longer see past (Truby's Lie; the psychology of self-deception). It is a
    high-conviction loop that reads the very evidence that would disconfirm it and
    -- because conviction outranks that evidence -- suppresses it, again and again.
    That suppression is the self-deception. If the lie is `breakable`, the raw
    weight of what it will not look at accumulates until it *overwhelms* the
    conviction and the loop is forced to perceive: the self-revelation, and the
    turn of a positive arc. If it is not breakable, it only hardens: the negative
    arc, the tragic self who doubles down. The lie also generates the want and
    defends against the feeling underneath, so getting the want never heals it --
    only seeing it does."""
    name: str
    claim: str                 # the false belief, in the character's own words
    evidence: str              # the life-channel that (dis)confirms the lie
    expects: float             # what the lie predicts that channel reads (low)
    threshold: float           # evidence below this -> the defended ache fires
    conviction: float          # how hard it is held (high = strong self-deception)
    learn: float               # how much each suppression hardens it
    overwhelm: float           # weight of evidence that breaks it (0 = never: kept)
    overwhelm_auto: bool = False  # derive the breaking point from conviction vs
                               # evidence, with no author number (the principled mode)
    feeling: str = "worthlessness"  # the ache the lie defends against
    harms: str = "self"        # "self" (psychological) or "others" (moral) weakness
    says: Optional[str] = None


@dataclass
class _Need:
    """What the character actually needs to become whole -- the opposite of the
    Lie, the salve to the wound (Truby's Need). It is unconscious and resisted:
    it aches the whole time the lie holds, and it is *not* fed by getting the
    want (that is the want/need collision at the heart of an inner story). It is
    met only when the lie is seen -- so its relief is wired to the lie's own
    self-revelation."""
    name: str
    truth: str                 # the thing actually needed (opposite of the lie)
    seen_channel: str          # goes high when the lie is seen (its revelation)
    feeling: str               # the ache of the unmet need
    fed_feeling: Optional[str]  # what being met feels like
    opposes: Optional[str]     # the lie it answers
    says: Optional[str] = None


class Character:
    """A person in a story. Verb-methods record dramatic intent; the Story
    compiles them. Most methods return `self`, so calls chain."""

    def __init__(self, story: "Story", name: str, temperament: Temperament,
                 clock: str = "body"):
        self.story = story
        self.name = name
        self.temp = temperament
        self.clock = _CLOCK_FOR.get(clock, clock)
        self._senses: list[_Sense] = []
        self._appraisals: list[_Appraisal] = []
        self._feelings: list[_Feeling] = []
        self._readings: list[_Reading] = []
        self._memories: list[_Memory] = []
        self._dissoc: list[_Dissociation] = []
        self._moods: list[_Mood] = []
        self._attention: Optional[_Attention] = None
        self._drives: list[_Drive] = []
        self._values: list[_Value] = []
        self._parts: list[_Part] = []
        self._relations: list[_Relation] = []
        self._cravings: list[_Craving] = []
        self._tendings: list[_Tending] = []
        self._confidences: list[_Confidence] = []
        self._wounds: list[_Wound] = []
        self._lies: list[_Lie] = []
        self._needs: list[_Need] = []
        self._lie_predictions: dict = {}   # lie name -> PredictedLie (if derived)
        self._budget: Optional[float] = None
        self._narrator: Optional[dict] = None
        self._body_channels: dict[str, float] = {}
        self._surface_decays: dict[str, float] = {}   # surface -> baseline it fades to

    # ---- what the character can sense --------------------------------------
    def senses(self, channel: str, *, kind: str = "Signal",
               baseline: float = 0.0):
        """An exteroceptive channel onto the world -- a thing they can hear or see."""
        self._add_sense(channel, "extero", baseline, kind)
        return self

    def has_body_signal(self, channel: str, *, baseline: float = 0.0,
                        kind: str = "Signal"):
        """An interoceptive channel: a signal from inside the body (heart, gut)."""
        self._body_channels[channel] = baseline
        self._add_sense(channel, "intero", baseline, kind)
        return self

    # ---- appraisal: a loop that reacts -------------------------------------
    def appraises(self, channel: str, *, as_threat: bool = False,
                  drives: Optional[str] = None, to: float = 100.0,
                  feeling: Optional[str] = None, when: Optional[str] = None,
                  precision: Optional[float] = None,
                  conviction: Optional[float] = None,
                  learn: Optional[float] = None,
                  updates: bool = False, stops_seeing: bool = False,
                  effortful: bool = False, shows_on: Optional[str] = None,
                  shows_value: float = 8.0, fades_to: Optional[float] = None,
                  expects: Optional[float] = None):
        """A loop that reads a channel and reacts. Temperament sets the dials
        unless overridden. `drives` names a body channel the appraisal pushes
        (appraisal reaching into physiology); `feeling` is emitted when it fires.

        `updates=True` revises the belief toward what was sensed (taking the
        world in). `stops_seeing=True` adds an `ignore` -- inert while the senses
        win, but the moment a hardening prior (`learn`) outranks them, the
        character stops taking the world in. Together with `learn`, that is how
        a love curdles into certainty: set updates=True, stops_seeing=True, and
        a learn rate.

        `shows_on` makes the feeling reach a surface channel -- a tell the world
        can read. `fades_to` gives that surface a resting value it decays back
        toward, so the tell is transient (a face composes itself again), which is
        what makes the surface a *signal* another can read rather than a constant."""
        t = self.temp
        name = f"appraising_{channel}"
        # a character may appraise the same channel two ways (delight at her
        # face, and grief at its absence). Disambiguate the second and later
        # loops by their feeling, so the names never collide.
        existing = {a.name for a in self._appraisals}
        if name in existing:
            suffix = feeling or f"{len(self._appraisals)}"
            name = f"appraising_{channel}_{suffix}"
            while name in existing:
                name += "_x"
        if drives:
            self._ensure_body_channel(drives)
        self._appraisals.append(_Appraisal(
            name=name, sense=channel, threat=as_threat,
            precision=t.precision if precision is None else precision,
            conviction=t.conviction if conviction is None else conviction,
            learn=t.learn if learn is None else learn,
            drives_body=drives, drives_to=to,
            feeling=feeling, spends=bool(feeling), when=when,
            updates=updates, stops_seeing=stops_seeing, effortful=effortful,
            shows_on=shows_on, shows_value=shows_value, expects=expects))
        if shows_on:
            self._expose_surface(shows_on)
            if fades_to is not None:
                self._surface_decays[shows_on] = fades_to
        # `fades_to` also applies to a body channel the appraisal drives: a
        # racing heart settles back toward rest once the threat passes, so the
        # spike is an event with a shape, not a permanent new floor.
        if drives and fades_to is not None:
            self._surface_decays[drives] = fades_to
        # An effortful appraisal needs a spotlight to spend; if the author asked
        # for one but never called has_attention(), give them a default rather
        # than silently ignoring `effortful=True`.
        if effortful and self._attention is None:
            self.has_attention()
        # make sure the sensed channel exists
        if not any(s.channel == channel for s in self._senses):
            self._add_sense(channel, "extero", t.baseline_expectation, "Signal")
        return self

    # ---- feeling: viscera -> a quale ---------------------------------------
    def feels(self, quale: str, *, from_body: str = "heart",
              when_body: str = "alarmed", cost: Optional[float] = None,
              resting: float = 70.0, threshold: float = 85.0):
        """The character reads its own bodily state and produces a feeling. The
        feeling arises only when the body signal climbs past `threshold` (a
        racing heart, not merely a beating one) -- so the feeling is an event,
        and it follows the body rather than arriving with the news."""
        # a body channel a feeling reads should rest at `resting`, not 0. Set it
        # explicitly so an earlier appraisal `drives=` didn't pin it to a floor.
        self._body_channels[from_body] = resting
        self._set_channel_baseline(from_body, resting)
        c = self.temp.feeling_cost if cost is None else cost
        self._feelings.append(_Feeling(
            quale=quale, from_channel=from_body,
            precision=min(1.0, self.temp.precision + 0.1),
            conviction=self.temp.conviction, cost=c,
            resting=resting, threshold=threshold))
        if self._budget is None:
            self._budget = 900.0
        return self

    # ---- reading another mind (a couple) -----------------------------------
    def reads(self, other: "Character", surface: str = "face", *,
              gain: float = 0.9, lag: str = "1s", into: Optional[str] = None):
        """Read another character's *surface* (never their interior). Creates a
        coupling: their `surface` becomes a channel this character senses, late
        and attenuated."""
        my_channel = into or f"{other.name.lower()}_{surface}"
        self._add_sense(my_channel, "extero", 5.0, "Expression")
        # ensure the other character exposes that surface as a proprio channel
        other._expose_surface(surface)
        self._readings.append(_Reading(
            other=other.name, their_surface=surface,
            my_channel=my_channel, gain=gain, lag=lag))
        return self

    # ---- somatic memory ----------------------------------------------------
    def remembers(self, name: str, *, cued_by: str, when_above: float,
                  evokes: str):
        """A body-memory keyed to a cue channel, firing a feeling with no
        episodic story attached (the flashback mechanism)."""
        if not any(s.channel == cued_by for s in self._senses):
            self._add_sense(cued_by, "extero", 0.0, "Signal")
        self._memories.append(_Memory(name, cued_by, when_above, evokes))
        return self

    # ---- dissociation ------------------------------------------------------
    def dissociates_when(self, *, appraisal: str, exceeds: float = 5.0,
                         detaching: str = "interoception",
                         repair_after: str = "20d"):
        """When the named appraisal's error exceeds a tolerance, detach a whole
        modality (dissociation), repairing slowly.

        The watched appraisal must be able to *produce* an error that large.
        Since error = precision x (sense - belief), a low-precision temperament
        (e.g. `numb`) attenuates the error below any useful threshold and the
        crash would never fire. So we make sure the watched appraisal senses
        sharply enough for the author's threshold to be reachable -- the
        dissociation is precisely what protects a person who does feel the blow.
        """
        watches = appraisal if appraisal.startswith("appraising_") \
            else f"appraising_{appraisal}"
        base = watches[len("appraising_"):]
        for a in self._appraisals:
            if a.name == watches:
                # need precision high enough that a plausible signal clears the
                # threshold; assume signals reach ~10, so precision >= exceeds/8
                need = min(0.98, max(a.precision, (exceeds / 8.0) + 0.15))
                a.precision = need
                break
        self._dissoc.append(_Dissociation(
            watches=watches, tolerance=exceeds,
            modality=detaching, repair_after=repair_after))
        return self

    # ---- learning ----------------------------------------------------------
    def learns(self, rate: float = 0.05):
        """Make appraisals harden with use (love curdling, fear compounding)."""
        self.temp = self.temp.tuned(learn=rate)
        for a in self._appraisals:
            a.learn = rate
        return self

    # ---- mood: a slow variable that outlasts any single feeling ------------
    def has_mood(self, name: str, *, fed_by, relieved_by=None,
                 decay: float = 0.9):
        """A mood integrates feelings over time and decays -- the emotional
        weather that persists after a feeling has passed. `fed_by` is a feeling
        (or list) that raises it; `relieved_by` lowers it.

            grandmother.has_mood("grief", fed_by="reaching", relieved_by="relief")

        Moods are what let a novel say a character 'had been low for weeks': no
        single event, but an accumulation. They also drive contrast -- a mood can
        be *relieved* by a quale, not only fed by one."""
        fed = [fed_by] if isinstance(fed_by, str) else list(fed_by)
        integ = [(f, 1.0) for f in fed]
        if relieved_by:
            rel = [relieved_by] if isinstance(relieved_by, str) else list(relieved_by)
            integ += [(r, -0.6) for r in rel]
        self._moods.append(_Mood(name=name, integrates=integ, decay=decay))
        return self

    # ---- attention: a spotlight that deliberation exhausts -----------------
    def has_attention(self, capacity: float = 4.0):
        """Give the character a finite attention spotlight. Appraisals marked
        `effortful=True` must spend it to act; when it is exhausted, they are
        starved -- the dramatic 'she was too overwhelmed to think straight'."""
        self._attention = _Attention(name=f"{self.name}_spotlight",
                                     capacity=capacity)
        return self

    # ---- wanting and fearing: the drives that organize a character ----------
    def wants(self, channel: str, *, toward: float = 9.0, strength: float = 0.3,
              baseline: float = 5.0):
        """A drive that pulls a channel toward a wished-for state. `wants` and
        `fears` on the SAME channel produce ambivalence: the character is drawn
        and repelled at once, and settles nowhere -- the engine of most fiction.

            ana.wants("closeness", toward=9)     # to be close
            ana.fears("closeness", toward=1)     # and to be safe
        """
        self._ensure_body_channel(channel, baseline=baseline)
        self._drives.append(_Drive(name=f"{self.name}_wants_{channel}",
                                   channel=channel, toward=toward,
                                   gain=strength, kind="want"))
        return self

    def fears(self, channel: str, *, toward: float = 1.0, strength: float = 0.3,
              baseline: float = 5.0):
        """A drive that pushes a channel away from a dreaded state (toward a
        safe value). Paired with `wants` on the same channel, it is avoidance in
        tension with approach."""
        self._ensure_body_channel(channel, baseline=baseline)
        self._drives.append(_Drive(name=f"{self.name}_fears_{channel}",
                                   channel=channel, toward=toward,
                                   gain=strength, kind="fear"))
        return self

    # ---- a value, and the condition of its betrayal ------------------------
    def values(self, name: str, *, says: str, betrayed_when: str,
               on_channel: Optional[str] = None):
        """A principle the character holds -- and the condition under which the
        body betrays it. Character is not the value; it is the *gap* between the
        value and the act. When `betrayed_when` (a condition on a channel) goes
        true, Winnow-S flags the hypocrisy the character cannot see in themselves.

            rader.values("honesty", says="I would never lie to her.",
                         betrayed_when="composure > 6", on_channel="composure")
        """
        chan = on_channel or betrayed_when.split()[0]
        # make sure the condition's channel exists so the loop can read it
        if not any(s.channel == chan for s in self._senses):
            self._add_sense(chan, "intero", 0.0, "Signal")
        self._values.append(_Value(name=name, stated=says,
                                    betrayed_when=betrayed_when, on_channel=chan))
        return self

    # ---- internal parts: a divided psyche ----------------------------------
    def part(self, name: str, *, role: str = "part", reacts_to: str,
             feeling: str, salience: float = 0.5, says: Optional[str] = None,
             when: Optional[str] = None, baseline: float = 0.0):
        """An internal part -- a sub-agent of the self that reacts to something
        and bids for consciousness at a given `salience`. A loud *protector*
        (high salience) can drown out a quiet *exile* (low salience), so the
        exile's pain is felt but never reaches awareness -- the structure of a
        divided psyche.

            self.part("the-manager", role="protector", reacts_to="criticism",
                      feeling="contempt", salience=0.95, says="I don't need anyone.")
            self.part("the-child",   role="exile",     reacts_to="criticism",
                      feeling="shame",    salience=0.30, says="I'm sorry, I'm sorry.")

        Both hear the same criticism; the manager wins the workspace and the
        child's shame never ignites. Winnow-S's 'never ignited' pattern finds it.
        """
        if not any(s.channel == reacts_to for s in self._senses):
            self._add_sense(reacts_to, "extero", baseline, "Signal")
        self._parts.append(_Part(name=name, role=role, channel=reacts_to,
                                 feeling=feeling, salience=salience,
                                 says=says, when=when))
        return self

    # ---- the relational self: a different person with different people ------
    def with_person(self, other: "Character", *, reading: str = "face",
                    feeling: str, precision: Optional[float] = None,
                    conviction: Optional[float] = None,
                    says: Optional[str] = None, gain: float = 0.8,
                    lag: str = "1s"):
        """Who this character *becomes* with a specific other. Sets up a reading
        of that person (a coupling) plus a self that runs its own precision and
        conviction -- open and trusting with one person, guarded and defended
        with another. 'Who they are' becomes a family of selves indexed by whom
        they are with, which is the deepest truth of characterization.

            cass.with_person(mother,  feeling="shame",     precision=0.9, conviction=0.2)
            cass.with_person(lover,   feeling="tenderness", precision=0.4, conviction=0.7)
        """
        # read the other's surface (a coupling), landing on a per-person channel
        into = f"{other.name.lower()}_{reading}"
        self.reads(other, reading, gain=gain, lag=lag, into=into)
        t = self.temp
        self._relations.append(_Relation(
            other=other.name, channel=into, feeling=feeling,
            precision=t.precision if precision is None else precision,
            conviction=t.conviction if conviction is None else conviction,
            says=says))
        return self

    # ---- a hunger fed by a supply the world sells --------------------------
    def craves(self, name: str, *, fed_by: str, feeling: str,
               fed_feeling: Optional[str] = None, gain: float = 0.6,
               erased: float = 0.0, threshold: float = 5.0,
               says: Optional[str] = None):
        """A hunger the world can feed and then charge for the feeding.

        `fed_by` is a supply channel; while it is present the `relief` fills and
        the hunger quiets. But relief drains at rate `erased`, so the supply is
        needed again -- and if `erased` is high the relief is wiped almost as
        fast as it is granted, which is the difference between a satisfaction and
        an addiction. This is Blade's rank, wiped by the tide-clean each night so
        he must win it again at dawn; the coat that ends being surplus; the Hive
        where the wage and the want are the same substance and the loop never
        opens. Set `fed_feeling` to name the hit (what being fed feels like).

            blade.craves("to-matter", fed_by="rank", feeling="worthlessness",
                         fed_feeling="pride", erased=0.9)   # the ring erases it nightly
        """
        relief = f"{name}_relief"
        # the supply the world offers, and the relief it fills, are channels
        if not any(s.channel == fed_by for s in self._senses):
            self._add_sense(fed_by, "extero", 0.0, "Supply")
        self._ensure_body_channel(relief, baseline=0.0)
        # (the erasure -- relief draining back toward empty -- is emitted by the
        # compiler as a flow whose time constant is set by `erased`.)
        self._cravings.append(_Craving(
            name=name, supply=fed_by, feeling=feeling, relief=relief,
            fed_feeling=fed_feeling, gain=gain, erased=erased,
            threshold=threshold, says=says))
        if self._budget is None:
            self._budget = 900.0
        return self

    # ---- co-regulation: a steady presence, not an argument -----------------
    def tended_by(self, other: "Character", *, calms: str,
                  reading: str = "steadiness", strength: float = 0.7,
                  gain: float = 0.9, lag: str = "1s"):
        """Be co-regulated by a steady other. While `other` is present and calm,
        the trust this character places in a distress signal is turned down, so
        the alarm stops flooding -- *without* changing what they believe. They
        still see what they see; they are simply no longer alone with it.

        This is the opposite of `argues`/appraisal-persuasion: it does not touch
        the belief, only the precision on the distress. It is Rover sitting in
        the Combs, Sound's grip in the black galleries, the watch that leaves no
        one alone in the dark. `calms` names the distress loop (or the channel it
        senses) whose precision the presence attenuates.

            topman.tended_by(rover, calms="appraising_grief", strength=0.8)
        """
        into = f"{other.name.lower()}_{reading}"
        # read the steady one's calm surface (a real coupling, late+attenuated)
        self.reads(other, reading, gain=gain, lag=lag, into=into)
        # steadiness rests at zero when the steady one is absent -- presence has
        # to arrive for it to matter, so the co-regulation has a before and after.
        self._set_channel_baseline(into, 0.0)
        other._set_channel_baseline(reading, 0.0)
        loop = calms if calms.startswith("appraising_") or calms.startswith("feeling_") \
            else f"appraising_{calms}"
        self._tendings.append(_Tending(
            other=other.name, channel=into, calms=loop,
            strength=strength, gain=gain, lag=lag))
        return self

    def steadies(self, *, on: str = "steadiness", value: float = 8.0,
                 always: bool = False):
        """Declare that this character can be a steady presence others lean on --
        exposing a calm surface a `tended_by` couples in. By default the presence
        is *scheduled*: use `character.shows("steadiness", 8)` in `story.at(...)`
        to bring them into reach (Rover sits down on the third day), so the
        co-regulation has a before and an after. Pass `always=True` for someone
        steady by constitution, whose calm is simply always available."""
        self._expose_surface(on)
        self._set_channel_baseline(on, 0.0)   # rests absent until they arrive
        if always:
            self._steady_surface = (on, value)
        return self

    def present(self, *, on: str = "steadiness", value: float = 8.0):
        """A scheduling event: this steady character is now in reach. Use inside
        `story.at(...)`, like `hears`/`shows`. Equivalent to showing the calm
        surface high -- the moment the biscuit arrives."""
        return self.shows(on, value)

    # ---- confidence: a belief held because others are seen to hold it -------
    def holds_with_others(self, name: str, *, field_tag: str, believing: float = 10.0,
                          alone: float = 0.1, together: float = 1.1,
                          shocked_at: Optional[str] = None,
                          says: Optional[str] = None):
        """Hold a belief whose whole strength is that everyone else is seen to
        hold it -- confidence in the book's exact sense: belief about other
        people's belief. Its conviction reads the shared `field_tag`; while the
        field is full the belief is unshakeable, and when the field thins it
        collapses far faster than evidence could move it.

        Give several characters the same `field_tag` and one of them a
        `shocked_at` time, and you get a cascade: the doctrine on the perches,
        the run on war-paper, the market that unfreezes the hour one man acts.

            for who in banks:
                who.holds_with_others("paper-is-sound", field_tag="holds",
                                      shocked_at=("3s" if who is venn else None))
        """
        # the holder's own holding lives on the shared field channel, high while
        # it holds; every other holder reads it (and it reads them) via field().
        self._ensure_body_channel(field_tag, baseline=believing)
        # a private, persistent doubt: 0 while the holder holds, driven to 1 by
        # an exogenous shock (the first mover, the stray fact). Once doubting,
        # this holder lets go for good, thinning the field for everyone else.
        doubt = f"{name}_doubt"
        self._ensure_body_channel(doubt, baseline=0.0)
        self._confidences.append(_Confidence(
            name=name, tag=field_tag, belief=believing,
            conviction_floor=alone, conviction_ceil=together,
            shock_at=shocked_at, says=says))
        if shocked_at is not None:
            self.story.at(shocked_at, (self, doubt, 1.0))
        return self

    # ---- the wound, the lie, and the need it defends -----------------------
    def wounded_by(self, ghost: str, *, teaches: Optional[str] = None,
                   cued_by: Optional[str] = None, evokes: Optional[str] = None,
                   when_above: float = 5.0):
        """The Ghost: the formative past event that still governs the present, and
        the Lie it taught (`teaches`, naming a `believes` on this character). If
        `cued_by`/`evokes` are given it also plants a somatic memory, so the wound
        can fire wordlessly in the body -- a flashback with no story attached.

            vera.wounded_by("the field, and the gunfire", teaches="unsafe",
                            cued_by="gunfire", evokes="panic")
        """
        self._wounds.append(_Wound(ghost=ghost, teaches=teaches))
        if cued_by is not None and evokes is not None:
            self.remembers(f"wound_{len(self._wounds)}", cued_by=cued_by,
                           when_above=when_above, evokes=evokes)
        return self

    def believes(self, lie: str, *, claim: str, disconfirmed_by: str,
                 expects: float = 2.0, threshold: float = 3.0,
                 conviction: float = 0.85, learn: float = 0.03,
                 breakable=True, feeling: str = "worthlessness",
                 harms: str = "self", says: Optional[str] = None,
                 baseline: float = 0.0):
        """The Lie the character believes -- a false belief, adopted to survive the
        wound, that they can no longer see past. `disconfirmed_by` is the channel of
        life-evidence that contradicts it; the lie predicts that channel reads low
        (`expects`), holds that prediction with high `conviction`, and so, when the
        evidence comes in high, *suppresses* it rather than updating -- the mechanism
        of self-deception. Each suppression hardens it (`learn`).

        `breakable` decides the arc:
          * `True` (the default) -- the lie can break, and *when* it breaks is
            derived automatically from its own strengths: a belief held harder
            (higher `conviction`, plus the hardening `learn` adds) resists longer,
            and one that trusts its disconfirming evidence less resists longer
            still. So the moment of self-revelation emerges from how strongly the
            lie is held versus how strong and trusted the evidence is -- no hand-set
            number. The positive arc.
          * a number -- an explicit absolute threshold on the accumulated evidence
            (for when you want to pin the moment exactly).
          * `None` or `False` -- the lie never breaks; it only hardens. The tragic
            arc, the self that meets the truth and doubles down.

        `harms` is 'self' (a psychological weakness) or 'others' (a moral one). The
        `feeling` is the ache the lie exists to keep out of awareness.

            blade.believes("only-rank-makes-me-real",
                claim="If I'm not ranked above them, I'm the surplus again.",
                disconfirmed_by="equal_regard", feeling="worthlessness",
                harms="others", breakable=None,          # he doubles down
                says="Some of us need there to be an upstairs.")
        """
        seen = f"{_ident(lie)}_seen"
        self._ensure_body_channel(disconfirmed_by, baseline=baseline)
        self._ensure_body_channel(seen, baseline=0.0)
        auto = (breakable is True)
        absolute = 0.0 if (breakable is None or breakable is False or auto) \
            else float(breakable)
        self._lies.append(_Lie(
            name=lie, claim=claim, evidence=disconfirmed_by, expects=expects,
            threshold=threshold, conviction=conviction, learn=learn,
            overwhelm=absolute, overwhelm_auto=auto,
            feeling=feeling, harms=harms, says=says))
        return self

    def needs(self, truth: str, *, feeling: str = "longing",
              fed_feeling: Optional[str] = None, opposes: Optional[str] = None,
              says: Optional[str] = None):
        """The Need: what the character must reach to become whole -- the opposite
        of the Lie, and the thing the story is really about. It is unconscious and
        resisted, and -- this is the whole point of an inner story -- it is *not*
        fed by getting the want. It aches the entire time the lie holds, and is met
        only when the lie is *seen*. Pass `opposes` naming the lie it answers; its
        relief is then wired to that lie's self-revelation.

            blade.needs("to-matter-as-an-equal", opposes="only-rank-makes-me-real",
                        feeling="worthlessness", fed_feeling="belonging")
        """
        seen = f"{_ident(opposes)}_seen" if opposes else f"{_ident(truth)}_seen"
        self._ensure_body_channel(seen, baseline=0.0)
        self._needs.append(_Need(
            name=truth, truth=truth, seen_channel=seen, feeling=feeling,
            fed_feeling=fed_feeling, opposes=opposes, says=says))
        return self

    def adopts(self, unmet: str, coping: str = "overcompensation", *,
               disconfirmed_by: str, conviction: Optional[float] = None,
               breakable=True, name: Optional[str] = None,
               fed_feeling: str = "recognition"):
        """*Predict* this character's lie from the wound, instead of specifying it.

        Given the unmet core need (`unmet`) and how the character copes with it
        (`coping`: surrender / avoidance / overcompensation), the schema engine
        forecasts the belief they will hold, what they will want, whom it harms,
        and how hard it is held -- and installs that lie and its need. This is the
        library making a positive prediction of personality structure rather than
        being told it: the same wound, coped with three ways, yields three people.

            blade.adopts("worth", "overcompensation", disconfirmed_by="equal_regard")
            # predicts: "If I am not ranked above them, I am the surplus again."

        Pass `conviction` to overrule the coping style's predicted grip, or
        `breakable=None` to keep the lie unbreakable. The `disconfirmed_by` channel
        is the evidence the author will drive against the lie.
        """
        from .schema import predict_lie
        p = predict_lie(unmet, coping)
        nm = name or f"{coping}_{_ident(unmet)}"
        if conviction is not None:
            self.story._accommodations.append(
                f"{self.name}.adopts({unmet!r}, {coping!r}): predicted "
                f"conviction {p.conviction} overridden to {conviction}")
        self.believes(nm, claim=p.claim, disconfirmed_by=disconfirmed_by,
                      feeling=p.feeling, harms=p.harms,
                      conviction=(p.conviction if conviction is None else conviction),
                      breakable=breakable, says=p.claim)
        self.needs(p.truth, opposes=nm, feeling=p.feeling,
                   fed_feeling=fed_feeling)
        self._lie_predictions[nm] = p
        return self

    # ---- appraisal: predict the feeling instead of naming it ---------------
    def appraises_event(self, channel: str, *, congruence: float,
                        agency: str = "circumstance", certainty: float = 0.7,
                        coping: float = 0.5, norm_compatible: bool = True,
                        norm_focus: str = "act", was_feared: bool = False,
                        relevance: float = 1.0, when: Optional[str] = None,
                        drives: Optional[str] = None, to: float = 100.0,
                        fades_to: Optional[float] = None,
                        shows_on: Optional[str] = None, shows_value: float = 8.0):
        """*Predict* what this character will feel about an event, instead of
        naming it. The author supplies only the appraisal -- was it bad for
        their goals, who caused it, how certain, can anything be done, did it
        break a standard -- and the appraisal engine (Scherer/OCC/Ellsworth
        convergent mappings) forecasts the discrete emotion and its Frijda
        action tendency, then compiles the loop that must produce it.

            vera.appraises_event("verdict", congruence=-0.9, agency="other",
                                 certainty=0.9, coping=0.2)
            # predicts: resentment -- other-blame without power

        Returns the PredictedFeeling (so the forecast can be preregistered);
        the character is modified in place, as with every other verb. The
        predicted quale is falsifiable per-story: it must fire in the Chronicle
        when the appraised event lands, or the model is wrong."""
        from .appraisal import predict_feeling
        pf = predict_feeling(congruence=congruence, agency=agency,
                             certainty=certainty, coping=coping,
                             norm_compatible=norm_compatible,
                             norm_focus=norm_focus, was_feared=was_feared,
                             relevance=relevance)
        if pf is None:
            return None
        self.appraises(channel, as_threat=(congruence < 0),
                       feeling=pf.quale, when=when, drives=drives, to=to,
                       fades_to=fades_to, shows_on=shows_on,
                       shows_value=shows_value)
        self._appraisal_predictions = getattr(self, "_appraisal_predictions", {})
        self._appraisal_predictions[channel] = pf
        return pf

    # ---- attachment: a style, and the separation it predicts ---------------
    def attaches(self, style: str, *, to: str = "them", **overrides):
        """Install an attachment style (secure / anxious / avoidant /
        disorganized) toward a figure. The style is a parameter bundle from
        Mikulincer & Shaver's hyperactivation/deactivation model, and it stakes
        a forecast about separation that `Story.predict_separation` will test:
        secure settles on reunion; anxious protests and stays up; avoidant
        narrates calm over a real somatic spike (the confabulation gap);
        disorganized approaches and avoids the same figure at once.

        Any keyword override of a style parameter is recorded as an
        accommodation."""
        from . import attachment as att
        return att.install(self, style, figure=to,
                           overrides=overrides or None)

    # ---- circumplex: a stance on the interpersonal circle ------------------
    def stance(self, *, dominance: float = 0.0, warmth: float = 0.0):
        """Place this character on the interpersonal circumplex. Used with
        `Story.meet(a, b)` to compile a dyad whose trajectory the
        complementarity principle predicts."""
        from .circumplex import Stance
        self._stance = Stance(dominance=dominance, warmth=warmth)
        return self

    # ---- narration ---------------------------------------------------------
    def narrates(self, *, downplaying: Optional[dict] = None,
                 voice: Optional[dict] = None):
        """Give the character a narrating self that speaks for its loops."""
        v = dict(voice or {})
        v.update(downplaying or {})
        self._narrator = {"voice": v}
        return self

    def has_budget(self, joules: float = 900.0):
        self._budget = joules
        return self

    # ---- timeline sugar ----------------------------------------------------
    def hears(self, channel: str, value: float):
        """Return an event for Story.at(...)."""
        return (self, channel, value)

    def shows(self, surface: str, value: float):
        """Drive one of this character's own surface channels (their face)."""
        self._expose_surface(surface)
        return (self, surface, value)

    # ---- internals ---------------------------------------------------------
    def _add_sense(self, ch, modality, baseline, kind):
        if not any(s.channel == ch for s in self._senses):
            self._senses.append(_Sense(ch, modality, baseline, kind))

    def _ensure_body_channel(self, ch, baseline=0.0):
        if ch not in self._body_channels:
            self._body_channels[ch] = baseline
        self._add_sense(ch, "intero", baseline, "Signal")

    def _set_channel_baseline(self, ch, baseline):
        """Update the baseline of an already-declared channel (a later feels()
        knows the resting value an earlier appraises() didn't)."""
        for s in self._senses:
            if s.channel == ch:
                s.baseline = baseline
                return
        self._add_sense(ch, "intero", baseline, "Signal")

    def _expose_surface(self, surface):
        # a surface another can read is a proprioceptive channel on this body
        self._add_sense(surface, "proprio", 5.0, "Expression")


class Story:
    """A whole simulation, authored in narrative terms."""

    def __init__(self, title: str, *, span: str = "10s", step: str = "1s",
                 about: Optional[str] = None, cadence: bool = False):
        self.title = title
        self.span = span
        self.step = step
        self.about = about
        self.cadence = cadence
        self.characters: list[Character] = []
        self._events: list[tuple] = []
        self._scenes: list[tuple] = []
        # theory defaults overridden by hand -- disclosed by Preregistration so
        # a run matching a hand-set dial is not mistaken for a prediction
        self._accommodations: list[str] = []

    # ---- building ----------------------------------------------------------
    def character(self, name: str, temperament: Temperament = trusting,
                  clock: str = "body") -> Character:
        c = Character(self, name, temperament, clock)
        self.characters.append(c)
        return c

    def scene(self, title: str, *, frm: str, to: str):
        self._scenes.append((title, frm, to))
        return self

    def at(self, t: str, *events):
        """Schedule world-events at time t. Each event comes from
        character.hears(...) or character.shows(...), or is a bare
        (channel, value) applied to the first character."""
        for ev in events:
            if len(ev) == 3:
                who, ch, val = ev
                self._events.append((t, who, ch, val))
            elif len(ev) == 2:
                ch, val = ev
                who = self.characters[0] if self.characters else None
                self._events.append((t, who, ch, val))
        return self

    def over(self, arc_obj, event_fn):
        """Spread an Arc across the timeline. `event_fn` maps a value to an
        event tuple (usually `character.hears`).

            story.over(arc.wobble(around=5, span="24y", every="2y"),
                       lambda v: soren.hears("her_face", v))

        This removes the last of the hand-written stimulus bookkeeping: describe
        the *shape* of how something changes, and let the library lay out the
        beats."""
        for (t, v) in arc_obj:
            self.at(t, event_fn(v))
        return self

    def consent(self, note: str):
        self.about = note
        return self

    # ---- compilation -------------------------------------------------------
    def source(self) -> str:
        from ._compiler import Compiler
        return Compiler(self).compile()

    # ---- run-through to the base toolchain --------------------------------
    def _result(self, functional_only=False):
        from soma import run_source
        return run_source(self.source(), title=self.title,
                          functional_only=functional_only)

    def run(self, rows: int = 30, width: int = 88, color: bool = False,
            unicode: bool = True) -> str:
        from soma import winnow, viz, query as qmod
        viz.configure(color=color, unicode=unicode, width=width)
        r = self._result()
        findings = winnow.sift(r.chronicle)
        qr = qmod.run_all(r.program, r.chronicle)
        return viz.render_report(r, findings=findings, trace_rows=rows,
                                 qresults=qr)

    def sift(self, pattern: Optional[str] = None):
        from soma import winnow
        return winnow.sift(self._result().chronicle, pattern)

    def prose(self, genders: Optional[dict] = None, width: int = 88) -> str:
        from soma import prose as prose_mod, viz
        viz.configure(color=False, unicode=True, width=width)
        return prose_mod.render(self._result(), genders=genders or {},
                                width=width - 4)

    def perturb(self, set_expr: str, width: int = 88):
        from soma import viz
        from soma.perturb import perturb as _perturb
        viz.configure(color=False, unicode=True, width=width)
        d = _perturb(self.source(), set_expr, title=self.title)
        return viz.render_diff(d)

    def result(self):
        """The raw Result object, for programmatic inspection."""
        return self._result()

    # ---- prediction: forecast a response to a situation never scripted --------
    def predict(self, who, stimulus: dict, *, beats: int = 6, hold: float = 8.0):
        """Forecast how a character would respond to a situation the author never
        wrote -- a counterfactual the model has not seen. This is the difference
        between replaying a script and making a positive prediction: the same
        mechanism is run on an *unseen* input, and it must generate the effect (or
        fail to), which is what makes the claim falsifiable.

        `stimulus` is a {channel: value} the character faces, alone, for `beats`
        beats (everything the author actually scripted is stripped away, so the
        forecast isolates this one situation). Returns a `Prediction`.

            fleet.predict("Blade", {"equal_regard": 9})
            # -> faced with equal regard at full strength, Blade SUPPRESSES it;
            #    his lie does not break. (Predicted, not scripted.)
        """
        import re as _re
        name = who.name if isinstance(who, Character) else who
        multi = len(self.characters) > 1
        # build the probe source: the character's whole structure, but the only
        # input is the stimulus under test.
        src = self.source()
        kept = [ln for ln in src.splitlines()
                if not ln.lstrip().startswith("stimulus ")]
        probe = []
        for ch, val in stimulus.items():
            scoped = f"{name}.{ch}" if multi else ch
            body = "  ".join(f"at {i}s: {_num_probe(val)}"
                             for i in range(1, beats + 1))
            probe.append(f"stimulus {scoped} {{ {body} }}")
        probe_src = "\n".join(kept + [""] + probe) + "\n"

        from soma import run_source
        r = run_source(probe_src, title=f"{self.title}__predict")
        chron = r.chronicle

        def owns(w):
            return (w.split(".")[0] == name) if multi else True

        # which loops actually READ the stimulus under test? Only those loops'
        # responses are evidence about how the character meets *this* situation --
        # the lie that reads it, an appraisal of it -- not the whole nervous system.
        probe_channels = set(stimulus)
        readers = set()
        for lp in r.program.loops:
            if lp.sense in probe_channels or lp.sense.split(".")[-1] in probe_channels:
                readers.add(lp.name)
        reader_tails = {rr.split(".")[-1] for rr in readers}

        def relevant(w):
            tail = w.split(".")[-1]
            return owns(w) and (not readers or w in readers or tail in reader_tails)

        revs = [(e.who, e.t) for e in chron
                if e.kind == "revelation" and relevant(e.who)]
        routes = [e.detail.get("route") for e in chron
                  if e.kind == "settle" and relevant(e.who)
                  and abs(e.detail.get("error", 0)) > 0.5]
        acts = routes.count("act")
        percs = routes.count("perceive")
        feelings = []
        for e in chron:
            if e.kind == "emit" and relevant(e.who):
                q = str(e.detail.get("quale", "")).replace("Qualia<", "").replace(">", "")
                if q and q not in feelings:
                    feelings.append(q)
        broke = revs[0] if revs else None
        if acts > percs:
            route = "suppress"
        elif percs > acts:
            route = "take-in"
        elif routes:
            route = "mixed"
        else:
            route = "unmoved"
        return Prediction(who=name, stimulus=dict(stimulus), route=route,
                          breaks_lie=(broke[0].split(".")[-1] if broke else None),
                          break_time=(broke[1] if broke else None),
                          feelings=feelings,
                          detail={"acts": acts, "perceives": percs})

    def tipping_point(self, who, channel: str, *, lo: float = 0.0,
                      hi: float = 9.0, step: float = 1.0, beats: int = 8):
        """Predict the *threshold*: the least sustained strength of `channel` at
        which the character's response flips from suppressing to breaking. A sharp,
        quantitative, falsifiable claim about a person the model was never given at
        that strength -- and, for an unbreakable lie, a prediction of *no* threshold
        in range, which is the strongest falsification target of all.

            fleet.tipping_point("Ink", "kept_for_nothing")   # -> breaks at >= 6.0
            ring.tipping_point("Blade", "equal_regard")       # -> never, in [0, 9]
        """
        v = lo
        while v <= hi + 1e-9:
            p = self.predict(who, {channel: v}, beats=beats)
            if p.breaks_lie:
                return {"who": (who.name if isinstance(who, Character) else who),
                        "channel": channel, "breaks_at": round(v, 2),
                        "in_range": (lo, hi)}
            v += step
        return {"who": (who.name if isinstance(who, Character) else who),
                "channel": channel, "breaks_at": None, "in_range": (lo, hi)}

    # ---- preregistration: forecasts staked before the run -------------------
    def preregister(self):
        """Open a preregistration: claims about this story staked BEFORE it is
        run, checked mechanically after, with theory-default overrides
        disclosed as accommodations. See soma.narrative.preregister."""
        from .preregister import Preregistration
        return Preregistration(self)

    # ---- attachment & circumplex forecasts ----------------------------------
    def predict_separation(self, who, *, beats: int = 5, reunion_beats: int = 5):
        """Test an attachment style's staked forecast against a separation the
        author never scripted (see soma.narrative.attachment)."""
        from . import attachment as att
        return att.predict_separation(self, who, beats=beats,
                                      reunion_beats=reunion_beats)

    def meet(self, a, b, *, lag: str = "1s", gain: float = 0.9):
        """Bind two characters (each of whom has a `stance`) into a circumplex
        dyad: manner surfaces, mutual reading through couple/lag, warmth
        correspondence, and a measurable rapport mood."""
        from .circumplex import bind_dyad
        ca = a if isinstance(a, Character) else next(
            c for c in self.characters if c.name == a)
        cb = b if isinstance(b, Character) else next(
            c for c in self.characters if c.name == b)
        return bind_dyad(ca, cb, a_stance=ca._stance, b_stance=cb._stance,
                         lag=lag, gain=gain)

    def predict_dyad(self, a, b, *, beats: int = 10):
        """Forecast, from the two stances alone, whether the interaction
        settles or strains and who gives ground -- then run the compiled dyad
        and check each claim (see soma.narrative.circumplex)."""
        from . import circumplex as cx
        return cx.predict_dyad(self, a, b, beats=beats)

    # ---- the study layer: insight into predictive characterizations --------
    def sensitivity(self, *, params: dict, outcome_name: str = "break_time",
                    character=None, channel: str = "heart", mood=None,
                    quale=None, n_base: int = 64, seed: int = 0):
        """Variance-based (Sobol) sensitivity: which dial actually writes this
        outcome, on its own vs. through interaction. See
        soma.narrative.sensitivity."""
        from .sensitivity import sensitivity
        return sensitivity(self, params=params, outcome_name=outcome_name,
                           character=character, channel=channel, mood=mood,
                           quale=quale, n_base=n_base, seed=seed)

    def discriminate(self, who, *, version_a: dict, version_b: dict,
                     probes: dict, outcome_name: str = "break_time",
                     beats: int = 8, character=None, channel: str = "heart",
                     mood=None, quale=None):
        """Adaptive-design-style model discrimination: find the probe under
        which two readings of a character diverge most -- the scene to write.
        See soma.narrative.discriminate."""
        from .discriminate import discriminate
        return discriminate(self, who, version_a=version_a, version_b=version_b,
                            probes=probes, outcome_name=outcome_name,
                            beats=beats, character=character, channel=channel,
                            mood=mood, quale=quale)

    def predict_break_onset(self, who, channel: str = "heart", *,
                            window: int = 4, overrides=None):
        """Critical-slowing-down early warning: read only the pre-transition
        dynamics and forecast whether a self-revelation is coming. See
        soma.narrative.earlywarning."""
        from .earlywarning import predict_break_onset
        return predict_break_onset(self, who, channel, window=window,
                                   overrides=overrides)

    def minimal_intervention(self, *, target, dials: dict, character=None,
                             channel: str = "heart", mood=None, quale=None,
                             steps: int = 24):
        """Counterfactual: the smallest single-dial change that flips the
        ending -- the margin the ending turns on. See
        soma.narrative.counterfactual."""
        from .counterfactual import minimal_intervention
        return minimal_intervention(self, target=target, dials=dials,
                                    character=character, channel=channel,
                                    mood=mood, quale=quale, steps=steps)

    def characterize(self, width: int = 88) -> str:
        """Synthesize a *portrait* -- not a log of what happened, but a reading
        of who each character is, drawn from the run. It gathers the drives that
        organize them, the values they hold and break, the feeling their psyche
        defends against, and whether they changed -- and writes it as prose a
        novelist could put in a notebook.

        This is the library's answer to the question the whole project is for:
        not 'what did the simulation do' but 'who is this person'."""
        from soma import winnow
        r = self._result()
        chron = r.chronicle
        findings = winnow.sift(chron)
        from collections import Counter

        # index findings by pattern for quick lookup
        by_pat = {}
        for f in findings:
            by_pat.setdefault(f.pattern, []).append(f)

        lines = []
        title = self.title.replace("_", " ").upper()
        lines.append(title)
        lines.append("a reading, drawn from the body's record")
        lines.append("")

        # per character, assemble the portrait
        multi = len(self.characters) > 1
        for c in self.characters:
            # a character who only shows a face (no appraisals, feelings, drives,
            # values, parts, or relations) has no interior to read -- they are a
            # presence in someone else's scene, not a subject. Skip them.
            has_interior = (c._appraisals or c._feelings or c._drives
                            or c._values or c._parts or c._relations
                            or c._moods or c._memories
                            or c._lies or c._needs or c._wounds or c._cravings)
            if not has_interior:
                continue
            if multi:
                lines.append(f"— {c.name} —")
            # temperament as disposition
            lines.append(f"Disposition: {c.temp.name}. "
                         f"{_temperament_gloss(c.temp.name)}")
            # what they want / fear
            wants = [d for d in c._drives if d.kind == "want"]
            fears = [d for d in c._drives if d.kind == "fear"]
            if wants or fears:
                w = ", ".join(sorted(set(d.channel for d in wants)))
                fr = ", ".join(sorted(set(d.channel for d in fears)))
                if w and fr and set(d.channel for d in wants) & set(d.channel for d in fears):
                    shared = (set(d.channel for d in wants)
                              & set(d.channel for d in fears))
                    lines.append(f"Torn: wants and fears the same thing "
                                 f"({', '.join(sorted(shared))}) -- drawn and "
                                 f"repelled at once, arriving nowhere.")
                else:
                    if w:
                        lines.append(f"Wants: {w}.")
                    if fr:
                        lines.append(f"Fears: {fr}.")
            # the wound, the lie it taught, the need it defends, and the arc --
            # the deepest layer of character (Truby's ghost/lie/need).
            for wd in c._wounds:
                lines.append(f"Wounded by: {wd.ghost}.")
            for lie in c._lies:
                kind = ("a moral weakness -- it harms others"
                        if lie.harms == "others"
                        else "a psychological weakness -- it harms mostly himself")
                lines.append(f"The lie he believes: \"{lie.claim}\" ({kind}).")
                pred = c._lie_predictions.get(lie.name)
                if pred is not None:
                    lines.append(f"  (predicted from the wound: {pred.schema}, "
                                 f"coped with by {pred._style()}.)")
                # the arc, read off the sift for this character
                def _mine(pat):
                    return [f for f in by_pat.get(pat, [])
                            if not multi or f.detail.get("owner") in (None, c.name)]
                if _mine("the lie seen"):
                    lines.append("Arc: the lie is seen -- overwhelmed at last by the "
                                 "evidence it could not keep suppressing. He changes.")
                elif _mine("the lie kept"):
                    lines.append("Arc: the lie is kept -- met with the truth, he "
                                 "doubles down. He does not change; he hardens.")
            for nd in c._needs:
                met = any((not multi or f.detail.get("owner") in (None, c.name))
                          for f in by_pat.get("the need met", []))
                if met:
                    lines.append(f"Needs (and reaches): {nd.truth.replace('-', ' ')} "
                                 f"-- what the want could never feed.")
                else:
                    lines.append(f"Needs (and never reaches): "
                                 f"{nd.truth.replace('-', ' ')} -- it aches under "
                                 f"everything the want reaches for.")
            # values held and broken
            for v in c._values:
                broke = any(v.name in f.detail.get("owner", "") or
                            f.detail.get("said") == v.stated
                            for f in by_pat.get("the value the body broke", []))
                if broke or by_pat.get("the value the body broke"):
                    lines.append(f"Holds: \"{v.stated}\" -- and breaks it. The "
                                 f"principle is real; it is simply not what "
                                 f"governs the act.")
                else:
                    lines.append(f"Holds: \"{v.stated}\" -- and keeps it, here.")
            # the defended feeling (only this character's)
            for f in by_pat.get("the feeling the whole self defends against", []):
                if f.detail.get("owner") not in (None, c.name) and multi:
                    continue
                lines.append(f"Defends against: {f.detail.get('quale')}. "
                             f"The rest of the self is built around not feeling it.")
            # change (only this character's)
            for f in by_pat.get("the person they became", []):
                if multi and f.detail.get("owner") != c.name:
                    continue
                lines.append(f"Changed: began in {f.detail.get('was')}, "
                             f"ended in {f.detail.get('became')}.")
            # internal parts: a divided self, and which part is never heard
            if c._parts:
                never = {f.detail.get("content", "") for f in findings
                         if f.pattern == "never ignited"}
                for p in c._parts:
                    safe = p.name.replace("-", "_")
                    silenced = any(safe in n for n in never)
                    role = p.role
                    art = "an" if role[:1] in "aeiou" else "a"
                    if silenced:
                        lines.append(f"Carries (unheard): {art} {role}, "
                                     f"'{p.name}', that feels {p.feeling} and "
                                     f"never reaches awareness -- felt, never known.")
                    else:
                        lines.append(f"Carries: {art} {role}, '{p.name}', that "
                                     f"feels {p.feeling} and gets a voice.")
            # the relational self: who she becomes with whom
            if len(c._relations) > 1:
                pairs = ", ".join(f"{r.feeling} with {r.other}"
                                  for r in c._relations)
                lines.append(f"A different self with each: {pairs} -- the same "
                             f"person, indexed by whom she is with.")
            # what they mostly felt
            owner_emits = [e for e in chron if e.kind == "emit"
                           and (not multi or e.who.startswith(c.name + "."))]
            if owner_emits:
                qs = Counter(str(e.detail.get("quale", ""))
                             .replace("Qualia<", "").replace(">", "")
                             for e in owner_emits)
                top = qs.most_common(1)[0]
                lines.append(f"Mostly felt: {top[0]} ({top[1]} times).")
            # the story they told
            owner_narr = [e for e in chron if e.kind == "narrate"
                          and (not multi or c.name in e.who)]
            if owner_narr:
                q = Counter(e.detail.get("quote", "") for e in owner_narr)
                said = q.most_common(1)[0][0]
                if said:
                    lines.append(f"The story they told themselves: \"{said}\"")
            lines.append("")

        from soma import viz
        viz.configure(color=False, unicode=True, width=width)
        # wrap each line to the box interior so nothing truncates
        wrapped = []
        for ln in lines:
            if not ln:
                wrapped.append("")
            else:
                wrapped.extend(viz.wrap_body(ln, width, indent=""))
        return viz.box("CHARACTER", wrapped, width=width)
