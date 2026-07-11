"""
web_bridge -- the single entry point the browser calls through Pyodide.

Each `run_command(...)` invocation mirrors exactly what `python -m soma <cmd>`
does on the command line, so the HTML playground produces byte-for-byte the same
output as the real toolchain. Output is returned as ANSI-colored text; the JS
side converts the ANSI escapes into HTML spans.
"""
from soma.parser import parse
from soma.interpreter import Interpreter
from soma.checker import SomaTypeError, ConsentError
from soma import winnow, viz, query as qmod
from soma import prose as prose_mod, perturb as perturb_mod


def _run(src, title, functional_only=False):
    prog = parse(src, title=title)
    return Interpreter(prog, functional_only=functional_only).run()


def _msg(text, color, width):
    """Wrap a plain (non-box) message -- an error, a note -- to the render width
    so it never overflows on a narrow screen, then color it."""
    from soma.viz import wrap_body, col
    lines = wrap_body(text, width + 2, indent="")   # +2: no box gutter here
    return "\n".join(col(ln, color) for ln in lines)


def run_command(command, src, title="untitled", **opts):
    """Dispatch one toolchain command and return its rendered text.

    command : one of run|check|sift|prose|trace|perturb|query
    src     : the SOMA source text
    opts    : command-specific options (rows, pattern, kinds, gender, set_expr,
              functional_only)
    Colored (ANSI) output is always produced; the browser converts it.
    """
    viz.configure(color=True, unicode=True, width=int(opts.get("width", 92)))
    functional_only = bool(opts.get("functional_only", False))
    rows = int(opts.get("rows", 30))

    try:
        if command == "check":
            from soma.checker import check as _check
            prog = parse(src, title=title)
            _check(prog, functional_only=functional_only)
            n_loops = len(prog.loops)
            n_bodies = len(prog.bodies)
            return _msg(
                f"\u2713 {title}: parses and checks clean "
                f"({n_loops} loops, {n_bodies} bodies).", "green", int(opts.get("width", 92)))

        if command == "perturb":
            set_expr = opts.get("set_expr", "").strip()
            if not set_expr:
                return viz.col("perturb needs a --set expression, e.g. "
                               "loop.precision=0.5", "red")
            try:
                d = perturb_mod.perturb(src, set_expr, title=title,
                                        functional_only=functional_only)
            except perturb_mod.PerturbError as e:
                return _msg(f"\u2717 PerturbError: {e}", "red", int(opts.get("width", 92)))
            return viz.render_diff(d)

        # everything else needs a run
        result = _run(src, title, functional_only)

        if command == "run":
            findings = winnow.sift(result.chronicle, opts.get("pattern") or None)
            qresults = qmod.run_all(result.program, result.chronicle)
            return viz.render_report(result, findings=findings, trace_rows=rows,
                                     qresults=qresults)

        if command == "sift":
            findings = winnow.sift(result.chronicle, opts.get("pattern") or None)
            return viz.render_sift(findings, limit=rows)

        if command == "trace":
            kinds = opts.get("kinds")
            kinds = kinds.split(",") if kinds else None
            # The trace is tabular: columns must stay aligned, so it is the one
            # view we do NOT reflow to a narrow width. We render it wide and let
            # the browser scroll it horizontally, rather than truncating detail.
            viz.configure(color=True, unicode=True, width=110)
            return viz.render_trace(result, max_rows=rows, kinds=kinds)

        if command == "prose":
            genders = {}
            g = opts.get("gender", "")
            if g:
                for pair in g.split(","):
                    if ":" in pair:
                        who, gg = pair.split(":")
                        genders[who.strip()] = gg.strip()
            return prose_mod.render(result, genders=genders,
                                    width=int(opts.get("width", 92)) - 4)

        if command == "query":
            qresults = qmod.run_all(result.program, result.chronicle)
            if not qresults:
                return _msg("this program declares no query { } blocks.", "grey", int(opts.get("width", 92)))
            return viz.render_queries(qresults, limit=rows)

        return _msg(f"unknown command: {command}", "red", int(opts.get("width", 92)))

    except (SomaTypeError, ConsentError) as e:
        return _msg(f"\u2717 {type(e).__name__}: {e}", "red", int(opts.get("width", 92)))
    except Exception as e:  # parse errors, etc.
        return _msg(f"\u2717 {type(e).__name__}: {e}", "red", int(opts.get("width", 92)))
