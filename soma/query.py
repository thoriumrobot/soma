"""
soma.query -- the general Winnow-S query language (spec section 8).

Complements the curated patterns in winnow.py with author-written queries:

    query "the body knew first" {
      feel ?c ?q ?t1
      act  ?c ?a ?t2
      where ?t2 >= ?t1
      where ?t2 - ?t1 < 2s
      surface "{?c} felt {?q}, then did {?a} -- before knowing why"
    }

A query is a conjunction of relational predicates over Chronicle events, plus
`where` filters, plus a `surface` template. It is a tiny relational join engine:
each predicate binds its variables against matching events; predicates sharing a
variable are joined; `where` filters prune; `surface` renders the survivors as
prose. This is Kreminski's Winnow, specialised to SOMA's interoceptive trace.
"""

from __future__ import annotations
from dataclasses import dataclass
from . import ast_nodes as A


@dataclass
class QueryResult:
    name: str
    t: float
    text: str
    bindings: dict


def _quale(e):
    q = e.detail.get("quale", "")
    return q[7:-1] if q.startswith("Qualia<") else q


# relation name -> (event kinds, field extractors positional)
RELATIONS = {
    "feel":    (("emit",),    [lambda e: e.who, _quale, lambda e: e.t]),
    "somatic": (("somatic",), [lambda e: e.who, _quale, lambda e: e.t]),
    "act":     (("move",),    [lambda e: e.who, lambda e: e.detail.get("action"), lambda e: e.t]),
    "drive":   (("drive",),   [lambda e: e.who, lambda e: e.detail.get("channel"), lambda e: e.t]),
    "spend":   (("spend",),   [lambda e: e.who, lambda e: e.detail.get("resource"), lambda e: e.t]),
    "narrate": (("narrate",), [lambda e: e.who, lambda e: e.detail.get("quote"),
                               lambda e: e.detail.get("gap", 0.0), lambda e: e.t]),
    "crash":   (("crash",),   [lambda e: e.who, lambda e: e.t]),
    "repair":  (("repair",),  [lambda e: e.who, lambda e: e.t]),
    "conflict":(("conflict",),[lambda e: e.who, lambda e: e.detail.get("pair"), lambda e: e.t]),
    "ignite":  (("ignite",),  [lambda e: e.who, lambda e: e.t]),
    "ignore":  (("ignore",),  [lambda e: e.who, lambda e: e.t]),
    "own":     (("ownership",),[lambda e: e.who, lambda e: e.detail.get("state"), lambda e: e.t]),
    "spike":   (("emit", "drive", "spend"), [lambda e: e.who, lambda e: e.t]),
}


def _match_pred(pred: A.QueryPred, events, binding):
    rel = RELATIONS.get(pred.rel)
    if rel is None:
        return []
    kinds, extractors = rel
    out = []
    for e in events:
        if e.kind not in kinds:
            continue
        vals = [ext(e) for ext in extractors]
        if len(pred.terms) > len(vals):
            continue
        b = dict(binding)
        ok = True
        for (kind, tv), val in zip(pred.terms, vals):
            if kind == "var":
                if tv in b and b[tv] != val:
                    ok = False; break
                b[tv] = val
            elif kind == "num":
                if float(val) != float(tv):
                    ok = False; break
            else:  # lit
                if str(val) != str(tv):
                    ok = False; break
        if ok:
            out.append(b)
    return out


def _eval(expr, b):
    if isinstance(expr, A.Num):
        return expr.value
    if isinstance(expr, A.Str):
        return expr.value
    if isinstance(expr, A.Ref):
        return b.get(expr.name, expr.name)
    if isinstance(expr, A.Bin):
        l, r = _eval(expr.left, b), _eval(expr.right, b)
        try:
            l = float(l); r = float(r)
        except (TypeError, ValueError):
            l, r = str(l), str(r)
        return {"+": lambda: l + r, "-": lambda: l - r, "*": lambda: l * r,
                "/": lambda: l / r if r else 0.0,
                "<": lambda: l < r, ">": lambda: l > r, "<=": lambda: l <= r,
                ">=": lambda: l >= r, "==": lambda: l == r, "!=": lambda: l != r}[expr.op]()
    return None


def _fmt_t(t):
    if not isinstance(t, (int, float)):
        return str(t)
    if t < 90:
        return f"{t:.1f}s"
    if t < 172800:
        return f"{t/3600:.1f}h"
    if t < 3.15e7:
        return f"{t/86400:.1f}d"
    return f"{t/3.15e7:.1f}y"


def _surface(template, b):
    out = template
    for k, v in b.items():
        token = "{" + k + "}"
        if token in out:
            val = _fmt_t(v) if k.startswith("?t") and isinstance(v, (int, float)) else v
            out = out.replace(token, str(val))
    return out


def run_query(q: A.Query, chronicle) -> list[QueryResult]:
    events = list(chronicle)
    bindings = [{}]
    for pred in q.preds:
        nxt = []
        for b in bindings:
            nxt.extend(_match_pred(pred, events, b))
        bindings = nxt
        if not bindings:
            break
    # apply where filters
    for w in q.wheres:
        bindings = [b for b in bindings if _eval(w, b)]
    # dedupe by surfaced text
    seen, results = set(), []
    for b in bindings:
        text = _surface(q.surface, b)
        if text in seen:
            continue
        seen.add(text)
        ts = [v for k, v in b.items() if k.startswith("?t") and isinstance(v, (int, float))]
        results.append(QueryResult(q.name, min(ts) if ts else 0.0, text, b))
    results.sort(key=lambda r: r.t)
    return results


def run_all(prog, chronicle) -> dict:
    return {q.name: run_query(q, chronicle) for q in prog.queries}
