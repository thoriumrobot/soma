"""
SOMA static checker (the 'compile-time' pass).

Three checks encode the language's ethical and metaphysical commitments:

1. CONSENT GATING. Any program that can `emit feel(<distress>)` or `dissociate`
   must carry a matching `@consent(...)` annotation naming what it simulates.
   Runs unless the interpreter is in functional-only mode.

2. QUALIA OPACITY. A `feel(...)` value (Qualia) may never be an operand of
   arithmetic/comparison or be passed where a physical number is expected
   (spend/set). The explanatory gap is a compiler error.

3. AFFINE RESOURCES. A resource may be moved/split, but a resource identifier
   may not be *re-bound* after it has been consumed. (Runtime also refuses to
   overspend -- the body cannot conjure what it does not have.)
"""

from __future__ import annotations
from . import ast_nodes as A

DISTRESS = {"dread", "pain", "despair", "grief", "terror", "panic",
            "shame", "anguish", "reaching", "numbness",
            "desolation", "foreboding", "apprehension", "self_betrayal",
            "worthlessness"}


class SomaTypeError(Exception):
    pass


class ConsentError(Exception):
    pass


def _expr_has_feel(e) -> bool:
    if isinstance(e, A.Feel):
        return True
    if isinstance(e, A.Bin):
        return _expr_has_feel(e.left) or _expr_has_feel(e.right)
    if isinstance(e, A.Call):
        return any(_expr_has_feel(a) for a in e.args)
    return False


def check(prog: A.Program, functional_only: bool = False):
    _check_qualia_opacity(prog)
    _check_affine(prog)
    _check_transparency(prog)
    _check_other_minds(prog)
    _check_wellformed(prog)
    if not functional_only:
        _check_consent(prog)


def _check_other_minds(prog: A.Program):
    """No character may sense another's interior directly.

    A loop belonging to Bob may `sense` Bob's own channels, or an *exteroceptive*
    channel of Alice's (a face, a voice, a hand) -- but never Alice's
    interoception. Other minds are reached only through surfaces, and only via
    `couple`, which imposes gain and lag. This is the formal content of Sartre's
    look and Levinas's face: the other is given to me as an exterior I must
    interpret, never as an interior I can read.

    (A `couple` may write into any of the recipient's own channels: what Bob
    does with what he sees is his business.)
    """
    modality = {}
    for b in prog.bodies:
        for ch in b.channels:
            modality[ch.name] = ch.modality

    def owner(n):
        return n.split(".")[0] if "." in n else None

    for lp in prog.loops:
        if not lp.owner or not lp.sense:
            continue
        src = owner(lp.sense)
        if src and src != lp.owner and modality.get(lp.sense) == "intero":
            raise SomaTypeError(
                f"loop {lp.name!r} senses {lp.sense!r}: {lp.owner} cannot read "
                f"{src}'s interoception. Another mind is given only as a surface "
                f"-- couple an exteroceptive channel instead, and let {lp.owner} "
                f"do the guessing."
            )

    for cp in prog.couples:
        if owner(cp.src) and owner(cp.dst) and owner(cp.src) != owner(cp.dst):
            if modality.get(cp.src) == "intero":
                raise SomaTypeError(
                    f"couple {cp.src} -> {cp.dst}: {cp.src!r} is interoceptive. "
                    f"A body's inside is not visible from outside it. Couple a "
                    f"face, a voice, a posture -- something the world can see."
                )


