"""
soma.perturb -- the novelist's real instrument (spec section 11.6).

    "Change one precision schedule, re-run, and watch the whole life
     reorganize. This is SOMA's real gift to a novelist: not answers, but
     legible causality."

`perturb` takes a program, mutates exactly one dial, runs both versions against
the same schedule, and reports the *difference in the story*: which storyful
patterns appeared, which vanished, which feelings arrived earlier or not at all.

The point is not that the perturbed run is better. The point is that the
difference is attributable. A novelist can say: *she is like this because her
conviction is 0.95, and if it were 0.4 she would be a different woman, and here
is exactly how.*
"""

from __future__ import annotations
import copy
from dataclasses import dataclass

from . import ast_nodes as A
from .parser import parse
from .interpreter import Interpreter
from . import winnow


class PerturbError(Exception):
    pass


LOOP_FIELDS = ("precision", "conviction", "learn", "mode", "overwhelm")
OTHER_FIELDS = ("threshold", "capacity", "gain", "lag", "setpoint", "strength")


def _match(items, name):
    return [x for x in items if x.name == name or x.name.endswith("." + name)]


def apply_set(prog: A.Program, spec: str) -> str:
    """Apply `name.field=value`.

    Loops take `precision`, `conviction`, `learn`, `mode`. But the questions a
    novelist most wants to ask are often not about a loop at all:

        workspace.threshold  -- what if she had been able to notice?
        spotlight.capacity   -- what if she had not been so tired?
        memory.strength      -- what if the body remembered less loudly?
        couple.gain / .lag   -- what if he had been quicker to read her face?

    Names may be bare or character-qualified (`Nadia.spotlight`).
    """
    if "=" not in spec or "." not in spec.split("=")[0]:
        raise PerturbError(f"expected name.field=value, got {spec!r}")
    lhs, rhs = spec.split("=", 1)
    *parts, field = lhs.split(".")
    name = ".".join(parts)

    # --- non-loop dials
    if field in OTHER_FIELDS:
        for ws in _match(prog.workspaces, name):
            if field == "threshold":
                old, ws.threshold = ws.threshold, float(rhs)
                return f"{ws.name}.threshold: {old} -> {ws.threshold}"
        for at in _match(prog.attentions, name):
            if field == "capacity":
                old, at.capacity = at.capacity, float(rhs)
                return f"{at.name}.capacity: {old} -> {at.capacity}"
        for m in _match(prog.memories, name):
            if field == "strength":
                old, m.strength = m.strength, float(rhs)
                return f"{m.name}.strength: {old} -> {m.strength}"
        for al in _match(prog.allostats, name):
            if field == "setpoint":
                old, al.setpoint = al.setpoint, float(rhs)
                return f"{al.name}.setpoint: {old} -> {al.setpoint}"
        for cp in prog.couples:
            if cp.src == name or cp.src.endswith("." + name):
                if field in ("gain", "lag"):
                    old = getattr(cp, field)
                    setattr(cp, field, float(rhs))
                    return f"couple {cp.src}->{cp.dst}.{field}: {old} -> {rhs}"

    if field not in LOOP_FIELDS:
        raise PerturbError(
            f"cannot perturb {field!r}; loops take {LOOP_FIELDS}, "
            f"and workspaces/attentions/memories/couples take {OTHER_FIELDS}")

    targets = _match(prog.loops, name)
    if not targets:
        names = ", ".join(lp.name for lp in prog.loops)
        raise PerturbError(f"no loop named {name!r}. Loops: {names}")

    loop_name = name
    desc = []
    for lp in targets:
        if field == "mode":
            old, lp.mode = lp.mode, rhs.strip()
            desc.append(f"{lp.name}.mode: {old} -> {lp.mode}")
        elif field == "learn":
            old, lp.learn = lp.learn, float(rhs)
            desc.append(f"{lp.name}.learn: {old} -> {lp.learn}")
        elif field == "overwhelm":
            old, lp.overwhelm = lp.overwhelm, float(rhs)
            desc.append(f"{lp.name}.overwhelm: {old} -> {lp.overwhelm}")
        else:
            val = float(rhs)
            old = getattr(lp, field)
            olds = (f"ramp({old.start}->{old.end})"
                    if isinstance(old, A.PrecRamp) else f"{old.value}")
            setattr(lp, field, A.PrecConst(val))
            desc.append(f"{lp.name}.{field}: {olds} -> {val}")
    return "; ".join(desc)


@dataclass
class Diff:
    change: str
    gained: list      # findings present only in the perturbed run
    lost: list        # findings present only in the original
    shifted: list     # (pattern, base_score, new_score)
    base_result: object
    new_result: object


def _key(f):
    return (f.pattern, f.text.split("--")[0][:60])


def perturb(src: str, spec, title="untitled", functional_only=False) -> Diff:
    """`spec` is one `name.field=value`, or a list of them: a life differs from
    another life in more than one dial, and often the interesting counterfactual
    is a conjunction (`he held it loosely` AND `he did not harden`)."""
    specs = [spec] if isinstance(spec, str) else list(spec)
    base_prog = parse(src, title=title)
    new_prog = parse(src, title=title)
    change = "; ".join(apply_set(new_prog, sp) for sp in specs)

    base = Interpreter(base_prog, functional_only=functional_only).run()
    new = Interpreter(new_prog, functional_only=functional_only).run()

    bf = {_key(f): f for f in winnow.sift(base.chronicle)}
    nf = {_key(f): f for f in winnow.sift(new.chronicle)}

    gained = [nf[k] for k in nf if k not in bf]
    lost = [bf[k] for k in bf if k not in nf]
    shifted = [(k[0], bf[k].score, nf[k].score) for k in nf
               if k in bf and abs(nf[k].score - bf[k].score) > 0.05]
    return Diff(change, gained, lost, shifted, base, new)
