"""
SOMA runtime.

The 'compiler' front end (lexer/parser/checker) produces a Program; this module
executes it. Execution is a *moment-based* scheduler -- a deliberate,
documented simplification of the manifesto's ideal of seven real-time clocks.
We cannot literally step a neural clock at 1 kHz for a biography-length
simulation, so instead the run is a sequence of N discrete *moments* (frames).
Each moment carries a timestamp; fast loops model instantaneous appraisal, slow
loops (mood, biography ramps) evolve across the whole run. This keeps causality
legible while spanning milliseconds to years.

Order within a moment:
  1. fire scheduled stimuli
  2. settle loops, fastest clock first (so appraisal can drive physiology
     before an interoceptive loop reads it)
  3. integrate moods (the slow variable)
  4. let the narrator tell its story (and, sometimes, get it wrong)
  5. run trauma handlers (crash / repair)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from . import ast_nodes as A
from .chronicle import Chronicle, Qualia
from .checker import check
from .mathlib import BUILTINS as _MATH

# clock -> nominal tick period in seconds (for ordering + reporting only)
CLOCK_PERIOD = {
    "neural": 0.01, "cardiac": 1.0, "breath": 4.0, "mood": 60.0,
    "hormonal": 3600.0, "circadian": 86400.0, "biography": 31_536_000.0,
    "lineage": 3.15e9,
}

# how each quale reads on the valence barometer (negative = costly)
VALENCE = {
    "dread": -1.0, "despair": -1.0, "grief": -0.9, "reaching": -0.6,
    "pain": -0.8, "terror": -1.0, "panic": -1.0, "shame": -0.8,
    "anguish": -1.0, "numbness": -0.15, "calm": 0.3, "relief": 0.6,
    "delight": 1.0, "delight_at_error": 1.0, "love": 1.0, "joy": 1.0,
    "warmth": 0.7, "hope": 0.6, "contempt": -0.7, "recognition": 0.1,
    "belonging": 0.7,
    # subtler affects a novel turns on -- the weather between the storms
    "unease": -0.5, "disquiet": -0.55, "foreboding": -0.7, "longing": -0.5,
    "tenderness": 0.8, "apprehension": -0.6, "desolation": -0.95,
    "wariness": -0.5, "yearning": -0.5,
    "comfort": 0.5, "safety": 0.5, "wonder": 0.8, "anger": -0.7,
    "self_betrayal": -0.85, "ambivalence": -0.4, "resolve": 0.4,
    # the appraisal-predicted emotions (soma.narrative.appraisal) and the
    # circumplex dyad qualia (soma.narrative.circumplex)
    "fear": -0.9, "resentment": -0.65, "frustration": -0.55, "guilt": -0.7,
    "regret": -0.6, "gratitude": 0.8, "ease": 0.5, "friction": -0.6,
    "loneliness": -0.7, "anticipation": 0.6, "reaching_out": 0.4,
    "terror": -0.95,
    "worthlessness": -0.85, "pride": 0.7, "grief": -0.9,
}

FIRE_EPS = 0.5          # |error| above which a loop 'fires'
ATTENUATED = 0.05       # pi_s below this => the error is ignored
ATTN_REGEN = 0.35       # fraction of spotlight capacity recovered per moment
LEARN_CAP  = 1.2        # experience can harden a prior only so far
BREAK_K    = 6.0        # `overwhelm: auto` breaks a belief when accumulated raw
                        # surprise exceeds BREAK_K * conviction / trust-in-evidence
                        # -- so a harder-held or less-trusted belief resists longer


@dataclass
class LoopState:
    decl: A.Loop
    belief: float
    label: str
    learned: float = 0.0     # conviction accrued by repetition
    overwhelm_debt: float = 0.0   # accumulated disconfirming surprise, suppressed

@dataclass
class Result:
    program: A.Program
    chronicle: Chronicle
    channel_hist: dict          # name -> list[float]
    mood_hist: dict             # name -> list[float]
    resource_hist: dict         # name -> list[float]
    times: list                 # frame -> t (seconds)
    functional_only: bool = False
    attn_hist: dict = None      # attention spotlight remaining
    aware_hist: dict = None     # awareness (transparent model of attention)
    ignition_hist: dict = None  # workspace ignition index
    interp: object = None       # back-reference (for phi on demand)


class Interpreter:
    def __init__(self, prog: A.Program, functional_only: bool = False):
        self.prog = prog
        self.functional_only = functional_only
        self.chron = Chronicle()
        self.lets = {}
        self.channels = {}       # name -> dict(value, baseline, modality)
        self.resources = {}      # name -> dict(cur, cap)
        self.loops: list[LoopState] = []
        self.moods = {}          # name -> value
        self.dissociated = {}    # scope -> bool
        self.dissoc_start = {}   # scope -> time
        self.repaired = set()
        # 0.3 subsystems
        self.attention = {}      # name -> dict(cur, cap)
        self.awareness = {}      # name -> dict(value, tracks, tau)
        self.workspace = {}      # name -> dict(threshold)
        self.owned = {}          # ownership name -> bool
        self.embody = {}         # embodiment: pairname -> dict(schema_ch,image_ch,tol)
        self.rebus_factor = 1.0  # multiplies prior precision (conviction) globally
        self._last_action = {}   # loop name -> last action magnitude (for reafference)
        # histories
        self.channel_hist = {}
        self.mood_hist = {}
        self.resource_hist = {}
        self.attn_hist = {}
        self.aware_hist = {}
        self.ignition_hist = {}
        self.times = []
        # per-frame scratch
        self._frame_emits = []       # (quale, loop, channel)
        self._frame_decisions = []   # (loop, channel, action_label, t)
        self._frame_broadcasts = []  # (content_label, salience, loop)
        self._cur_owner = None       # character scope of the settling loop
        self._cur_route = None       # arbitration outcome of the settling loop
        self._frame_stimuli = set()  # channels the world wrote to this frame
        self.scene = None            # current scene title

    # ---------- name resolution ----------
    def _res(self, name, table):
        """Resolve a name against a table, trying the bare name first and then
        the enclosing character's scope. So inside `character Alice`, `heart`
        finds `Alice.heart`, while `Bob.face` is found verbatim -- one rule for
        both self-knowledge and knowledge of others."""
        if name in table:
            return name
        if self._cur_owner:
            q = f"{self._cur_owner}.{name}"
            if q in table:
                return q
        return name

    def chan(self, name):
        return self.channels.get(self._res(name, self.channels))

    # ---------- expression evaluation ----------
    def num_of(self, e) -> float:
        if isinstance(e, A.Num):
            return float(e.value)
        if isinstance(e, A.Str):
            return 0.0
        if isinstance(e, A.Ref):
            # the arbitration outcome reads naturally without parentheses:
            #     move ! set(verdict, 9) when acting
            if e.name == "acting":
                return 1.0 if self._cur_route == "act" else 0.0
            if e.name == "perceiving":
                return 1.0 if self._cur_route == "perceive" else 0.0
            ch = self.chan(e.name)
            if ch is not None:
                return float(ch["value"])
            mn = self._res(e.name, self.moods)
            if mn in self.moods:
                return float(self.moods[mn])
            if e.name in self.lets:
                return float(self.lets[e.name])
            return 0.0
        if isinstance(e, A.Call):
            # `acting` / `perceiving` -- the arbitration outcome, readable.
            # Precision arbitration decides whether a loop changes its mind or
            # changes the world. Until now that decision was invisible to the
            # program that made it. A clinician who is *perceiving* asks another
            # question; one who is *acting* writes the diagnosis down.
            if e.fn == "acting":
                return 1.0 if self._cur_route == "act" else 0.0
            if e.fn == "perceiving":
                return 1.0 if self._cur_route == "perceive" else 0.0
            if e.fn == "owned" and e.args:
                # `owned(limb)` -- 1.0 if the part is currently owned, else 0.0.
                # Lets a defensive loop fire only for a limb that is actually
                # his: the flinch is the ownership illusion's proof.
                nm = e.args[0].name if isinstance(e.args[0], A.Ref) else None
                for k, v in self.owned.items():
                    if k == nm or k.endswith("." + str(nm)):
                        return 1.0 if v else 0.0
                return 0.0
            if e.fn == "belief" and e.args:
                # `belief(loop)` -- what a loop currently expects. A narrator may
                # read it; another loop may act on it. Nothing may read a Qualia.
                nm = e.args[0].name if isinstance(e.args[0], A.Ref) else None
                for ls in self.loops:
                    if ls.decl.name == nm or ls.decl.name.endswith("." + str(nm)):
                        return float(ls.belief)
                return 0.0
            if e.fn == "field" and e.args:
                # `field(tag)` -- the mean value, right now, of every channel
                # whose name is `tag` or ends `.tag`. It reads a *population*:
                # how the whole group is currently disposed, not any one member.
                # This is what makes a belief-about-belief expressible -- a
                # conviction that tracks how many others currently hold the same
                # thing, so that confidence (belief about others' belief) can
                # cascade when the field thins. Absent members do not count; an
                # empty field reads 0.
                tag = e.args[0].name if isinstance(e.args[0], A.Ref) else \
                    (e.args[0].value if isinstance(e.args[0], A.Str) else None)
                if tag is None:
                    return 0.0
                vals = [c["value"] for nm, c in self.channels.items()
                        if nm == tag or nm.endswith("." + tag)]
                # a member may exclude itself with field(tag, self_channel):
                # subtract the reader's own compliance so it reads *others*.
                if len(e.args) > 1:
                    mine = self.chan(e.args[1].name) if isinstance(e.args[1], A.Ref) else None
                    if mine is not None and vals:
                        tot = sum(vals) - float(mine["value"])
                        return tot / (len(vals) - 1) if len(vals) > 1 else 0.0
                return sum(vals) / len(vals) if vals else 0.0
            if e.fn == "predict" and e.args:
                a = e.args[0]
                if isinstance(a, A.Ref):
                    ch = self.chan(a.name)
                    if ch is not None:
                        return float(ch["baseline"])
                return self.num_of(a)
            if e.fn in ("metabolic_reserve",) and e.args:
                return self.num_of(e.args[0])
            # retention / protention over a channel's recorded history
            if e.fn == "ret" and e.args:
                cname = self._res(e.args[0].name, self.channels) if isinstance(e.args[0], A.Ref) else None
                back = int(self.num_of(e.args[1])) if len(e.args) > 1 else 1
                hist = self.channel_hist.get(cname, [])
                return float(hist[-back]) if len(hist) >= back else (
                    float(hist[0]) if hist else 0.0)
            if e.fn == "pro" and e.args:              # linear protention
                cname = self._res(e.args[0].name, self.channels) if isinstance(e.args[0], A.Ref) else None
                hist = self.channel_hist.get(cname, [])
                if len(hist) >= 2:
                    return float(2 * hist[-1] - hist[-2])
                return float(hist[-1]) if hist else 0.0
            if e.fn in _MATH:
                return _MATH[e.fn](*[self.num_of(a) for a in e.args])
            if e.args:
                return self.num_of(e.args[0])
            return 0.0
        if isinstance(e, A.Bin):
            l, r = self.num_of(e.left), self.num_of(e.right)
            return {"+": l + r, "-": l - r, "*": l * r, "/": l / r if r else 0.0,
                    "<": float(l < r), ">": float(l > r), "<=": float(l <= r),
                    ">=": float(l >= r), "==": float(l == r), "!=": float(l != r)}[e.op]
        return 0.0

    def label_of(self, e) -> str:
        if isinstance(e, A.Str):
            return e.value
        if isinstance(e, A.Ref):
            return e.name
        if isinstance(e, A.Num):
            return f"{e.value:g}"
        if isinstance(e, A.Feel):
            return e.quale
        if isinstance(e, A.Call):
            # `acting` / `perceiving` -- the arbitration outcome, readable.
            # Precision arbitration decides whether a loop changes its mind or
            # changes the world. Until now that decision was invisible to the
            # program that made it. A clinician who is *perceiving* asks another
            # question; one who is *acting* writes the diagnosis down.
            if e.fn == "acting":
                return 1.0 if self._cur_route == "act" else 0.0
            if e.fn == "perceiving":
                return 1.0 if self._cur_route == "perceive" else 0.0
            if e.fn == "owned" and e.args:
                # `owned(limb)` -- 1.0 if the part is currently owned, else 0.0.
                # Lets a defensive loop fire only for a limb that is actually
                # his: the flinch is the ownership illusion's proof.
                nm = e.args[0].name if isinstance(e.args[0], A.Ref) else None
                for k, v in self.owned.items():
                    if k == nm or k.endswith("." + str(nm)):
                        return 1.0 if v else 0.0
                return 0.0
            if e.fn == "belief" and e.args:
                # `belief(loop)` -- what a loop currently expects. A narrator may
                # read it; another loop may act on it. Nothing may read a Qualia.
                nm = e.args[0].name if isinstance(e.args[0], A.Ref) else None
                for ls in self.loops:
                    if ls.decl.name == nm or ls.decl.name.endswith("." + str(nm)):
                        return float(ls.belief)
                return 0.0
            if e.fn == "predict" and e.args:
                return self.label_of(e.args[0])
            if not e.args:
                return e.fn
            inner = ", ".join(self.label_of(a) for a in e.args)
            return f"{e.fn}({inner})"
        if isinstance(e, A.Bin):
            return f"{self.label_of(e.left)}{e.op}{self.label_of(e.right)}"
        return "?"

    def prec(self, spec, progress) -> float:
        if isinstance(spec, A.PrecRamp):
            return spec.start + (spec.end - spec.start) * progress
        if isinstance(spec, A.PrecExpr):
            # dynamic precision: read now, in the current scope. Clamped, because
            # a precision is a confidence, and confidences do not go negative.
            return max(0.0, self.num_of(spec.expr))
        return float(spec.value)

    # ---------- setup ----------
    def setup(self):
        check(self.prog, functional_only=self.functional_only)
        for lt in self.prog.lets:
            self.lets[lt.name] = self.num_of(lt.value)
        for body in self.prog.bodies:
            for ch in body.channels:
                self.channels[ch.name] = {
                    "value": ch.baseline, "baseline": ch.baseline,
                    "modality": ch.modality, "gain": ch.gain,
                    "efference": ch.efference,
                }
                self.channel_hist[ch.name] = []
        for r in self.prog.resources:
            self.resources[r.name] = {"cur": r.amount, "cap": r.amount}
            self.resource_hist[r.name] = []
        # Channels must all exist before any loop reads its prior: a loop may
        # predict a schema/image channel or a `flow` channel it does not sense.
        for emb in self.prog.embodiments:
            for (pname, sval, ival, tol) in emb.pairs:
                sc, ic = f"{pname}_schema", f"{pname}_image"
                self.channels[sc] = {"value": sval, "baseline": sval, "modality": "schema"}
                self.channels[ic] = {"value": ival, "baseline": ival, "modality": "image"}
                self.channel_hist[sc] = []
                self.channel_hist[ic] = []
                self.embody[pname] = {"schema": sc, "image": ic, "tol": tol}
        for fl in self.prog.flows:
            if fl.channel not in self.channels:
                self.channels[fl.channel] = {"value": 0.0, "baseline": 0.0, "modality": "intero"}
                self.channel_hist[fl.channel] = []
        for lp in self.prog.loops:
            self._cur_owner = lp.owner       # a prior is read in its own scope
            self.loops.append(LoopState(lp, self.num_of(lp.prior),
                                        self.label_of(lp.prior)))
        self._cur_owner = None
        for m in self.prog.moods:
            self.moods[m.name] = 0.0
            self.mood_hist[m.name] = []
        # --- 0.3 subsystems ---
        for a in self.prog.attentions:
            self.attention[a.name] = {"cur": a.capacity, "cap": a.capacity}
            self.attn_hist[a.name] = []
        for aw in self.prog.awarenesses:
            self.awareness[aw.name] = {"value": 0.0, "tracks": aw.tracks, "tau": aw.tau}
            self.aware_hist[aw.name] = []
        for ws in self.prog.workspaces:
            self.workspace[ws.name] = {"threshold": ws.threshold}
            self.ignition_hist[ws.name] = []
        for ow in self.prog.ownerships:
            self.owned[ow.name] = ow.initial

    # ---------- run ----------
    def run(self) -> Result:
        self.setup()
        dur, dt = self.prog.sim.duration, self.prog.sim.dt
        nframes = max(1, int(round(dur / dt)) + 1)
        cadence = getattr(self.prog.sim, "cadence", False)
        last_tick = {}
        for f in range(nframes):
            t = f * dt
            progress = f / (nframes - 1) if nframes > 1 else 1.0
            self.times.append(t)
            self._frame_emits = []
            self._frame_decisions = []
            self._frame_broadcasts = []
            self._frame_stimuli = set()

            self.mark_scene(t, f)
            self.replenish_attention(dt, t, f)
            self.apply_interventions(t, dt, f)
            self.fire_stimuli(t, dt, f)
            self.transmit_couples(dt, t, f)
            self.integrate_flows(dt, t, f)
            # settle loops fastest-first, honoring per-clock cadence if enabled
            for ls in sorted(self.loops, key=lambda l: CLOCK_PERIOD.get(l.decl.clock, 1.0)):
                if cadence and not self._ticks(ls.decl.clock, t, dt, last_tick):
                    continue
                self.settle(ls, progress, t, f)
            self._cur_owner = None
            self.check_embodiment(t, f)
            self.fire_somatic_memory(t, f)
            self.update_allostats(dt, t, f)
            self.update_workspace(t, f)
            self.update_awareness(dt, t, f)
            self.check_ownership(t, f)
            self.integrate_moods(t, f)
            self.narrate(t, f)
            self.run_handlers(progress, t, f)

            # snapshot histories
            for name, ch in self.channels.items():
                self.channel_hist[name].append(ch["value"])
            for name, v in self.moods.items():
                self.mood_hist[name].append(v)
            for name, r in self.resources.items():
                self.resource_hist[name].append(r["cur"])
            for name, a in self.attention.items():
                self.attn_hist[name].append(a["cur"])
            for name, aw in self.awareness.items():
                self.aware_hist[name].append(aw["value"])

        return Result(self.prog, self.chron, self.channel_hist, self.mood_hist,
                      self.resource_hist, self.times, self.functional_only,
                      self.attn_hist, self.aware_hist, self.ignition_hist, self)

    def _ticks(self, clock, t, dt, last_tick):
        period = CLOCK_PERIOD.get(clock, 1.0)
        if period <= dt:
            return True
        prev = last_tick.get(clock, -1e18)
        if t - prev >= period - 1e-9:
            last_tick[clock] = t
            return True
        return False

    def mark_scene(self, t, f):
        """Scenes give the Chronicle a narrative spine. Nothing about the
        physics changes; the novelist simply gets to read the trace in beats."""
        cur = None
        for sc in self.prog.scenes:
            if sc.t0 <= t <= sc.t1:
                cur = sc.title
                break
        if cur != self.scene:
            self.scene = cur
            if cur:
                self.chron.log(t, f, "scene", cur, note="scene begins")

    def transmit_couples(self, dt, t, f):
        """A's surface becomes B's sensation, delayed and attenuated.

        B never reads A's interior. He reads a face, `lag` seconds old, scaled
        by `gain` -- and then his own loops must guess at what produced it. The
        misreading is not a failure of the model; it is the model.

        A `stimulus` fired into the same channel this frame wins: the world can
        interrupt what a face was saying.
        """
        for cp in self.prog.couples:
            if cp.src not in self.channels or cp.dst not in self.channels:
                continue
            if cp.dst in self._frame_stimuli:
                self.chron.log(t, f, "couple", cp.src, to=cp.dst,
                               note="overridden by a stimulus this frame")
                continue
            if cp.lag > 0:
                back = int(round(cp.lag / dt))
                hist = self.channel_hist.get(cp.src, [])
                val = hist[-back] if len(hist) >= back and back > 0 else \
                    (hist[0] if hist else self.channels[cp.src]["value"])
            else:
                val = self.channels[cp.src]["value"]
            new = cp.gain * val
            if abs(new - self.channels[cp.dst]["value"]) > 1e-9:
                self.channels[cp.dst]["value"] = new
                self.chron.log(t, f, "couple", cp.src, to=cp.dst,
                               value=round(new, 2), lag=cp.lag)

    def replenish_attention(self, dt, t, f):
        """The spotlight is affine *within* a moment -- it cannot be spent twice,
        and what is spent is gone. Across moments it recovers, slowly, toward
        capacity. (Attention is a renewable scarcity, not a one-shot budget:
        that is what distinguishes it from the metabolic `resource`, which the
        body genuinely cannot conjure.)"""
        for name, spot in self.attention.items():
            if spot["cur"] < spot["cap"]:
                spot["cur"] = min(spot["cap"], spot["cur"] + ATTN_REGEN * spot["cap"])

    def fire_stimuli(self, t, dt, f):
        for stim in self.prog.stimuli:
            for (st, val) in stim.events:
                if t - dt < st <= t or (f == 0 and st <= 0):
                    if stim.channel in self.channels:
                        self.channels[stim.channel]["value"] = val
                        self._frame_stimuli.add(stim.channel)
                        self.chron.log(t, f, "stimulus", stim.channel, value=val)

    # ---------- the loop, settling ----------
    def settle(self, ls: LoopState, progress, t, f):
        lp = ls.decl
        self._cur_owner = lp.owner
        ch = self.channels.get(lp.sense)
        sense = ch["value"] if ch else 0.0
        modality = ch["modality"] if ch else "extero"

        # reafference: subtract the self-caused part of the signal (efference copy)
        if lp.efference and lp.efference in self._last_action:
            gain = ch.get("gain", 0.35) if ch else 0.35
            sense = sense - gain * self._last_action[lp.efference]

        pi_s = self.prec(lp.precision, progress)
        # conviction = declared prior precision + whatever experience has taught,
        # then globally scaled by any REBUS relaxation
        pi_p = (self.prec(lp.conviction, progress) + ls.learned) * self.rebus_factor
        # attenuation under dissociation. A handler names a scope; a scope is a
        # modality ("interoception", "proprioception", "exteroception") or the
        # bare word "self" for all of them. A loop whose sense lives in a
        # detached modality receives only ghost precision.
        if self._is_dissociated(modality):
            pi_s = ATTENUATED
        error = pi_s * (sense - ls.belief)

        if pi_s <= ATTENUATED:
            # A channel attenuated to the floor -- by dissociation, or by a
            # precision expression driven to zero -- carries no usable evidence.
            # It is ignored: the world cannot move the belief, and the belief
            # cannot be acted out on the strength of a signal this weak.
            route = "ignore"
        elif pi_s >= pi_p:
            route = "perceive"
        else:
            route = "act"

        # Overwhelm: a defended belief has a breaking point. Precision arbitration
        # lets high conviction suppress disconfirming evidence indefinitely -- which
        # is self-deception, and true to life until the evidence becomes undeniable.
        # While the loop suppresses, the raw surprise it refuses to look at
        # accumulates; once the debt exceeds the threshold, the belief can no longer
        # hold and is forced to perceive -- the mechanistic self-revelation.
        #
        # The threshold comes one of two ways:
        #   * `overwhelm: <n>`   -- an absolute debt bound the author sets.
        #   * `overwhelm: auto`  -- derived, with no author number, from the
        #     belief's own strengths: BREAK_K * (conviction / trust-in-evidence).
        #     A belief held harder (higher pi_p, including the hardening that `learn`
        #     adds each time it fires) needs proportionally more evidence to break;
        #     a belief that puts little trust in the disconfirming channel (low pi_s)
        #     is harder to break still. So *when* a lie breaks emerges from how
        #     strongly it is held versus how strong and trusted the evidence is,
        #     rather than from a hand-set moment. (This is the predictive-processing
        #     account: entrenched high-precision priors down-weight prediction error,
        #     and change comes only as precision-weighted evidence accumulates.)
        overwhelmed = False
        if lp.overwhelm_auto or (lp.overwhelm and lp.overwhelm > 0):
            # only *disconfirming* surprise counts toward the break: evidence that
            # reads higher than the held belief (the world is better/other than the
            # lie insists). Evidence that merely confirms the belief -- or falls
            # quiet -- lets the debt settle back, so a lie is never broken by the
            # very evidence that feeds it.
            raw = max(0.0, sense - ls.belief)
            if route == "act" and raw > FIRE_EPS:
                ls.overwhelm_debt += raw
            else:
                ls.overwhelm_debt *= 0.5
            if lp.overwhelm_auto:
                threshold = BREAK_K * pi_p / max(pi_s, 0.05)
            else:
                threshold = lp.overwhelm
            ls._overwhelm_bound = round(threshold, 3)
            if route == "act" and ls.overwhelm_debt >= threshold:
                route = "perceive"
                overwhelmed = True
                ls.overwhelm_debt = 0.0
                self.chron.log(t, f, "revelation", lp.name,
                               note="the belief could no longer suppress the evidence")

        self.chron.log(t, f, "settle", lp.name,
                       sense=round(sense, 2), belief=round(ls.belief, 2),
                       error=round(error, 2), pi_s=round(pi_s, 2),
                       pi_p=round(pi_p, 2), route=route,
                       debt=round(ls.overwhelm_debt, 3),
                       bound=getattr(ls, "_overwhelm_bound", None))

        self._cur_route = route

        fired = (abs(error) > FIRE_EPS or overwhelmed) and route != "ignore"
        if not fired:
            return

        # Habit formation. Every time a loop fires, the prior that drove it
        # gains a little confidence. This is how a body teaches a mind: not by
        # argument, but by repetition. It is also how love curdles -- a model
        # that keeps being confirmed stops being able to be surprised.
        if lp.learn:
            ls.learned = min(LEARN_CAP, ls.learned + lp.learn)
            if abs(ls.learned - lp.learn) < 1e-9:
                self.chron.log(t, f, "learn", lp.name, delta=lp.learn,
                               note="the prior begins to harden")

        # deliberation spends the attention spotlight; if starved, the loop
        # cannot act (habit loops are free -- dual-process control).
        spot = self._spotlight_of(lp.owner)
        if lp.mode == "deliberate" and spot is not None:
            cost = 1.0
            if spot["cur"] < cost:
                self.chron.log(t, f, "starved", lp.name,
                               note="no attention left to deliberate")
                return
            spot["cur"] -= cost

        for st in lp.act:
            # `<stmt> when <cond>`: an act that only sometimes happens. The
            # condition is read in the loop's own scope, at this instant.
            if isinstance(st, A.Guard):
                if not self.num_of(st.cond):
                    continue
                st = st.stmt
            if isinstance(st, A.Update):
                if route == "perceive":
                    ls.belief += 0.6 * (sense - ls.belief)   # learn toward sense
                else:
                    ls.belief += 0.1 * (sense - ls.belief)   # acting resists updating
                ls.label = self.label_of(st.target)
            elif isinstance(st, A.Move):
                self.exec_action(st.action, ls, t, f)
            elif isinstance(st, A.Ignore):
                # You suppress an error *because* your prior outranks your
                # senses. Once precision arbitration flips to `perceive` (as
                # after `rebus`), the same statement no longer silences the
                # world -- which is the whole point of relaxing a prior.
                if route == "act":
                    self.chron.log(t, f, "ignore", lp.name, note="error suppressed")
            elif isinstance(st, A.Emit):
                self.emit(st.feel.quale, ls, ch, t, f)
            elif isinstance(st, A.Broadcast):
                label = self.label_of(st.content)
                sal = self.num_of(st.salience) if st.salience is not None else abs(error)
                self._frame_broadcasts.append((label, sal, lp.name))
                self.chron.log(t, f, "broadcast", lp.name, content=label,
                               salience=round(sal, 2))
            elif isinstance(st, A.Attend):
                self._do_attend(st, ls, error, t, f)

    def exec_action(self, call: A.Call, ls: LoopState, t, f):
        fn = call.fn
        if fn == "spend" and call.args:
            rname = self._res(call.args[0].name, self.resources) \
                if isinstance(call.args[0], A.Ref) else None
            amt = self.num_of(call.args[1]) if len(call.args) > 1 else 0.0
            if rname in self.resources:
                cur = self.resources[rname]["cur"]
                spent = min(cur, amt)
                self.resources[rname]["cur"] = cur - spent
                self.chron.log(t, f, "spend", ls.decl.name, resource=rname,
                               asked=amt, spent=round(spent, 1),
                               left=round(cur - spent, 1))
                if spent < amt:
                    self.chron.log(t, f, "budget", ls.decl.name,
                                   note=f"body cannot conjure {amt - spent:.0f} {rname}")
            return
        if fn == "set" and len(call.args) >= 2:
            cname = self._res(call.args[0].name, self.channels) \
                if isinstance(call.args[0], A.Ref) else None
            val = self.num_of(call.args[1])
            if cname in self.channels:
                prev = self.channels[cname]["value"]
                self.channels[cname]["value"] = val
                self.chron.log(t, f, "drive", ls.decl.name, channel=cname,
                               to=round(val, 1))
                # An efference copy predicts the *change* one's own action makes,
                # not the absolute state of the world afterwards. Subtracting the
                # absolute value would have the organism deny its own existence.
                self._last_action[ls.decl.name] = val - prev
            return
        # otherwise: a labeled bodily action = a decision
        label = self.label_of(call)
        self.chron.log(t, f, "move", ls.decl.name, action=label,
                       via=ls.decl.sense)
        self._last_action.setdefault(ls.decl.name, 1.0)
        self._frame_decisions.append((ls.decl.name, ls.decl.sense, label, t))

    def _spotlight_of(self, owner):
        """A character spends only their own attention.

        If `owner` declared a spotlight, that is the one charged. Otherwise an
        unscoped (single-character) spotlight is used. A character who declared
        none simply has no attentional economy modelled -- and, crucially, may
        not spend someone else's. Nadia's capacity to attend is not a resource
        available to Hal, however much of it he takes up."""
        if owner:
            for a in self.attention:
                if a.startswith(f"{owner}."):
                    return self.attention[a]
            return None
        for a in self.attention:
            if "." not in a:
                return self.attention[a]
        return next(iter(self.attention.values())) if self.attention else None

    def _do_attend(self, st: A.Attend, ls, error, t, f):
        spot = self._spotlight_of(ls.decl.owner)
        if spot is None:
            return
        cost = self.num_of(st.cost) if st.cost is not None else 1.0
        got = min(spot["cur"], cost)
        spot["cur"] -= got
        self.chron.log(t, f, "attend", ls.decl.name, target=st.target,
                       cost=round(got, 2), left=round(spot["cur"], 2))
        if got < cost:
            self.chron.log(t, f, "starved", ls.decl.name,
                           note=f"attention spotlight exhausted at {st.target}")

    # ---------- 0.3 subsystems ----------
    def apply_interventions(self, t, dt, f):
        for iv in self.prog.interventions:
            if iv.kind == "rebus" and t - dt < iv.at <= t:
                self.rebus_factor = max(0.02, 1.0 - iv.strength)
                self.chron.log(t, f, "rebus", "intervention",
                               strength=iv.strength,
                               note="high-level priors relaxed (REBUS)")

    def integrate_flows(self, dt, t, f):
        """Continuous physiology by Heun's method (predictor-corrector), the
        hybrid continuous/discrete substrate the spec calls for.

        All flows advance in lock-step: within each substep every flow's
        derivative is evaluated against the SAME frozen state, then all channels
        are updated together. This is what makes a coupled system
        (dx = -x, dy = +x) conserve correctly -- integrating flows one at a time
        would let a later flow read an already-half-integrated channel."""
        import math as _m
        flows = self.prog.flows
        if not flows:
            return
        SUB = 8
        h = dt / SUB
        # snapshot starting values, for the instability fallback
        start = {fl.channel: self.channels[fl.channel]["value"] for fl in flows}
        for _ in range(SUB):
            # predictor: all derivatives against the current (frozen) state
            base = {fl.channel: self.channels[fl.channel]["value"] for fl in flows}
            k1 = {}
            for fl in flows:
                self._cur_owner = fl.owner
                k1[fl.channel] = self.num_of(fl.dynamics)
            # step every channel to its Euler predictor
            for fl in flows:
                self.channels[fl.channel]["value"] = base[fl.channel] + h * k1[fl.channel]
            # corrector: derivatives at the predicted state
            k2 = {}
            for fl in flows:
                self._cur_owner = fl.owner
                k2[fl.channel] = self.num_of(fl.dynamics)
            # Heun update for every channel at once
            for fl in flows:
                v = base[fl.channel] + 0.5 * h * (k1[fl.channel] + k2[fl.channel])
                if not _m.isfinite(v):
                    # A stiff flow (tau << dt) can blow up under explicit
                    # integration. Pin to the last good value and record the
                    # instability rather than poisoning the Chronicle with NaN.
                    hist = self.channel_hist[fl.channel]
                    v = hist[-1] if hist else start[fl.channel]
                    self.chron.log(t, f, "unstable", fl.channel,
                                   note="flow tau is much smaller than dt; clamped")
                self.channels[fl.channel]["value"] = v
        self._cur_owner = None

    def check_embodiment(self, t, f):
        """Body schema vs body image: when they diverge past tolerance, that is
        a phantom limb / depersonalization / anorexia -- a formal event."""
        for pname, d in self.embody.items():
            s = self.channels[d["schema"]]["value"]
            i = self.channels[d["image"]]["value"]
            if abs(s - i) > d["tol"]:
                self.chron.log(t, f, "conflict", pname, pair=pname,
                               schema=round(s, 1), image=round(i, 1),
                               note="body schema and body image disagree")

    def fire_somatic_memory(self, t, f):
        """A somatic memory can fire -- biasing affect -- without any episodic
        trace: the body remembering what the mind cannot recall."""
        for mem in self.prog.memories:
            self._cur_owner = mem.owner
            if mem.cue not in self.channels:
                continue
            # evaluate `when` with channels in scope
            hit = self.num_of(mem.when) if mem.when is not None else 0.0
            if hit:
                if mem.register == "somatic":
                    _q = Qualia(mem.evoke)
                    self.chron.log(t, f, "somatic", mem.name, quale=repr(_q),
                                   register=mem.register, cue=mem.cue,
                                   note="somatic memory fired without episodic trace")
                    self._frame_emits.append((mem.evoke, mem.name, mem.cue))
                else:
                    self.chron.log(t, f, "recall", mem.name, register=mem.register,
                                   cue=mem.cue)
        self._cur_owner = None

    def update_allostats(self, dt, t, f):
        """Predictive (allostatic) regulation: pre-emptively drive a channel
        toward its set point, spending budget in advance. Ported from ilion's
        Allostasis model."""
        for al in self.prog.allostats:
            self._cur_owner = al.owner
            if al.regulate not in self.channels:
                continue
            sensed = self.channels[al.regulate]["value"]
            drive = al.gain * (al.setpoint - sensed)
            self.channels[al.regulate]["value"] = sensed + drive * dt
            if al.resource and al.resource in self.resources and abs(drive) > 0.01:
                cost = min(self.resources[al.resource]["cur"], abs(drive))
                self.resources[al.resource]["cur"] -= cost
            self.chron.log(t, f, "allostat", al.name, regulate=al.regulate,
                           drive=round(drive, 2), toward=al.setpoint)
        self._cur_owner = None

    def update_workspace(self, t, f):
        """Global workspace: coalitions compete; the winner is amplified and, if
        it dominates strongly enough, broadcast globally (Dehaene's ignition is
        winner-take-all with recurrent amplification -- a nonlinear, all-or-none
        transition). We score dominance rather than field coherence: a content
        ignites when it is both salient and clearly beats its rival. Below
        threshold the content is processed locally and dies -- felt, never known.

        (ilion's `ignition_index` -- mean activity x pairwise coherence -- stays
        available as a callable builtin for authors who want that read-out; it
        answers a different question, namely whether a field is synchronised.)
        """
        for name, ws in self.workspace.items():
            if not self._frame_broadcasts:
                self.ignition_hist[name].append(0.0)
                continue
            sals = sorted((s for (_l, s, _w) in self._frame_broadcasts), reverse=True)
            top = sals[0]
            second = sals[1] if len(sals) > 1 else 0.0
            dominance = (top - second) / top if top > 1e-9 else 0.0
            idx = top * (0.5 + 0.5 * dominance)
            winner = max(self._frame_broadcasts, key=lambda b: b[1])
            self.ignition_hist[name].append(idx)
            if idx >= ws["threshold"]:
                self.chron.log(t, f, "ignite", name, content=winner[0],
                               index=round(idx, 2), by=winner[2],
                               note="content won the workspace and was broadcast")
            else:
                self.chron.log(t, f, "local", name, content=winner[0],
                               index=round(idx, 2),
                               note="processed locally; died below threshold")

    def update_awareness(self, dt, t, f):
        """Graziano attention schema: awareness is a lagged, transparent model
        of attention -- usable, not introspectable (see checker)."""
        for name, aw in self.awareness.items():
            spot = self.attention.get(aw["tracks"])
            if not spot:
                continue
            attn = spot["cur"] / spot["cap"] if spot["cap"] else 0.0
            aw["value"] += (attn - aw["value"]) * min(1.0, dt / aw["tau"])

    def check_ownership(self, t, f):
        """Body-ownership as a dependent type: when predicted and observed
        proprioception match within tolerance, the part is owned; when they
        diverge (or a synchronous illusion drives them together) ownership
        migrates -- the rubber-hand illusion as a type-level event."""
        for ow in self.prog.ownerships:
            if ow.predicted not in self.channels or ow.observed not in self.channels:
                continue
            p = self.channels[ow.predicted]["value"]
            o = self.channels[ow.observed]["value"]
            match = abs(p - o) <= ow.tolerance
            if match != self.owned.get(ow.name, True):
                self.owned[ow.name] = match
                self.chron.log(t, f, "ownership", ow.name,
                               state="owned" if match else "disowned",
                               predicted=round(p, 1), observed=round(o, 1),
                               note=("ownership migrated -- this feels like mine"
                                     if match else
                                     "ownership lost -- this feels alien"))

    def emit(self, quale, ls, ch, t, f):
        if self.functional_only:
            self.chron.log(t, f, "emit", ls.decl.name, quale=f"[{quale}]", note="functional-only")
            self._frame_emits.append((quale, ls.decl.name, ls.decl.sense))
            return
        # under dissociation, feeling in the detached modality flattens to numbness
        if ch and self._is_dissociated(ch["modality"]):
            quale = "numbness"
        _q = Qualia(quale)   # opaque; created but never inspected
        self.chron.log(t, f, "emit", ls.decl.name, quale=repr(_q))
        self._frame_emits.append((quale, ls.decl.name, ls.decl.sense))

    # ---------- mood: the slow variable ----------
    def integrate_moods(self, t, f):
        for m in self.prog.moods:
            val = self.moods[m.name]
            contrib = 0.0
            for (src, w) in m.integrates:
                for (quale, loop, chan) in self._frame_emits:
                    if src in (quale, loop):
                        contrib += w * VALENCE.get(quale, -0.5)
            val = m.decay * val + contrib
            self.moods[m.name] = val
            if abs(contrib) > 1e-9:
                self.chron.log(t, f, "mood", m.name, value=round(val, 3),
                               delta=round(contrib, 3))

    # ---------- the narrator, and its errors ----------
    def narrate(self, t, f):
        for nar in self.prog.narrators:
            subs = set(nar.subscribes)
            # 1) voice the feelings we can see
            for (quale, loop, chan) in self._frame_emits:
                if loop not in subs:
                    continue
                line = nar.voice.get(quale)
                if line:
                    # authored line that downplays distress => confabulation gap
                    gap = 0.55 if VALENCE.get(quale, 0) < -0.3 else 0.1
                else:
                    line = self._voiced(quale)
                    gap = 0.15
                self.chron.log(t, f, "narrate", nar.name, quote=line,
                               about=quale, gap=round(gap, 2))
            # 2) explain the decisions -- confabulating for what we cannot see
            for (loop, chan, action, dt_) in self._frame_decisions:
                # A narrator speaks only for its own character. The interpreter
                # invents reasons for actions it did not witness -- but they must
                # be ITS OWN actions. Nobody confabulates on behalf of a stranger.
                if nar.owner and not loop.startswith(f"{nar.owner}."):
                    continue
                if loop in subs:
                    quote = nar.voice.get(action) or (
                        f"I chose to {self._human(action)}; it was the thing to do.")
                    gap = 0.15
                elif nar.confabulates:
                    # invent a reason from whatever loop we *can* see
                    seen = self._belief_of_subscribed(subs)
                    # A confabulation needs a *reason*, not a number. If the only
                    # thing the interpreter can see is a bare quantity, it does
                    # what people do: it says it felt right.
                    reason = self._human(seen) if seen else ""
                    if reason.replace(".", "").replace("-", "").isdigit():
                        reason = ""
                    quote = nar.voice.get(action) or (
                        f"I {self._human(action)} because {reason}."
                        if reason else f"I {self._human(action)}; it just felt right.")
                    gap = 0.97
                else:
                    continue
                self.chron.log(t, f, "narrate", nar.name,
                               quote=quote, about=action, gap=round(gap, 2))

    @staticmethod
    def _human(label):
        """`turn_toward(the_cold_half)` -> `turn toward the cold half`. The
        narrator speaks English, not identifiers."""
        lab = label.replace("(", " ").replace(")", "").replace(",", "")
        return lab.replace("_", " ").strip()

    def _voiced(self, quale):
        table = {
            "dread": "Something is wrong.", "delight_at_error": "You surprise me.",
            "delight": "Oh -- I didn't expect that.", "reaching": "You're still here, aren't you.",
            "joy": "God, it's good to be alive.",
            "grief": "I miss you.", "pain": "It hurts again.", "numbness": "I feel nothing.",
            "warmth": "This is good.", "love": "I could watch you all day.",
            "calm": "I'm alright. Everything's alright.",
            "shame": "I shouldn't have said anything.",
            "terror": "I have to get out.", "anguish": "I can't -- I can't.",
            "relief": "Oh, thank God.", "hope": "Maybe. Maybe this time.",
            "recognition": "I know that. I know that from somewhere.",
            "despair": "What's the point.", "panic": "I can't breathe.",
            "contempt": "Yes, yes. I know. You've said.",
            "unease": "I don't know why. I just feel it sometimes.",
            "disquiet": "Nothing's wrong. I just can't settle.",
            "foreboding": "Something's coming. I can feel it.",
            "longing": "I keep thinking about it.", "yearning": "If only.",
            "tenderness": "Oh, you.", "apprehension": "I have a bad feeling.",
            "desolation": "There's nothing left in me.",
            "wariness": "I'm watching. I'm always watching.",
            "comfort": "There. That's better.", "safety": "I'm safe here.",
            "wonder": "I've never seen anything like it.", "anger": "How dare they.",
            "self_betrayal": "That isn't who I am. That isn't who I am.",
            "worthlessness": "I don't count. I never did.",
            "pride": "There. You saw that. You all saw that.",
            "ambivalence": "I don't know what I want.", "resolve": "No. This, and not that.",
        }
        return table.get(quale, f"I feel {quale}.")

    def _belief_of_subscribed(self, subs):
        for ls in self.loops:
            if ls.decl.name in subs:
                return ls.label
        return None

    # ---------- trauma: crash & repair ----------
    _MOD_SCOPE = {"intero": "interoception", "proprio": "proprioception",
                  "extero": "exteroception", "schema": "proprioception",
                  "image": "proprioception"}

    def _is_dissociated(self, modality):
        if self.dissociated.get("self"):
            return True
        scope = self._MOD_SCOPE.get(modality)
        return bool(scope and self.dissociated.get(scope))

    def run_handlers(self, progress, t, f):
        # per-loop error this frame, and the global worst. A handler may key off
        # a specific loop -- `when error(the_body) > 5.5` -- so that each
        # supervision band watches its own subsystem, not the loudest one.
        self._frame_errors = {e.who: abs(e.detail.get("error", 0.0))
                              for e in self.chron.of_kind("settle") if e.frame == f}
        worst = max(self._frame_errors.values(), default=0.0)
        for h in self.prog.handlers:
            crash_scopes = [sc for (_, sc, _) in h.on_crash] or ["interoception"]
            # crash: fire when the condition holds and this scope is attached
            if h.when is not None:
                for (kind, scope, titr) in h.on_crash:
                    if kind == "dissociate" and not self.dissociated.get(scope):
                        if self._cond(h.when, worst):
                            self.dissociated[scope] = True
                            self.dissoc_start[scope] = t
                            self.chron.log(t, f, "crash", h.name, scope=scope,
                                           note=f"detached from {scope}")
            # repair: fire once the dwell time has elapsed, then re-arm so that a
            # later crash can be repaired again -- dissociation is a cycle, not a
            # one-way door.
            if h.after is not None:
                for (kind, scope, titr) in h.repair:
                    if kind == "reattach" and self.dissociated.get(scope):
                        start = self.dissoc_start.get(scope, 0.0)
                        if t - start >= h.after:
                            self.dissociated[scope] = False
                            self.chron.log(t, f, "repair", h.name, scope=scope,
                                           titrate=titr,
                                           note=f"{scope} slowly re-supervised")

    def _cond(self, cond, worst):
        errmap = getattr(self, "_frame_errors", {})

        def resolve_error_call(e):
            if isinstance(e, A.Call) and e.fn == "error" and e.args:
                nm = e.args[0].name if isinstance(e.args[0], A.Ref) else None
                for who, val in errmap.items():
                    if who == nm or who.endswith("." + str(nm)):
                        return val
                return 0.0
            return None

        if isinstance(cond, A.Bin):
            def side(e):
                hit = resolve_error_call(e)
                if hit is not None:
                    return hit
                if isinstance(e, A.Ref) and e.name == "error":
                    return worst
                if isinstance(e, A.Ref) and e.name in self.lets:
                    return self.lets[e.name]
                return self.num_of(e)
            l, r = side(cond.left), side(cond.right)
            return {"<": l < r, ">": l > r, "<=": l <= r, ">=": l >= r,
                    "==": l == r, "!=": l != r}.get(cond.op, False)
        return False


def run_source(src: str, title="untitled", functional_only=False) -> Result:
    from .parser import parse
    prog = parse(src, title=title)
    return Interpreter(prog, functional_only=functional_only).run()