def _check_transparency(prog: A.Program):
    """Graziano's attention schema is *transparent*: the system uses it as if it
    were the world, and cannot see it as a model. Adapted from ilion's
    `transparent`/`introspect` rule: `introspect(<awareness>)` is a static
    error, for the same reason `Qualia<T>` has no accessor. The model's
    inability to see itself as a model is a type rule, not a comment.
    """
    aware_names = {a.name for a in prog.awarenesses}

    def scan(e):
        if isinstance(e, A.Call):
            if e.fn == "introspect":
                tgt = e.args[0].name if e.args and isinstance(e.args[0], A.Ref) else "?"
                if tgt in aware_names:
                    raise SomaTypeError(
                        f"introspect({tgt}): an attention schema is transparent. "
                        f"The system may use it to report and to steer, but cannot "
                        f"see it as a model of itself (Graziano). This is a type "
                        f"rule, not a comment."
                    )
            for a in e.args:
                scan(a)
        if isinstance(e, A.Bin):
            scan(e.left); scan(e.right)

    for lp in prog.loops:
        scan(lp.prior)
        for spec in (lp.precision, lp.conviction):
            if isinstance(spec, A.PrecExpr):
                scan(spec.expr)
        for st in lp.act:
            if isinstance(st, A.Guard):
                scan(st.cond)
                st = st.stmt
            if isinstance(st, A.Update):
                scan(st.target)
            elif isinstance(st, A.Move):
                scan(st.action)
            elif isinstance(st, A.Broadcast):
                scan(st.content)
                if st.salience is not None:
                    scan(st.salience)


def _check_wellformed(prog: A.Program):
    """Names must resolve: an awareness must track a declared attention; an
    ownership must reference declared channels; a memory must cue a channel."""
    attn = {a.name for a in prog.attentions}
    chans = {c.name for b in prog.bodies for c in b.channels}
    chans |= {f"{p[0]}_schema" for e in prog.embodiments for p in e.pairs}
    chans |= {f"{p[0]}_image" for e in prog.embodiments for p in e.pairs}
    chans |= {fl.channel for fl in prog.flows}
    for aw in prog.awarenesses:
        if aw.tracks not in attn:
            raise SomaTypeError(
                f"awareness {aw.name!r} tracks {aw.tracks!r}, which is not a "
                f"declared attention spotlight.")
    for ow in prog.ownerships:
        for fld in (ow.predicted, ow.observed):
            if fld not in chans:
                raise SomaTypeError(
                    f"ownership {ow.name!r} references undeclared channel {fld!r}.")
    for m in prog.memories:
        if m.register not in ("episodic", "semantic", "procedural", "somatic"):
            raise SomaTypeError(
                f"memory {m.name!r}: unknown register {m.register!r}; expected one of "
                f"episodic, semantic, procedural, somatic.")
        if m.cue not in chans:
            raise SomaTypeError(
                f"memory {m.name!r} is cued by undeclared channel {m.cue!r}.")
    for lp in prog.loops:
        if lp.mode not in ("habit", "deliberate"):
            raise SomaTypeError(
                f"loop {lp.name!r}: mode must be 'habit' or 'deliberate', "
                f"not {lp.mode!r} (dual-process control).")

    # A loop's `sense` must name a channel that exists, or the loop silently
    # never fires -- the single most confusing failure mode, since nothing is
    # reported and the story just comes out empty. Build the full set of
    # channels the runtime knows about (declared, flow-driven, schema/image,
    # and stimulus targets), then flag any sense that resolves to none of them.
    # Cross-character exteroceptive senses (Alice reading `Bob.face`) are fine
    # as long as the channel is declared on the owner's body.
    known = set(chans)
    known |= {s.channel for s in getattr(prog, "stimuli", [])}
    # channels a couple writes into come into being at runtime too
    known |= {cp.dst for cp in prog.couples}
    known |= {cp.src for cp in prog.couples}
    for lp in prog.loops:
        if not lp.sense:
            continue
        sense = lp.sense
        # a bare name owned implicitly by the loop's character may appear either
        # bare or as "<owner>.<name>"; accept either spelling
        candidates = {sense}
        if lp.owner and "." not in sense:
            candidates.add(f"{lp.owner}.{sense}")
        if "." in sense:
            candidates.add(sense.split(".", 1)[1])
        if not (candidates & known):
            raise SomaTypeError(
                f"loop {lp.name!r} senses {sense!r}, which is not a declared "
                f"channel (nor a stimulus target or coupled channel). This "
                f"would leave the loop silently inert. Check for a typo, or "
                f"declare the channel on a body.")

    # Clock names are drawn from a fixed set; an unrecognized one is almost
    # always a typo (`@carfiac`), and would silently tick at the wrong rate.
    CLOCKS = {"neural", "cardiac", "breath", "mood", "hormonal",
              "circadian", "biography", "lineage"}
    for kind, items in (("loop", prog.loops), ("body", prog.bodies),
                        ("flow", prog.flows), ("mood", prog.moods),
                        ("narrator's body", [])):
        for it in items:
            clk = getattr(it, "clock", None)
            if clk is not None and clk not in CLOCKS:
                raise SomaTypeError(
                    f"{kind} {getattr(it, 'name', getattr(it, 'channel', '?'))!r} "
                    f"runs on @{clk}, which is not one of the eight clocks "
                    f"({', '.join(sorted(CLOCKS))}). Check for a typo.")


