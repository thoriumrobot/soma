"""
somaviz: a text-based visualization library for SOMA simulations.

Everything renders in a terminal. The goal is legibility for a *novelist*: not
dashboards, but the interior of a character laid out so cause and feeling are
visible at a glance. Provides:

  * sparklines and bars (unicode, with ASCII fallback)
  * channel plots (interoceptive / exteroceptive / proprioceptive)
  * a moment-by-moment trace table
  * the signature two-column view: the narrator's story vs. the Chronicle's
    ground truth, with the confabulation gap between them
  * mood-over-time, resource ('body budget') depletion
  * a rendered sift report
"""

from __future__ import annotations
import shutil

# ------- palette / glyphs -------
BLOCKS = "▁▂▃▄▅▆▇█"
BAR = "█"
ASCII_BLOCKS = ".:-=+*#@"

_USE_COLOR = True
_USE_UNICODE = True
_FORCE_WIDTH = None      # when set, overrides terminal detection (used by the browser)

C = {
    "reset": "\033[0m", "dim": "\033[2m", "bold": "\033[1m",
    "red": "\033[31m", "green": "\033[32m", "yellow": "\033[33m",
    "blue": "\033[34m", "magenta": "\033[35m", "cyan": "\033[36m",
    "grey": "\033[90m",
}


def configure(color=True, unicode=True, width=None):
    global _USE_COLOR, _USE_UNICODE, _FORCE_WIDTH
    _USE_COLOR = color
    _USE_UNICODE = unicode
    _FORCE_WIDTH = width


import re as _re
_ANSI_RE = _re.compile(r"\x1b\[[0-9;]*m")


def _visible(s):
    """Length of a string ignoring ANSI color codes."""
    return len(_ANSI_RE.sub("", s))


def wrap_body(text, width, indent="     ", first=None):
    """Fold a long plain-text line to fit inside a box of the given width.

    Returns a list of lines, each already prefixed with `indent` (or `first`
    for the first line). Used for the long descriptive sentences in Winnow-S
    findings, queries, and the two-column view, so they never overflow the box
    on a narrow (mobile) screen. Word-wrap; never breaks a word unless it is
    itself wider than the available room.
    """
    first = indent if first is None else first
    # Match box()'s content budget exactly: it truncates anything wider than
    # (width - 3) visible chars. Subtracting the indent leaves the room for text.
    avail = max(8, width - 3 - len(indent))
    words = str(text).split()
    lines, cur = [], ""
    for w in words:
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= avail:
            cur += " " + w
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    if not lines:
        lines = [""]
    out = []
    for i, ln in enumerate(lines):
        out.append((first if i == 0 else indent) + ln)
    return out


def col(s, c):
    if not _USE_COLOR:
        return s
    return f"{C.get(c,'')}{s}{C['reset']}"


def _blocks():
    return BLOCKS if _USE_UNICODE else ASCII_BLOCKS


def term_width(default=88):
    if _FORCE_WIDTH is not None:
        return _FORCE_WIDTH
    try:
        return min(shutil.get_terminal_size().columns, 100)
    except Exception:
        return default


# ------- braille canvas (adapted from ilion/viz.py) -------
_DOTS = ((0x01, 0x02, 0x04, 0x40), (0x08, 0x10, 0x20, 0x80))
_SERIES_COLORS = ["cyan", "yellow", "magenta", "green", "red", "blue"]


