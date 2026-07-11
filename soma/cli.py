"""
somac -- the SOMA command-line toolchain.

    python -m soma run   FILE [--functional-only] [--sift PATTERN] [--no-color]
    python -m soma check FILE [--functional-only]
    python -m soma trace FILE [--kinds settle,emit,...]
    python -m soma sift  FILE [PATTERN]
    python -m soma ast   FILE
"""

from __future__ import annotations
import argparse, sys, os

from .parser import parse
from .interpreter import Interpreter
from .checker import SomaTypeError, ConsentError
from . import winnow, viz, query as qmod
from . import observables, prose as prose_mod, perturb as perturb_mod


def _read(path):
    with open(path, "r") as f:
        return f.read(), os.path.splitext(os.path.basename(path))[0]


def _compile_and_run(path, functional_only):
    src, title = _read(path)
    prog = parse(src, title=title)
    return Interpreter(prog, functional_only=functional_only).run()


def cmd_run(args):
    viz.configure(color=not args.no_color, unicode=not args.ascii)
    try:
        result = _compile_and_run(args.file, args.functional_only)
    except (SomaTypeError, ConsentError) as e:
        print(viz.col(f"✗ {type(e).__name__}: {e}", "red"))
        return 1
    findings = winnow.sift(result.chronicle, args.sift)
    qresults = qmod.run_all(result.program, result.chronicle)
    phi = None
    if getattr(args, "phi", False):
        phi = observables.integrated_information(result.interp)
    print(viz.render_report(result, findings=findings, trace_rows=args.rows,
                            phi=phi, qresults=qresults))
    return 0


def cmd_phi(args):
    viz.configure(color=not args.no_color, unicode=not args.ascii)
    result = _compile_and_run(args.file, args.functional_only)
    nodes = args.nodes.split(",") if args.nodes else None
    phi = observables.integrated_information(result.interp, nodes)
    print(viz.render_phi(phi))
    return 0


def cmd_query(args):
    viz.configure(color=not args.no_color, unicode=not args.ascii)
    result = _compile_and_run(args.file, args.functional_only)
    qresults = qmod.run_all(result.program, result.chronicle)
    if not qresults:
        print(viz.col("this program declares no query { } blocks.", "grey"))
        return 0
    print(viz.render_queries(qresults, limit=args.rows))
    return 0


def cmd_plot(args):
    viz.configure(color=not args.no_color, unicode=not args.ascii)
    result = _compile_and_run(args.file, args.functional_only)
    names = args.vars.split(",") if args.vars else list(result.channel_hist)[:3]
    series = {}
    for n in names:
        n = n.strip()
        if n in result.channel_hist:
            series[n] = (result.times, result.channel_hist[n])
        elif n in result.mood_hist:
            series[n] = (result.times, result.mood_hist[n])
        elif n in (result.attn_hist or {}):
            series[n] = (result.times, result.attn_hist[n])
    if not series:
        print(viz.col(f"no such channels: {names}", "red"))
        return 1
    print("\n".join(viz.plot_series(series, width=viz.term_width(),
                                    title=f"{result.program.title}: "
                                          + ", ".join(series))))
    return 0


def cmd_check(args):
    src, title = _read(args.file)
    try:
        prog = parse(src, title=title)
        from .checker import check
        check(prog, functional_only=args.functional_only)
    except (SomaTypeError, ConsentError) as e:
        print(viz.col(f"✗ {type(e).__name__}: {e}", "red"))
        return 1
    except Exception as e:
        print(viz.col(f"✗ ParseError: {e}", "red"))
        return 1
    print(viz.col(f"✓ {title}: parses and checks clean "
                  f"({len(prog.loops)} loops, {len(prog.bodies)} bodies).", "green"))
    return 0


def cmd_trace(args):
    viz.configure(color=not args.no_color, unicode=not args.ascii)
    result = _compile_and_run(args.file, args.functional_only)
    kinds = args.kinds.split(",") if args.kinds else None
    print(viz.render_trace(result, max_rows=args.rows, kinds=kinds))
    return 0


