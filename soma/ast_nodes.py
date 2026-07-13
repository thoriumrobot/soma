"""
SOMA abstract syntax tree.

These dataclasses are the *compiled* form the parser produces and the runtime
walks. Kept deliberately small and literal -- the interesting machinery is in
the runtime, not the grammar.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

# ---------- expressions ----------

@dataclass
class Num:
    value: float

@dataclass
class Str:
    value: str

@dataclass
class Ref:              # bare identifier: a channel, a let-binding, or a label
    name: str

@dataclass
class Call:             # predict(x), spend(b,200), set(heart,118), stiffen(back)...
    fn: str
    args: list

@dataclass
class Feel:             # feel(dread) -> produces an opaque Qualia
    quale: str

@dataclass
class Bin:              # arithmetic / comparison
    op: str
    left: object
    right: object

# ---------- precision specifications ----------

@dataclass
class PrecConst:
    value: float

@dataclass
class PrecExpr:        # precision: clamp(0.9 - 0.7 * deference, 0.05, 1.0)
    expr: object       # re-evaluated every moment, in the loop's own scope

@dataclass
class PrecRamp:        # ramp(0.5 -> 0.99 over biography)
    start: float
    end: float
    clock: str

# ---------- act-block statements ----------

@dataclass
class Update:          # update -> expr   (belief moves toward the sensed value)
    target: object

@dataclass
class Move:            # move ! action    (change the world/body)
    action: Call

@dataclass
class Ignore:
    pass

@dataclass
class Emit:            # emit feel(dread)
    feel: Feel

@dataclass
class Guard:           # `<stmt> when <cond>` -- an act that only sometimes happens
    cond: object
    stmt: object

@dataclass
class Broadcast:      # broadcast <expr> with salience <expr>  (global workspace)
    content: object
    salience: object = None

@dataclass
class Attend:         # attend <target> cost <expr>  (spend the attention spotlight)
    target: str
    cost: object = None

# ---------- top-level declarations ----------

@dataclass
class Flow:           # continuous physiology: flow heart { dynamics: -(heart-70)/tau }
    channel: str
    dynamics: object
    clock: str = "cardiac"
    owner: str = None

@dataclass
class Embodiment:     # body schema vs body image, paired by name
    name: str
    pairs: list = field(default_factory=list)   # list[(pairname, schema_val, image_val, tol)]

@dataclass
class Memory:         # four registers; somatic can fire without episodic trace
    register: str     # episodic|semantic|procedural|somatic
    name: str
    cue: str          # channel
    when: object      # threshold expr
    evoke: str        # quale to feel
    strength: float = 1.0
    owner: str = None

@dataclass
class Attention:      # the affine spotlight
    name: str
    capacity: float

@dataclass
class Workspace:      # global workspace / ignition
    name: str
    threshold: float = 0.5

@dataclass
class Awareness:      # Graziano attention schema: a transparent model of attention
    name: str
    tracks: str       # attention name
    tau: float = 0.1

@dataclass
class Allostat:       # predictive allostatic controller
    name: str
    regulate: str     # channel
    setpoint: float
    gain: float = 0.5
    resource: str = None    # optionally pre-spends a budget
    owner: str = None

@dataclass
class Intervene:      # global perturbation, e.g. rebus(entropy)
    kind: str         # 'rebus'
    at: float
    strength: float

@dataclass
class Ownership:      # body-ownership dependent type (rubber hand, phantom)
    name: str
    predicted: str    # channel
    observed: str     # channel
    tolerance: float = 2.0
    initial: bool = True   # is the part owned at t=0? (a rubber hand is not)

@dataclass
class Couple:         # A's expression becomes B's sensation, after a lag
    src: str          # qualified channel  (Alice.face)
    dst: str          # qualified channel  (Bob.sees_face)
    gain: float = 1.0
    lag: float = 0.0

@dataclass
class Scene:          # a narrative beat: a named window of the Chronicle
    title: str
    t0: float
    t1: float

@dataclass
class QueryPred:
    rel: str
    terms: list       # list[('var', name) | ('lit', value)]

@dataclass
class Query:
    name: str
    preds: list = field(default_factory=list)
    wheres: list = field(default_factory=list)   # Bin expressions over ?vars
    surface: str = ""

@dataclass
class Sim:
    duration: float = 6.0
    dt: float = 0.5
    cadence: bool = False    # if true, each loop ticks at its own clock's cadence

@dataclass
class Let:
    name: str
    value: object

@dataclass
class Channel:
    modality: str      # 'intero'|'extero'|'proprio'|'schema'|'image'
    name: str
    ctype: str
    baseline: float = 0.0
    retention: Optional[float] = None
    protention: Optional[float] = None
    efference: Optional[str] = None
    gain: float = 0.35

@dataclass
class Body:
    name: str
    clock: str
    channels: list = field(default_factory=list)
    owner: str = None

@dataclass
class Resource:
    name: str
    amount: float
    unit: str = "Joule"

@dataclass
class Stimulus:
    channel: str
    events: list = field(default_factory=list)   # list[(time, value)]

@dataclass
class Loop:
    name: str
    clock: str
    prior: object
    sense: str                 # channel name
    precision: object          # PrecConst | PrecRamp   (sensory precision pi_s)
    conviction: object         # PrecConst | PrecRamp   (prior precision pi_p)
    act: list                  # list of act statements
    mode: str = "deliberate"   # 'habit' (cheap) | 'deliberate' (spends attention)
    efference: str = None      # loop whose action reafferently cancels this sense
    learn: float = 0.0         # experience hardens the prior: pi_p += learn per fire
    overwhelm: float = 0.0     # raw disconfirming surprise that, accumulated, forces
                               # a perceive (self-revelation); 0 = never breaks
    overwhelm_auto: bool = False  # if set, the breaking threshold is derived from the
                               # belief's own conviction vs its trust in the evidence
                               # (no author number) -- see Interpreter.settle
    owner: str = None          # the character this loop belongs to

@dataclass
class Mood:
    name: str
    clock: str
    integrates: list           # list[(source_name, weight)]
    decay: float = 0.98

@dataclass
class Narrator:
    name: str
    subscribes: list           # list[str] of loop names
    confabulates: bool = True
    voice: dict = field(default_factory=dict)   # quale/action -> line
    owner: str = None

@dataclass
class Handler:
    name: str
    when: Optional[object] = None      # Bin condition on error
    on_crash: list = field(default_factory=list)   # statements
    after: Optional[float] = None      # repair delay (seconds)
    repair: list = field(default_factory=list)

@dataclass
class Program:
    consent: list = field(default_factory=list)   # @consent strings
    sim: Sim = field(default_factory=Sim)
    lets: list = field(default_factory=list)
    bodies: list = field(default_factory=list)
    resources: list = field(default_factory=list)
    stimuli: list = field(default_factory=list)
    loops: list = field(default_factory=list)
    moods: list = field(default_factory=list)
    narrators: list = field(default_factory=list)
    handlers: list = field(default_factory=list)
    flows: list = field(default_factory=list)
    embodiments: list = field(default_factory=list)
    memories: list = field(default_factory=list)
    attentions: list = field(default_factory=list)
    workspaces: list = field(default_factory=list)
    awarenesses: list = field(default_factory=list)
    allostats: list = field(default_factory=list)
    interventions: list = field(default_factory=list)
    ownerships: list = field(default_factory=list)
    queries: list = field(default_factory=list)
    couples: list = field(default_factory=list)
    scenes: list = field(default_factory=list)
    characters: list = field(default_factory=list)
    title: str = "untitled"