class Canvas:
    """Braille pixel canvas: w x h character cells => 2w x 4h pixels."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.grid = [[0] * w for _ in range(h)]
        self.colr = [[None] * w for _ in range(h)]

    def set(self, px, py, color=None):
        if not (0 <= px < self.w * 2 and 0 <= py < self.h * 4):
            return
        cx, cy = px // 2, py // 4
        self.grid[cy][cx] |= _DOTS[px % 2][py % 4]
        if color:
            self.colr[cy][cx] = color

    def line(self, x0, y0, x1, y1, color=None):
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy; x0 += sx
            if e2 <= dx:
                err += dx; y0 += sy

    def rows(self):
        out = []
        for y in range(self.h):
            row = []
            for x in range(self.w):
                ch = chr(0x2800 + self.grid[y][x])
                c = self.colr[y][x]
                row.append(col(ch, c) if c else ch)
            out.append("".join(row))
        return out


def plot_series(series, width=70, height=10, title=None, legend=True):
    """series: {name: (xs, ys)} or {name: ys}. Falls back to sparklines in
    ASCII mode, where braille glyphs would not render."""
    import math as _m
    norm = {}
    for k, v in series.items():
        if isinstance(v, tuple):
            norm[k] = (list(v[0]), list(v[1]))
        else:
            norm[k] = (list(range(len(v))), list(v))
    if not norm:
        return ["(no data)"]
    if not _USE_UNICODE:
        return [f"  {n:<12} {sparkline(ys, 50)}" for n, (_x, ys) in norm.items()]

    allx = [x for xs, _ in norm.values() for x in xs]
    ally = [y for _, ys in norm.values() for y in ys if y is not None and _m.isfinite(y)]
    if not allx or not ally:
        return ["(no data)"]
    x0, x1 = min(allx), max(allx)
    y0, y1 = min(ally), max(ally)
    if x1 - x0 < 1e-15: x1 = x0 + 1
    if y1 - y0 < 1e-15: y1 = y0 + 1
    pad = 0.05 * (y1 - y0)
    y0 -= pad; y1 += pad

    gutter = 11
    cw = max(10, width - gutter - 1)
    cv = Canvas(cw, height)

    def px(x): return int((x - x0) / (x1 - x0) * (cw * 2 - 1))
    def py(y): return int((y1 - y) / (y1 - y0) * (height * 4 - 1))

    for i, (name, (xs, ys)) in enumerate(norm.items()):
        c = _SERIES_COLORS[i % len(_SERIES_COLORS)]
        prev = None
        for x, y in zip(xs, ys):
            if y is None or not _m.isfinite(y):
                prev = None; continue
            p = (px(x), py(y))
            if prev:
                cv.line(prev[0], prev[1], p[0], p[1], c)
            else:
                cv.set(p[0], p[1], c)
            prev = p

    rows = cv.rows()
    out = []
    if title:
        out.append(col(title, "bold"))
    for r in range(height):
        yv = y1 - (r + 0.5) * (y1 - y0) / height
        lab = f"{yv:>9.3g} " if r % 2 == 0 else " " * 10
        out.append(col(lab, "grey") + "│" + rows[r])
    out.append(" " * 10 + "└" + "─" * cw)
    if legend and len(norm) > 1:
        items = [col("──", _SERIES_COLORS[i % len(_SERIES_COLORS)]) + " " + n
                 for i, n in enumerate(norm)]
        out.append(" " * 11 + "  ".join(items))
    return out


# ------- primitives -------
def sparkline(values, width=None):
    if not values:
        return ""
    import math as _m
    blocks = _blocks()
    vals = [v if _m.isfinite(v) else 0.0 for v in values]
    if width and len(vals) > width:
        # simple decimation
        step = len(vals) / width
        vals = [vals[int(i * step)] for i in range(width)]
    lo, hi = min(vals), max(vals)
    if hi - lo < 1e-9:
        idx = len(blocks) // 2
        return blocks[idx] * len(vals)
    out = []
    for v in vals:
        frac = (v - lo) / (hi - lo)
        out.append(blocks[min(len(blocks) - 1, int(frac * (len(blocks) - 1) + 0.5))])
    return "".join(out)


def bar(frac, width=20):
    frac = max(0.0, min(1.0, frac))
    n = int(round(frac * width))
    fill = BAR if _USE_UNICODE else "#"
    empty = "·" if _USE_UNICODE else "."
    return fill * n + empty * (width - n)


def rule(width=None, ch="─"):
    width = width or term_width()
    return (ch if _USE_UNICODE else "-") * width


def header(title, width=None):
    width = width or term_width()
    t = f" {_t(title)} "
    side = (width - len(t))
    left = side // 2
    right = side - left
    line = ("─" if _USE_UNICODE else "-")
    return col(line * left + t + line * right, "bold")


def _t(title):
    """Panel titles use a middot separator in unicode mode, a dash in ASCII."""
    return title if _USE_UNICODE else title.replace("·", "-")


def box(title, lines, width=None):
    width = width or term_width()
    title = _t(title)
    tl, tr, bl, br, h, v = ("╭", "╮", "╰", "╯", "─", "│") if _USE_UNICODE else ("+", "+", "+", "+", "-", "|")
    # title rule, clamped so a long title never blows the width on a phone
    inner = width - 5 - len(title)
    if inner < 0:
        title = title[:max(0, width - 6)]
        inner = width - 5 - len(title)
    out = [col(tl + h + f" {title} " + h * max(0, inner) + tr, "cyan")]
    for ln in lines:
        # Backstop: hard-truncate any content line that would overflow the box,
        # measuring on *visible* width (ignoring color codes) and preserving any
        # trailing reset. Individual renderers try to fit; this guarantees it, so
        # the output is always clean on a narrow (mobile) screen.
        budget = width - 3          # "│ " prefix + one cell of right margin
        if _visible(ln) > budget:
            ln = _truncate_visible(ln, budget)
        out.append(col(v, "cyan") + " " + ln)
    out.append(col(bl + h * (width - 2) + br, "cyan"))
    return "\n".join(out)


def _truncate_visible(s, budget):
    """Cut a possibly-colored string to `budget` visible chars, add an ellipsis,
    and close any open color span so nothing bleeds past the box."""
    ell = "…" if _USE_UNICODE else "..."
    out, vis, i = [], 0, 0
    had_color = False
    while i < len(s) and vis < budget - 1:
        m = _ANSI_RE.match(s, i)
        if m:
            out.append(m.group(0)); had_color = True; i = m.end()
            continue
        out.append(s[i]); vis += 1; i += 1
    res = "".join(out) + ell
    if had_color:
        res += C["reset"]
    return res


# ------- composite views -------
def fmt_t(t):
    if t < 90:
        return f"{t:5.1f}s"
    if t < 5400:
        return f"{t/60:5.1f}m"
    if t < 172800:
        return f"{t/3600:5.1f}h"
    if t < 3.1e7:
        return f"{t/86400:5.1f}d"
    return f"{t/3.15e7:5.1f}y"


def render_channels(result):
    lines = []
    mod_color = {"intero": "red", "extero": "cyan", "proprio": "yellow",
                 "schema": "green", "image": "magenta"}
    prog = result.program
    modality = {}
    for b in prog.bodies:
        for ch in b.channels:
            modality[ch.name] = ch.modality
    for e in prog.embodiments:
        for (pname, _s, _i, _t) in e.pairs:
            modality[f"{pname}_schema"] = "schema"
            modality[f"{pname}_image"] = "image"
    for fl in prog.flows:
        modality.setdefault(fl.channel, "intero")
    w = term_width()
    arrow = "→" if _USE_UNICODE else "->"
    for name, hist in result.channel_hist.items():
        if not hist:
            continue
        m = modality.get(name, "extero")
        tag = col(f"{m[:6]:>6}", mod_color.get(m, "cyan"))
        summary = f"{hist[0]:g}{arrow}{hist[-1]:g}"
        nm = name[:18]
        namew = max(12, len(nm))
        used = 2 + 6 + 1 + namew + 1 + 2 + len(summary)
        spark_w = max(8, min(60, (w - 3) - used))
        spark = sparkline(hist, width=spark_w)
        lines.append(f"  {tag} {nm:<12} {spark}  {col(summary,'grey')}")
    return box("BODY · channels over time", lines)


def render_resources(result):
    if not result.resource_hist:
        return ""
    w = term_width()
    lines = []
    bw = max(8, min(24, w - 60))
    for name, hist in result.resource_hist.items():
        cap = hist[0] if hist else 1
        frac = (hist[-1] / cap) if cap else 0
        nm = name[:18]
        label = f"{hist[-1]:.0f}/{cap:.0f}"
        used = 2 + max(12, len(nm)) + 1 + bw + 1 + len(label) + 2
        sw = max(8, min(40, (w - 3) - used))
        lines.append(f"  {nm:<12} {bar(frac, bw)} {col(label,'grey')}  "
                     f"{sparkline(hist, sw)}")
    return box("BODY BUDGET · affine resources (cannot be conjured)", lines)


def render_moods(result):
    if not result.mood_hist:
        return ""
    w = term_width()
    lines = []
    for name, hist in result.mood_hist.items():
        # normalize around 0 for a signed sparkline
        nm = name[:18]
        summary = f"now {hist[-1]:+.2f}"
        used = 2 + max(12, len(nm)) + 1 + 2 + len(summary)
        sw = max(8, min(50, (w - 3) - used))
        lines.append(f"  {nm:<12} {sparkline(hist,sw)}  "
                     f"{col(summary,'grey')}")
    return box("MOOD · the slow variable (integrates affect, decays)", lines)


def render_trace(result, max_rows=40, kinds=None):
    rows = []
    for e in result.chronicle:
        if kinds and e.kind not in kinds:
            continue
        rows.append(e)
    rows = rows[:max_rows]
    lines = []
    kind_color = {
        "settle": "grey", "emit": "magenta", "move": "yellow", "drive": "blue",
        "spend": "yellow", "budget": "red", "mood": "green", "narrate": "cyan",
        "crash": "red", "repair": "green", "stimulus": "bold", "ignore": "grey",
        "conflict": "red",
    }
    for e in rows:
        detail = " ".join(f"{k}={v}" for k, v in e.detail.items())
        kc = kind_color.get(e.kind, "reset")
        lines.append(f"  {col(fmt_t(e.t),'grey')} {col(f'{e.kind:<8}',kc)} "
                     f"{col(e.who[:12].ljust(12),'dim')} {detail}")
    return box(f"CHRONICLE · trace ({len(rows)} of {len(result.chronicle)} events)", lines)


def _wrap(s, w):
    words, lines, cur = s.split(), [], ""
    for wd in words:
        if len(cur) + len(wd) + 1 > w:
            lines.append(cur); cur = wd
        else:
            cur = (cur + " " + wd).strip()
    if cur:
        lines.append(cur)
    return lines or [""]


def render_two_column(result, width=None):
    """The signature view: what the character SAYS vs. what actually HAPPENED.

    Alignment is computed on *plain* text; color is applied only to whole
    columns afterward, so a fixed divider stays put. Consecutive identical
    narrator lines are collapsed with a (xN) count -- a stuck story reads as
    stuck, not as noise.
    """
    width = width or term_width()
    D = width // 2               # divider column
    # Lw/Rw are the wrap widths for the two columns. The full row is
    # "  " + Lw + " " + divider + " " + Rw, and box() truncates anything past
    # (width-3) visible chars, so the right column must leave room for the
    # 2-char box gutter -- hence Rw is 2 narrower than the naive half.
    Lw, Rw = D - 3, width - D - 5

    narrates = [e for e in result.chronicle if e.kind == "narrate"]
    truth = [e for e in result.chronicle
             if e.kind in ("emit", "drive", "spend", "move", "crash", "repair",
                           "budget", "somatic", "conflict", "ownership",
                           "ignite", "rebus", "starved")]

    # group narrator quotes globally by text (first-seen order)
    ngroups = {}
    for e in narrates:
        q = e.detail.get("quote", "")
        if q in ngroups:
            ngroups[q][2] += 1
        else:
            ngroups[q] = [q, e, 1]
    coll = list(ngroups.values())
    # group truth events globally by description (first-seen order)
    tgroups = {}
    for e in truth:
        d = _truth_desc(e)
        if d in tgroups:
            tgroups[d][2] += 1
        else:
            tgroups[d] = [d, e, 1]
    tcoll = list(tgroups.values())
    events = sorted(
        [("N", q, e, n) for (q, e, n) in coll] +
        [("T", d, e, n) for (d, e, n) in tcoll],
        key=lambda x: x[2].t)

    divider = "│" if _USE_UNICODE else "|"

    def emit_row(left, right):
        rows_l = _wrap(left, Lw) if left else [""]
        rows_r = _wrap(right, Rw) if right else [""]
        for i in range(max(len(rows_l), len(rows_r))):
            l = rows_l[i] if i < len(rows_l) else ""
            r = rows_r[i] if i < len(rows_r) else ""
            line = "  " + l.ljust(Lw) + " " + col(divider, "grey") + " "
            out.append(line + col(r, "grey" if r.startswith(" ") else "reset"))

    out = ["  " + col("THE STORY SHE TELLS".ljust(Lw), "bold") + "   " +
           col("THE BODY'S RECORD", "bold"),
           "  " + col(rule(width - 5, "─"), "grey")]
    for tag, q, e, n in events:
        if tag == "N":
            gap = e.detail.get("gap", 0)
            times = f"({n}x) " if n > 1 else ""
            q1, q2 = ("«", "»") if _USE_UNICODE else ("<<", ">>")
            mark = (f"  {q1}confabulates{q2}" if gap >= 0.9
                    else (f"  {q1}downplays{q2}" if gap >= 0.5 else ""))
            left = f"{fmt_t(e.t).strip()}  {times}\"{q}\"  [gap {gap}]{mark}"
            emit_row(left, "")
        else:
            times = f"({n}x) " if n > 1 else ""
            right = f"{fmt_t(e.t).strip()}  {times}{q}"
            emit_row("", right)
    return box("NARRATOR vs GROUND TRUTH", out)


def _truth_desc(e):
    d = e.detail
    if e.kind == "emit":
        return f"feels {d.get('quale','?')}"
    if e.kind == "somatic":
        return f"somatic memory fires {d.get('quale','?')} (no story attached)"
    if e.kind == "conflict":
        return f"schema/image conflict: {d.get('pair')}"
    if e.kind == "ownership":
        return f"{e.who} becomes {d.get('state')}"
    if e.kind == "ignite":
        return f"IGNITES: {d.get('content')} reaches consciousness"
    if e.kind == "rebus":
        return "priors relaxed (REBUS)"
    if e.kind == "starved":
        return "no attention left to deliberate"
    if e.kind == "drive":
        arrow = "→" if _USE_UNICODE else "->"
        return f"{d.get('channel')} {arrow} {d.get('to')}"
    if e.kind == "spend":
        return f"spends {d.get('spent')} {d.get('resource')} (left {d.get('left')})"
    if e.kind == "budget":
        return d.get("note", "budget exceeded")
    if e.kind == "move":
        return f"acts: {d.get('action')}"
    if e.kind == "crash":
        return "DISSOCIATES (interoception detaches)"
    if e.kind == "repair":
        return "reattaches, slowly"
    return e.kind


def render_sift(findings, limit=12):
    w = term_width()
    lines = []
    if not findings:
        lines = [col("  (no storyful patterns surfaced)", "grey")]
    for fnd in findings[:limit]:
        score_bar = bar(fnd.score, 10)
        lines.append(f"  {col(score_bar,'yellow')} {col(fnd.pattern,'bold')}")
        lines.extend(wrap_body(fnd.text, w, indent="     "))
    return box("WINNOW-S · storyful moments, ranked", lines)


def render_attention(result):
    """The affine spotlight, and awareness as its transparent model."""
    if not result.attn_hist and not result.aware_hist:
        return ""
    w = term_width()
    budget = w - 3
    lines = []
    for name, hist in (result.attn_hist or {}).items():
        if not hist:
            continue
        cap = max(hist) or 1
        label = f"{hist[-1]:.1f}/{cap:.1f}"
        nm = name[:14]
        fixed = 2 + 9 + 1 + max(10, len(nm)) + 1 + 1 + len(label) + 2  # +1 for bar/spark gap
        bw = max(6, min(20, (budget - fixed - 8)))
        sw = max(6, min(28, budget - fixed - bw))
        lines.append(f"  {col('spotlight','yellow')} {nm:<10} "
                     f"{bar(hist[-1]/cap, bw)} {col(label,'grey')}  "
                     f"{sparkline(hist, sw)}")
    for name, hist in (result.aware_hist or {}).items():
        if not hist:
            continue
        label = f"{hist[-1]:.2f}"
        nm = name[:14]
        fixed = 2 + 9 + 1 + max(10, len(nm)) + 1 + 1 + len(label) + 2
        bw = max(6, min(20, (budget - fixed - 8)))
        sw = max(6, min(28, budget - fixed - bw))
        lines.append(f"  {col('awareness','magenta')} {nm:<10} "
                     f"{bar(max(0.0,min(1.0,hist[-1])), bw)} "
                     f"{col(label,'grey')}  {sparkline(hist, sw)}")
    if not lines:
        return ""
    return box("ATTENTION · an affine spotlight, and the schema that models it", lines)


def render_ignition(result):
    """Global workspace: which contents crossed threshold and were broadcast."""
    if not result.ignition_hist:
        return ""
    ww = term_width()
    lines = []
    for name, hist in result.ignition_hist.items():
        if not hist:
            continue
        thr = next((w.threshold for w in result.program.workspaces if w.name == name), 0.5)
        nm = name[:18]
        summary = f"peak {max(hist):.2f}  threshold {thr}"
        namew = max(12, len(nm))
        sw = max(8, min(50, (ww - 3) - (2 + namew + 1 + 2 + len(summary))))
        lines.append(f"  {nm:<12} {sparkline(hist, sw)}  "
                     f"{col(summary,'grey')}")
    ig = [e for e in result.chronicle if e.kind == "ignite"]
    if ig:
        seen = {}
        for e in ig:
            seen.setdefault(e.detail.get("content"), []).append(e.t)
        for content, ts in seen.items():
            lines.append(f"    {col('ignited','green')} {content}  "
                         f"{col(f'x{len(ts)}, first at {fmt_t(ts[0]).strip()}','grey')}")
    else:
        lines.append(col("    nothing ignited: every content died locally", "grey"))
    if not lines:
        return ""
    return box("GLOBAL WORKSPACE · competition and ignition", lines)


def render_embodiment(result):
    """Schema/image conflicts: the seams of embodiment."""
    conf = [e for e in result.chronicle if e.kind == "conflict"]
    own = [e for e in result.chronicle if e.kind == "ownership"]
    if not conf and not own:
        return ""
    lines = []
    groups = {}
    for e in conf:
        groups.setdefault(e.detail.get("pair"), []).append(e)
    for pair, evs in groups.items():
        e = evs[0]
        lines.append(f"  {col('conflict','red')} {pair:<10} "
                     f"schema {e.detail.get('schema')} vs image {e.detail.get('image')}  "
                     f"{col(f'x{len(evs)} from {fmt_t(e.t).strip()}','grey')}")
        lines.append(f"     {col(e.detail.get('note',''), 'grey')}")
    for e in own:
        c = "green" if e.detail.get("state") == "owned" else "red"
        lines.append(f"  {col(e.detail.get('state','?'),c)} {e.who:<10} "
                     f"{col(fmt_t(e.t).strip(),'grey')}  {e.detail.get('note','')}")
    return box("EMBODIMENT · body schema vs body image, and ownership", lines)


def render_memory(result):
    som = [e for e in result.chronicle if e.kind == "somatic"]
    rec = [e for e in result.chronicle if e.kind == "recall"]
    if not som and not rec:
        return ""
    lines = []
    groups = {}
    for e in som:
        groups.setdefault(e.who, []).append(e)
    for name, evs in groups.items():
        dash = "—" if _USE_UNICODE else "--"
        lines.append(f"  {col('somatic','red')} {name:<12} fired x{len(evs)}, "
                     f"first at {col(fmt_t(evs[0].t).strip(),'grey')} "
                     f"{dash} {col('no episodic trace','grey')}")
    groups = {}
    for e in rec:
        groups.setdefault((e.who, e.detail.get("register")), []).append(e)
    for (name, reg), evs in groups.items():
        lines.append(f"  {col(reg or '?','cyan')} {name:<12} recalled x{len(evs)}")
    return box("MEMORY · four registers (the body can remember alone)", lines)


def render_phi(phi):
    """Integrated information, with the honesty the measure requires."""
    if not phi or not phi.get("ok"):
        reason = (phi or {}).get("reason", "not computed")
        return box("INTEGRATED INFORMATION", [col(f"  (skipped: {reason})", "grey")])
    lines = [
        f"  {'phi (bits)':<16} {bar(min(1.0, phi['phi_bits']), 24)} {phi['phi_bits']:.3f}",
        f"  {'EI (bits)':<16} {bar(min(1.0, phi['EI_bits']/2), 24)} {phi['EI_bits']:.3f}",
        f"  {'determinism':<16} {bar(phi['determinism'], 24)} {phi['determinism']:.3f}",
        f"  {'degeneracy':<16} {bar(phi['degeneracy'], 24)} {phi['degeneracy']:.3f}",
        "",
        col(f"  nodes: {', '.join(phi['nodes'])}", "grey"),
        col(f"  minimum-information partition: {phi['mip']}", "grey"),
        col("  phi_approx: binary coarse-graining, uniform interventions, bipartition", "grey"),
        col("  search. A property of this model, never evidence about sentience.", "grey"),
    ]
    return box("INTEGRATED INFORMATION · phi at the MIP (approximate)", lines)


def render_queries(qresults, limit=8):
    if not qresults:
        return ""
    w = term_width()
    lines = []
    for name, rows in qresults.items():
        lines.append(f"  {col(name, 'bold')} {col(f'({len(rows)} matches)', 'grey')}")
        if not rows:
            lines.append(col("     (no matches)", "grey"))
        for r in rows[:limit]:
            # don't print the timestamp twice if the author's template has one
            has_t = any(k.startswith("?t") and str(_fmt_inline(v)) in r.text
                        for k, v in r.bindings.items() if isinstance(v, (int, float)))
            stamp = "" if has_t else fmt_t(r.t).strip() + "  "
            wrapped = wrap_body(stamp + r.text, w, indent="     ")
            # colour the stamp grey on the first wrapped line
            if stamp and wrapped:
                wrapped[0] = "     " + col(stamp, "grey") + wrapped[0][5 + len(stamp):]
            lines.extend(wrapped)
        if len(rows) > limit:
            ell = "…" if _USE_UNICODE else "..."
            lines.append(col(f"     {ell} and {len(rows)-limit} more", "grey"))
    return box("WINNOW-S · author queries", lines)


def _fmt_inline(t):
    if t < 90:
        return f"{t:.1f}s"
    if t < 172800:
        return f"{t/3600:.1f}h"
    if t < 3.15e7:
        return f"{t/86400:.1f}d"
    return f"{t/3.15e7:.1f}y"


def render_social(result):
    """Who was reading whom, and how late."""
    cps = [e for e in result.chronicle if e.kind == "couple"]
    if not cps:
        return ""
    seen, lines = {}, []
    for e in cps:
        k = (e.who, e.detail.get("to"))
        seen.setdefault(k, []).append(e)
    arrow = "->" if not _USE_UNICODE else "→"
    w = term_width()
    # column widths for src/dst names, from the widest present, capped so the
    # whole row (indent + src + arrow + dst + lag-label) fits the box budget.
    def _lag_str(lag):
        return "0s" if lag <= 0 else fmt_t(lag).strip()
    labels = [f"lag {_lag_str(evs[0].detail.get('lag', 0))}, x{len(evs)}"
              for evs in seen.values()]
    tail = max((len(x) for x in labels), default=12)
    names = [s for (s, _d) in seen] + [d for (_s, d) in seen]
    longest = max((len(n) for n in names), default=8)
    colw = max(6, min(longest, (w - 3 - 2 - 4 - tail - 1) // 2))
    for (src, dst), evs in seen.items():
        lag = evs[0].detail.get("lag", 0)
        s = (src[:colw]).ljust(colw)
        d = (dst[:colw]).ljust(colw)
        lines.append(f"  {col(s,'cyan')} {arrow} {col(d,'magenta')} "
                     f"{col(f'lag {_lag_str(lag)}, x{len(evs)}','grey')}")
    return box("BETWEEN THEM · one body's surface as another's sensation", lines)


def render_scenes(result):
    marks = [e for e in result.chronicle if e.kind == "scene"]
    if not marks:
        return ""
    lines = [f"  {col(fmt_t(e.t).strip(),'grey'):<10} {col(e.who,'bold')}" for e in marks]
    return box("SCENES", lines)


def render_diff(d, limit=8):
    """The perturb view: what one dial did to the story."""
    lines = [f"  {col('changed:','bold')} {d.change}", ""]
    if d.gained:
        lines.append(col("  APPEARED (only in the perturbed life)", "green"))
        for f in d.gained[:limit]:
            lines.append(f"    + {col(f.pattern,'bold')}: {f.text}")
    if d.lost:
        lines.append("")
        lines.append(col("  VANISHED (only in the original)", "red"))
        for f in d.lost[:limit]:
            lines.append(f"    - {col(f.pattern,'bold')}: {f.text}")
    if d.shifted:
        lines.append("")
        lines.append(col("  SHIFTED IN WEIGHT", "yellow"))
        for (pat, a, b) in d.shifted[:limit]:
            arrow = "->" if not _USE_UNICODE else "→"
            lines.append(f"    ~ {pat}: {a:.2f} {arrow} {b:.2f}")
    if not (d.gained or d.lost or d.shifted):
        lines.append(col("  the story did not change. the dial was not load-bearing.", "grey"))
    return box("PERTURB · one dial, two lives", lines)


def render_report(result, findings=None, trace_rows=30, phi=None, qresults=None):
    """Full page: everything, in a sensible reading order."""
    parts = [
        header(f"SOMA · {result.program.title}"
               + ("  [functional-only]" if result.functional_only else "")),
        "",
        render_scenes(result),
        render_channels(result),
        render_social(result),
        render_resources(result),
        render_attention(result),
        render_moods(result),
        render_ignition(result),
        render_embodiment(result),
        render_memory(result),
        "",
        render_two_column(result),
        "",
    ]
    if qresults:
        parts.append(render_queries(qresults))
    if findings is not None:
        parts.append(render_sift(findings))
    if phi is not None:
        parts.append(render_phi(phi))
    parts.append("")
    parts.append(render_trace(result, max_rows=trace_rows))
    return "\n".join(p for p in parts if p != "")