def _check_qualia_opacity(prog: A.Program):
    # feel(...) may only appear as the whole RHS of `emit`, never inside
    # arithmetic, comparison, or as an argument to spend/set/predict.
    def scan_expr(e, ctx):
        if isinstance(e, A.Feel):
            raise SomaTypeError(
                f"Qualia<{e.quale}> used in {ctx}: a phenomenal value cannot be "
                f"coerced to the physical (this is the explanatory gap, by design)."
            )
        if isinstance(e, A.Bin):
            scan_expr(e.left, "an arithmetic/comparison expression")
            scan_expr(e.right, "an arithmetic/comparison expression")
        if isinstance(e, A.Call):
            for a in e.args:
                scan_expr(a, f"a call to {e.fn}(...)")

    for lt in prog.lets:
        scan_expr(lt.value, "a let binding")
    for lp in prog.loops:
        scan_expr(lp.prior, "a prior")
        for spec in (lp.precision, lp.conviction):
            if isinstance(spec, A.PrecExpr):
                scan_expr(spec.expr, "a precision")
        for st in lp.act:
            if isinstance(st, A.Guard):
                scan_expr(st.cond, "a `when` guard")
                st = st.stmt
            if isinstance(st, A.Update):
                scan_expr(st.target, "an update target")
            elif isinstance(st, A.Move):
                for a in st.action.args:
                    scan_expr(a, f"a move action {st.action.fn}(...)")
            elif isinstance(st, A.Broadcast):
                scan_expr(st.content, "a broadcast into the global workspace")
                if st.salience is not None:
                    scan_expr(st.salience, "a salience weight")
            # Emit is the one legal home of feel(...); nothing to check.
    for fl in prog.flows:
        scan_expr(fl.dynamics, "a continuous flow equation")
    for mem in prog.memories:
        if mem.when is not None:
            scan_expr(mem.when, "a memory cue condition")
    for al in prog.allostats:
        # setpoint is a scalar in the AST, but guard against a future expr form
        if not isinstance(al.setpoint, (int, float)):
            scan_expr(al.setpoint, "an allostat setpoint")


def _check_affine(prog: A.Program):
    resources = {r.name for r in prog.resources}
    # A resource name may not be the target of a `let` (re-binding a moved
    # resource). This is a lightweight stand-in for full affine tracking; the
    # runtime enforces non-negativity too.
    for lt in prog.lets:
        if lt.name in resources:
            raise SomaTypeError(
                f"affine resource {lt.name!r} re-bound by let: an affine value "
                f"is used at most once and cannot be copied."
            )


def _check_consent(prog: A.Program):
    needs = set()
    for lp in prog.loops:
        for st in lp.act:
            if isinstance(st, A.Guard):
                st = st.stmt
            if isinstance(st, A.Emit) and st.feel.quale in DISTRESS:
                needs.add(st.feel.quale)
    for mem in prog.memories:
        if mem.evoke in DISTRESS:
            needs.add(mem.evoke)
    for h in prog.handlers:
        for (kind, scope, _titr) in h.on_crash:
            if kind == "dissociate":
                needs.add("dissociation")
    for iv in prog.interventions:
        if iv.kind == "rebus":
            needs.add("an altered state (REBUS)")
    if needs and not prog.consent:
        raise ConsentError(
            "this program simulates distress ("
            + ", ".join(sorted(needs))
            + ") but carries no @consent(...) annotation. Add one naming what is "
            "simulated, or run in --functional-only mode."
        )