def cmd_sift(args):
    viz.configure(color=not args.no_color, unicode=not args.ascii)
    result = _compile_and_run(args.file, args.functional_only)
    findings = winnow.sift(result.chronicle, args.pattern)
    print(viz.render_sift(findings, limit=args.rows))
    return 0


def cmd_prose(args):
    viz.configure(color=not args.no_color, unicode=not args.ascii)
    result = _compile_and_run(args.file, args.functional_only)
    genders = {}
    if args.gender:
        for pair in args.gender.split(","):
            who, g = pair.split(":")
            genders[who.strip()] = g.strip()
    print(prose_mod.render(result, genders=genders))
    return 0


def cmd_perturb(args):
    viz.configure(color=not args.no_color, unicode=not args.ascii)
    src, title = _read(args.file)
    try:
        d = perturb_mod.perturb(src, args.set, title=title,
                                functional_only=args.functional_only)
    except perturb_mod.PerturbError as e:
        print(viz.col(f"✗ PerturbError: {e}", "red"))
        return 1
    print(viz.render_diff(d))
    return 0


def cmd_ast(args):
    src, title = _read(args.file)
    prog = parse(src, title=title)
    import pprint
    print(f"consent={prog.consent}")
    print(f"sim: duration={prog.sim.duration} dt={prog.sim.dt}")
    for section in ("lets", "bodies", "resources", "stimuli", "flows", "loops",
                    "moods", "narrators", "handlers", "embodiments", "memories",
                    "attentions", "workspaces", "awarenesses", "allostats",
                    "interventions", "ownerships", "queries", "couples",
                    "scenes", "characters"):
        items = getattr(prog, section)
        if items:
            print(viz.col(f"\n{section}:", "bold"))
            for it in items:
                print("  ", it)
    return 0


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    p = argparse.ArgumentParser(prog="somac", description="the SOMA toolchain")
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("file")
        sp.add_argument("--functional-only", action="store_true",
                        help="stub out feel(); log only access-states (ethics mode)")
        sp.add_argument("--no-color", action="store_true")
        sp.add_argument("--ascii", action="store_true", help="ASCII glyphs only")
        sp.add_argument("--rows", type=int, default=30)

    r = sub.add_parser("run", help="compile, simulate, and render a full report")
    common(r); r.add_argument("--sift", default=None, help="only this sift pattern")
    r.add_argument("--phi", action="store_true",
                   help="also compute approximate integrated information")
    r.set_defaults(func=cmd_run)

    ph = sub.add_parser("phi", help="integrated information (phi_approx) only")
    common(ph); ph.add_argument("--nodes", default=None,
                                help="comma-separated channels to use as nodes")
    ph.set_defaults(func=cmd_phi)

    q = sub.add_parser("query", help="run the program's own Winnow-S query blocks")
    common(q); q.set_defaults(func=cmd_query)

    pl = sub.add_parser("plot", help="braille line plot of channels over time")
    common(pl); pl.add_argument("--vars", default=None,
                                help="comma-separated channel/mood names")
    pl.set_defaults(func=cmd_plot)

    c = sub.add_parser("check", help="parse + static checks only")
    common(c); c.set_defaults(func=cmd_check)

    t = sub.add_parser("trace", help="print the raw Chronicle trace")
    common(t); t.add_argument("--kinds", default=None,
                              help="comma-separated event kinds to include")
    t.set_defaults(func=cmd_trace)

    s = sub.add_parser("sift", help="run Winnow-S story sifting")
    common(s); s.add_argument("pattern", nargs="?", default=None)
    s.set_defaults(func=cmd_sift)

    pr = sub.add_parser("prose", help="render the run as free indirect discourse")
    common(pr); pr.add_argument("--gender", default=None,
                                help="Alice:she,Bob:he — pronouns for the prose")
    pr.set_defaults(func=cmd_prose)

    pb = sub.add_parser("perturb", help="change one dial, re-run, diff the story")
    common(pb); pb.add_argument("--set", required=True, action="append",
                                help="name.field=value (repeatable), e.g. "
                                     "--set courtship.conviction=0.9 --set courtship.learn=0")
    pb.set_defaults(func=cmd_perturb)

    a = sub.add_parser("ast", help="dump the parsed program")
    a.add_argument("file"); a.set_defaults(func=cmd_ast)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
