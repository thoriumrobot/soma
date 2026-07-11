"""
Winnow-S: story sifting over a SOMA Chronicle.

Named after Max Kreminski's Winnow (AIIDE 2021), a declarative language for
finding narratively compelling sequences in a corpus of events. SOMA extends
the idea with interoceptive and precision predicates. Rather than ship a full
Datalog engine, we provide a curated library of *sifting patterns* -- the
dramatic shapes a novelist actually hunts for -- each a function over the
Chronicle returning ranked, prose-ready findings.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Finding:
    pattern: str
    t: float
    score: float
    text: str
    detail: dict


def _fmt_t(t: float) -> str:
    if t < 90:
        return f"{t:.1f}s"
    if t < 5400:
        return f"{t/60:.1f}m"
    if t < 172800:
        return f"{t/3600:.1f}h"
    if t < 3.1e7:
        return f"{t/86400:.1f}d"
    return f"{t/3.15e7:.1f}y"


def sift_body_knew_first(chron, window=3.0):
    """A gut/heart move, then a decision, then a reason given AFTER the fact."""
    out = []
    emits = [e for e in chron if e.kind == "emit"]
    drives = [e for e in chron if e.kind in ("drive", "spend")]
    signals = emits + drives
    decisions = [e for e in chron if e.kind == "move"]
    narrates = [e for e in chron if e.kind == "narrate"]
    # group by (signal, decision) shape: a beat that recurs is one finding
    groups = {}
    for sig in signals:
        for dec in decisions:
            if 0 <= dec.t - sig.t <= window:
                q = sig.detail.get("quale", sig.detail.get("channel", "the body"))
                key = (q, dec.detail.get("action"))
                later = [n for n in narrates if n.t >= dec.t]
                gap = max((n.detail.get("gap", 0) for n in later), default=0)
                if key in groups:
                    groups[key][2] += 1
                else:
                    groups[key] = [sig.t, gap, 1]
    for (q, action), (t0, gap, n) in groups.items():
        times = f" It happened {n} times." if n > 1 else ""
        out.append(Finding(
            "the body knew first", t0, min(1.0, 0.5 + gap),
            f"From {_fmt_t(t0)} the body moved ({q}); the choice "
            f"'{action}' followed, and the reason came only afterward.{times}",
            {"gap": gap, "n": n}))
    return out


def sift_confabulation(chron, threshold=0.5):
    """The narrator explains, or explains away, something the body says otherwise.

    A denial is only as storyful as the thing denied: "I'm fine" over a flicker of
    unease is a small gap; "I'm fine" while dread breaks through nine times is a
    person at war with their own record. So the score rises with how hard the
    denied feeling actually pressed, and the finding names it. Identical quotes
    collapse to one recurring beat (with a count and the first time)."""
    # how strongly was each feeling actually felt, across the whole run?
    felt = {}
    for e in chron:
        if e.kind in ("emit", "somatic"):
            felt[_quale(e)] = felt.get(_quale(e), 0) + 1
    groups = {}
    for e in chron:
        if e.kind == "narrate" and e.detail.get("gap", 0) >= threshold:
            q = e.detail.get("quote")
            about = e.detail.get("about", "")
            about = about[7:-1] if about.startswith("Qualia<") else about
            g = groups.setdefault(q, [e.t, e.detail["gap"], 0, about])
            g[2] += 1
    out = []
    for q, (t0, gap, n, about) in groups.items():
        pressed = felt.get(about, 0)                 # times the denied feeling fired
        # grade: a stark, recurring denial of a strongly-felt distress scores high
        score = min(0.95, gap + 0.03 * min(n, 8) + 0.025 * min(pressed, 12))
        times = f", and goes on insisting it ({n}x)" if n > 1 else ""
        if about and pressed >= 3:
            pretty = about.replace("_", " ")
            body = (f"-- while '{pretty}' kept breaking through underneath "
                    f"({pressed} times). The words are the cover story; the body "
                    f"keeps the true one.")
        else:
            body = "-- while the body's own record says otherwise."
        out.append(Finding(
            "confabulation gap", t0, round(score, 2),
            f'From {_fmt_t(t0)} the narrator insists: "{q}"{times} {body}',
            {"quote": q, "n": n, "about": about, "pressed": pressed}))
    return out


def sift_precision_pathology(chron, ignore_run=2):
    """A loop whose prior precision grows until it ignores the world."""
    out = []
    ignores = [e for e in chron if e.kind == "ignore"]
    by_loop = {}
    for e in ignores:
        by_loop.setdefault(e.who, []).append(e)
    for loop, evs in by_loop.items():
        if len(evs) >= ignore_run:
            first = evs[0]
            out.append(Finding(
                "precision pathology", first.t, min(1.0, 0.4 + 0.1 * len(evs)),
                f"'{loop}' stopped listening: it suppressed disconfirming evidence "
                f"{len(evs)} times, a belief hardening into a body.", {"n": len(evs)}))
    return out


_DISTRESS_Q = ("dread", "grief", "reaching", "pain", "terror", "despair",
               "shame", "panic", "anguish", "numbness")
_PLEASURE_Q = ("delight", "delight_at_error", "love", "joy", "warmth")


def _quale(e):
    q = e.detail.get("quale", "")
    return q[7:-1] if q.startswith("Qualia<") else q   # unwrap "Qualia<x>"


def sift_retained_residual(chron):
    """A *distressing* feeling that keeps returning after the mind moved on."""
    out = []
    by_q = {}
    for e in chron:
        if e.kind in ("emit", "somatic"):
            by_q.setdefault(_quale(e), []).append(e)
    for q, evs in by_q.items():
        if q in _DISTRESS_Q and len(evs) >= 3:
            span = evs[-1].t - evs[0].t
            out.append(Finding(
                "retained residual", evs[-1].t, min(1.0, 0.5 + 0.05 * len(evs)),
                f"{q} returned {len(evs)} times across {_fmt_t(span)} -- the body "
                f"kept a question the mind believed it had answered.",
                {"n": len(evs), "span": span}))
    return out


def sift_delight_in_error(chron):
    """The rare loop that is rewarded by being wrong: the shape of new love."""
    out = []
    by_q = {}
    for e in chron:
        if e.kind == "emit":
            by_q.setdefault(_quale(e), []).append(e)
    for q, evs in by_q.items():
        if q in _PLEASURE_Q and len(evs) >= 3:
            span = evs[-1].t - evs[0].t
            out.append(Finding(
                "delight in error", evs[0].t, min(1.0, 0.5 + 0.04 * len(evs)),
                f"{len(evs)} times across {_fmt_t(span)} the prediction failed and "
                f"the failure felt like {q} -- being surprised, and glad of it.",
                {"n": len(evs)}))
    return out


def sift_love_curdling(chron):
    """A loop whose affect flips sign: what once delighted now sours.

    The signature of a model that hardened -- a prior that was held loosely
    (and so could be gladly surprised) becoming a prior that is defended (and so
    is only irritated by the same surprise). Delight and contempt from the SAME
    loop, in that order, is the shape of a love going wrong. It is worth naming
    because the person living it never sees the turn; they only notice, years
    on, that they are tired of being surprised."""
    out = []
    by_loop = {}
    for e in chron:
        if e.kind == "emit":
            by_loop.setdefault(e.who, []).append(e)
    for loop, evs in by_loop.items():
        pleasure = [e for e in evs if _quale(e) in _PLEASURE_Q]
        sour = [e for e in evs if _quale(e) in ("contempt", "despair", "numbness")]
        if pleasure and sour and pleasure[0].t < sour[0].t:
            turn = sour[0].t
            out.append(Finding(
                "love curdling", turn, 0.95,
                f"'{loop}' was delighted to be wrong {len(pleasure)} times, and "
                f"then, from {_fmt_t(turn)}, the same surprises began to sour "
                f"into {_quale(sour[0])} -- the model had hardened from a thing "
                f"revised into a thing defended.",
                {"turn": turn, "pleasure": len(pleasure), "sour": len(sour)}))
    return out


def sift_crash_and_repair(chron):
    """Dissociation, and whether it was ever re-supervised."""
    out = []
    crashes = [e for e in chron if e.kind == "crash"]
    repairs = [e for e in chron if e.kind == "repair"]
    for c in crashes:
        rep = next((r for r in repairs if r.t > c.t), None)
        if rep:
            out.append(Finding(
                "rupture and repair", rep.t, 0.95,
                f"Dissociation at {_fmt_t(c.t)} was slowly re-supervised by "
                f"{_fmt_t(rep.t)} -- reattachment came not as a flood but as a "
                f"series of small permissions.", {}))
        else:
            out.append(Finding(
                "unrepaired rupture", c.t, 0.9,
                f"At {_fmt_t(c.t)} interoception detached and did not, within this "
                f"life, come back.", {}))
    return out


def sift_schema_image_conflict(chron):
    """The seam of embodiment: the operative body and the pictured body disagree."""
    out = []
    groups = {}
    for e in chron:
        if e.kind == "conflict":
            groups.setdefault(e.detail.get("pair"), []).append(e)
    for pair, evs in groups.items():
        e = evs[0]
        out.append(Finding(
            "schema/image conflict", e.t, min(1.0, 0.6 + 0.02 * len(evs)),
            f"'{pair}': the body that acts and the body that is pictured "
            f"disagreed {len(evs)} times from {_fmt_t(e.t)} "
            f"(schema {e.detail.get('schema')} vs image {e.detail.get('image')}) "
            f"-- the reaching hand and the missing hand are not the same hand.",
            {"n": len(evs)}))
    return out


def sift_ownership_migration(chron):
    """When a limb stops being mine, or a rubber one starts."""
    out = []
    for e in chron:
        if e.kind == "ownership":
            owned = e.detail.get("state") == "owned"
            out.append(Finding(
                "ownership migration", e.t, 0.85,
                f"At {_fmt_t(e.t)} '{e.who}' became "
                f"{'mine again' if owned else 'not-mine'} -- {e.detail.get('note','')}",
                {"state": e.detail.get("state")}))
    return out


def sift_unignited(chron):
    """Content that competed for the workspace and lost: felt, never known."""
    bc = [e for e in chron if e.kind == "broadcast"]
    ig = {e.detail.get("content") for e in chron if e.kind == "ignite"}
    groups = {}
    for e in bc:
        c = e.detail.get("content")
        if c not in ig:
            groups.setdefault(c, []).append(e)
    out = []
    for c, evs in groups.items():
        out.append(Finding(
            "never ignited", evs[0].t, 0.7,
            f"'{c}' bid for the workspace {len(evs)} times from "
            f"{_fmt_t(evs[0].t)} and never crossed threshold -- processed, "
            f"and never known.", {"n": len(evs), "content": c}))
    return out


def sift_somatic_without_episodic(chron):
    """The body remembers what the mind has no record of."""
    out = []
    groups = {}
    for e in chron:
        if e.kind == "somatic":
            groups.setdefault(e.who, []).append(e)
    for name, evs in groups.items():
        out.append(Finding(
            "body remembers alone", evs[0].t, min(1.0, 0.65 + 0.03 * len(evs)),
            f"'{name}' fired {len(evs)} times from {_fmt_t(evs[0].t)} with no "
            f"episodic trace -- a memory with a body and no story.", {"n": len(evs)}))
    return out


def sift_attention_starved(chron):
    """Deliberation that could not afford itself."""
    out = []
    groups = {}
    for e in chron:
        if e.kind == "starved":
            groups.setdefault(e.who, []).append(e)
    for name, evs in groups.items():
        out.append(Finding(
            "attention starved", evs[0].t, min(1.0, 0.5 + 0.04 * len(evs)),
            f"'{name}' wanted to deliberate {len(evs)} times and could not afford "
            f"it -- the spotlight was already spent; habit took the wheel.",
            {"n": len(evs)}))
    return out


def sift_learned_deference(chron, drop=0.5):
    """A body taught not to trust itself.

    The signature: a loop's SENSORY precision falls steeply across the run --
    not by a declared ramp but because something in the world drove it down --
    while the somatic register goes on firing the whole time. The signal never
    stopped. The permission to feel it did.

    This is the shape of medical dismissal, of a childhood spent being told you
    are exaggerating, and of every relationship in which one person's account of
    the other's interior wins. It is not repression: nothing is pushed down.
    The gain is simply turned to zero, and the organism does the rest.
    """
    out = []
    by_loop = {}
    for e in chron:
        if e.kind == "settle":
            by_loop.setdefault(e.who, []).append(e)
    somatic = [e for e in chron if e.kind == "somatic"]

    for loop, evs in by_loop.items():
        if len(evs) < 4:
            continue
        first, last = evs[0].detail.get("pi_s", 0), evs[-1].detail.get("pi_s", 0)
        if first <= 0 or last / first > drop:
            continue                       # precision did not collapse
        owner = loop.split(".")[0] if "." in loop else None
        still = [e for e in somatic
                 if (not owner or e.who.startswith(f"{owner}.")) and e.t >= evs[-1].t * 0.6]
        if not still:
            continue
        out.append(Finding(
            "learned not to feel", evs[0].t, 0.95,
            f"'{loop}' began at precision {first:.2f} and ended at {last:.2f} -- "
            f"its trust in its own senses fell by {100*(1-last/first):.0f}%. "
            f"The body never stopped signalling: the somatic register fired "
            f"{len(still)} more times after the collapse. Nothing was repressed. "
            f"The gain was turned down, and she agreed with it.",
            {"first": first, "last": last, "somatic_after": len(still)}))
    return out


def sift_ambivalence(chron):
    """Two drives pulling one channel opposite ways, at once, for the length of
    the story. The character is not undecided; they are *torn* -- wanting and
    fearing the same thing so evenly that they arrive nowhere. This is the shape
    of every approach-avoidance conflict a novel is built on.
    """
    out = []
    drives = [e for e in chron if e.kind == "allostat"]
    # group by the channel each drive regulates
    by_channel = {}
    for e in drives:
        chan = e.detail.get("regulate")
        by_channel.setdefault(chan, {}).setdefault(e.who, []).append(e)
    for chan, byname in by_channel.items():
        if len(byname) < 2:
            continue
        # find a pair pulling opposite directions (one drive positive, one neg)
        names = list(byname)
        pos = [n for n in names if byname[n] and byname[n][0].detail.get("drive", 0) > 0]
        neg = [n for n in names if byname[n] and byname[n][0].detail.get("drive", 0) < 0]
        if not (pos and neg):
            continue
        # how long did both fire together?
        overlap = min(len(byname[pos[0]]), len(byname[neg[0]]))
        if overlap < 3:
            continue
        w = pos[0].replace("_", " "); f = neg[0].replace("_", " ")
        out.append(Finding(
            "the thing they both want and fear", byname[pos[0]][0].t, 0.9,
            f"'{chan}' was pulled two ways for {overlap} moments at once -- "
            f"'{w}' toward one pole and '{f}' toward the other. Not indecision: "
            f"a steady, simultaneous wanting-and-refusing that settled nowhere. "
            f"Whatever they reached for, they were already pulling back from.",
            {"channel": chan, "toward": pos[0], "away": neg[0], "moments": overlap}))
    return out


def sift_self_betrayal(chron):
    """The moment a character does the thing they would swear they never would.
    A held value emits `self_betrayal` when its condition goes true -- and the
    narrator, subscribed to the same loop, often goes on stating the value in
    the very breath the body breaks it. That gap is the character.
    """
    out = []
    betrayals = [e for e in chron if e.kind == "emit"
                 and "self_betrayal" in str(e.detail.get("quale", ""))]
    if not betrayals:
        return out
    # group by owner
    by_owner = {}
    for e in betrayals:
        # e.who is like 'Rader.upholding_honesty' (scoped) or 'upholding_honesty'
        raw = e.who.split(".")[0] if "." in e.who else e.who
        owner = raw[len("upholding_"):] if raw.startswith("upholding_") else raw
        # for a scoped character the owner is the char name before the dot
        if "." in e.who:
            owner = e.who.split(".")[0]
        by_owner.setdefault(owner, []).append(e)
    narrates = [e for e in chron if e.kind == "narrate"]
    for owner, evs in by_owner.items():
        # was the narrator still speaking (a value, composure) as it happened?
        spoken = [n for n in narrates
                  if abs(n.t - evs[0].t) < 2.0
                  and (n.who == owner or n.who.endswith(owner)
                       or n.who in ("self", f"self_{owner}"))]
        line = spoken[0].detail.get("quote", "") if spoken else ""
        tail = (f" -- and even then the account it gave itself was \"{line}\""
                if line else "")
        out.append(Finding(
            "the value the body broke", evs[0].t, 0.92,
            f"'{owner}' crossed its own line {len(evs)} times, beginning at "
            f"{_fmt_t(evs[0].t)}: it did the thing it holds itself above{tail}. "
            f"The principle was never dropped. It was simply not what governed "
            f"the act.",
            {"owner": owner, "count": len(evs), "said": line}))
    return out


def sift_defended_core(chron):
    """What the whole psyche is organized NOT to feel. A feeling that bids
    repeatedly (it keeps being generated) yet is disproportionately the one that
    gets dissociated away, ignored, starved, or -- bid into the workspace and
    never ignited -- the sore spot the rest of the character is built around
    protecting.
    """
    out = []
    emits = [e for e in chron if e.kind == "emit"]
    if not emits:
        return out
    from collections import Counter
    # count each quale, and how often it coincided with a defense
    defenses = [e for e in chron if e.kind in ("crash", "ignore", "starved")]
    def_times = [e.t for e in defenses]

    # a feeling emitted by a loop whose broadcast never ignites is defended too:
    # gather the times of losing bids (broadcasts with no matching ignite).
    ignited = {e.detail.get("content") for e in chron if e.kind == "ignite"}
    for e in chron:
        if e.kind == "broadcast" and e.detail.get("content") not in ignited:
            def_times.append(e.t)

    if not def_times:
        return out

    # The most precise signal: a feeling carried by a part whose bid never
    # ignites. Match emits from the losing loop directly (same loop emits both
    # the broadcast and the feeling), which pins the exile's feeling exactly.
    ignited_c = {e.detail.get("content") for e in chron if e.kind == "ignite"}
    losing_loops = set()
    for e in chron:
        if e.kind == "broadcast" and e.detail.get("content") not in ignited_c:
            losing_loops.add(e.who)
    if losing_loops:
        exile_feel = Counter()
        for e in emits:
            if e.who in losing_loops:
                q = str(e.detail.get("quale", "")).replace("Qualia<", "").replace(">", "")
                exile_feel[q] += 1
        if exile_feel:
            q, n = exile_feel.most_common(1)[0]
            if n >= 3:
                out.append(Finding(
                    "the feeling the whole self defends against", 0.0, 0.9,
                    f"'{q}' is what the character will not let itself know: it "
                    f"arose {n} times from a part that bid for awareness every "
                    f"time and was never heard. The rest of the self is arranged "
                    f"around not feeling this.",
                    {"quale": q, "total": n, "defended": n}))
                return out

    # Next most precise: a feeling whose own loop is repeatedly *starved* -- the
    # character spends attention elsewhere so it never reaches them. Starvation
    # is a deeper defense than mere frequency of management, so a feeling that is
    # starved more often than it is felt is the truer defended core.
    starved_loops = Counter(e.who for e in chron if e.kind == "starved")
    if starved_loops:
        # map each starved loop to the feeling it emits, and compare how often
        # that feeling was starved vs. how often it actually got through.
        starve_feel = Counter()
        felt = Counter()
        for e in emits:
            q = str(e.detail.get("quale", "")).replace("Qualia<", "").replace(">", "")
            felt[q] += 1
            if e.who in starved_loops:
                # attribute this loop's starvation count to its feeling once
                pass
        loop_feel = {}
        for e in emits:
            if e.who in starved_loops:
                q = str(e.detail.get("quale", "")).replace("Qualia<", "").replace(">", "")
                loop_feel.setdefault(e.who, q)
        for loop, count in starved_loops.items():
            q = loop_feel.get(loop)
            if q is not None:
                starve_feel[q] += count
        # the defended feeling is the one most starved relative to being felt
        best = None
        for q, s in starve_feel.items():
            if s >= 3 and s >= felt.get(q, 0):
                if best is None or s > best[1]:
                    best = (q, s, felt.get(q, 0))
        if best:
            q, s, f = best
            out.append(Finding(
                "the feeling the whole self defends against", 0.0, 0.9,
                f"'{q}' is what the character keeps just out of reach: {s} times "
                f"the loop that would feel it wanted to and could not afford the "
                f"attention -- it got through only {f}. He spends himself "
                f"elsewhere precisely so this need never fully arrives.",
                {"quale": q, "starved": s, "felt": f}))
            return out

    quale_counts = Counter()
    quale_near_defense = Counter()
    for e in emits:
        q = str(e.detail.get("quale", "")).replace("Qualia<", "").replace(">", "")
        quale_counts[q] += 1
        if any(abs(e.t - dt) < 2.0 for dt in def_times):
            quale_near_defense[q] += 1
    for q, near in quale_near_defense.most_common(1):
        total = quale_counts[q]
        if total < 4 or near < 3:
            continue
        frac = near / total
        if frac < 0.4:
            continue
        out.append(Finding(
            "the feeling the whole self defends against", 0.0, 0.88,
            f"Of everything felt, '{q}' is the one the character keeps having to "
            f"manage: it arose {total} times and {near} of those coincided with a "
            f"defense -- a dissociation, a suppression, a bid that never reached "
            f"awareness. The rest of the psyche is arranged around not feeling "
            f"this.",
            {"quale": q, "total": total, "defended": near}))
    return out


def sift_mood_trajectory(chron, min_events=4, drift=1.5):
    """A mood that sinks (or lifts) steadily across the run -- the emotional
    weather turning while no single moment names it. This is how a scene sours:
    not one blow, but an accumulation, the slow settling of a feeling into a
    climate. Reads each mood's first value against its last.
    """
    out = []
    by_mood = {}
    for e in chron:
        if e.kind == "mood":
            by_mood.setdefault(e.who, []).append(e)
    for mood, evs in by_mood.items():
        if len(evs) < min_events:
            continue
        first = evs[0].detail.get("value", 0)
        last = evs[-1].detail.get("value", 0)
        delta = last - first
        if abs(delta) < drift:
            continue
        pretty = mood.replace("_", " ")
        if delta < 0:
            out.append(Finding(
                "a mood that sours", evs[0].t, min(0.9, 0.6 + abs(delta) / 10),
                f"'{pretty}' deepened steadily from {first:.1f} to {last:.1f} "
                f"across the run -- no single blow, just the slow settling of a "
                f"feeling into a climate. The weather turned while they weren't "
                f"looking.",
                {"mood": mood, "from": round(first, 1), "to": round(last, 1)}))
        else:
            out.append(Finding(
                "a mood that lifts", evs[0].t, min(0.9, 0.6 + abs(delta) / 10),
                f"'{pretty}' rose steadily from {first:.1f} to {last:.1f} across "
                f"the run -- something eased, a little at a time, until the whole "
                f"cast of feeling had changed.",
                {"mood": mood, "from": round(first, 1), "to": round(last, 1)}))
    return out


def sift_change_of_self(chron, split=0.5):
    """Who they were, versus who they became. Compare the first half of the run
    to the second: if the dominant feeling, or the arbitration habit (perceiving
    vs. acting), has flipped, that is a character arc -- measured, not asserted.

    Computed per character: pooling everyone's feelings would invent an arc out
    of the difference between two people, which is not a change in anyone.
    """
    out = []
    t_max = max((e.t for e in chron), default=0)
    if t_max <= 0:
        return out
    cut = t_max * split
    from collections import Counter

    # group emits and settles by owning character (the part before the dot)
    def owner_of(who):
        return who.split(".")[0] if "." in who else None

    owners = set()
    for e in chron:
        if e.kind in ("emit", "settle"):
            o = owner_of(e.who)
            if o:
                owners.add(o)
    # single-character stories have unqualified loop names -> one nameless owner
    if not owners:
        owners = {None}

    def dominant(evs):
        c = Counter(str(e.detail.get("quale", "")).replace("Qualia<", "").replace(">", "")
                    for e in evs)
        return c.most_common(1)[0] if c else (None, 0)

    def act_frac(evs):
        routes = [e.detail.get("route") for e in evs]
        acts = sum(1 for r in routes if r == "act")
        return acts / len(routes) if routes else 0

    for owner in owners:
        def mine(kind):
            return [e for e in chron if e.kind == kind
                    and (owner is None or owner_of(e.who) == owner)]
        emits = mine("emit")
        settles = mine("settle")
        if len(emits) < 6 or not settles:
            continue
        who = f"{owner}: " if owner else ""
        early_q, _ = dominant([e for e in emits if e.t <= cut])
        late_q, _ = dominant([e for e in emits if e.t > cut])
        early_act = act_frac([e for e in settles if e.t <= cut])
        late_act = act_frac([e for e in settles if e.t > cut])

        if early_q and late_q and early_q != late_q:
            out.append(Finding(
                "the person they became", cut, 0.86,
                f"{who}In the first half of their life here, what they mostly "
                f"felt was '{early_q}'. By the second half it was '{late_q}'. "
                f"The dominant key of their inner life changed -- the same "
                f"person, arriving somewhere they did not start.",
                {"owner": owner, "was": early_q, "became": late_q}))
        if abs(late_act - early_act) > 0.25:
            direction = ("stopped taking the world in and began imposing on it"
                         if late_act > early_act
                         else "stopped imposing and began, at last, to take it in")
            out.append(Finding(
                "a turn in how they meet the world", cut, 0.8,
                f"{who}Their arbitration shifted: early on {100*early_act:.0f}% "
                f"of their loops acted rather than perceived; late it was "
                f"{100*late_act:.0f}%. They {direction}.",
                {"owner": owner, "early_act": round(early_act, 2),
                 "late_act": round(late_act, 2)}))
    return out


def sift_fed_by_erasure(chron):
    """A hunger the world feeds and then wipes, so it must be fed again -- the
    shape of every dependency a place can sell. The signature is a feeling that
    fires from a `hungering_*` loop again and again across the run while a
    `feeding_*` loop keeps topping the same person up: fed, erased, hungry, fed.
    The loop never opens. This is Blade's rank washed off by the tide-clean each
    night, the coat that ends being surplus, the comb where wage and want are one
    substance."""
    out = []
    # key every hunger and feeding by (owner, craving-name), so a single craving
    # is one story whichever way it went -- wiped, unfed, or kept fed.
    aches = {}     # (owner, name) -> [(t, quale), ...]
    fed = {}       # (owner, name) -> [t, ...]
    for e in chron:
        if e.kind != "emit":
            continue
        tail = e.who.split(".")[-1]
        owner = e.who.split(".")[0] if "." in e.who else ""
        if tail.startswith("hungering_"):
            aches.setdefault((owner, tail[len("hungering_"):]), []).append(
                (e.t, _quale(e)))
        elif tail.startswith("feeding_"):
            fed.setdefault((owner, tail[len("feeding_"):]), []).append(e.t)
    seen = set(aches) | set(fed)
    for key in seen:
        owner, raw = key
        name = raw.replace("_", " ")
        ach = aches.get(key, [])
        fds = fed.get(key, [])
        was_fed = len(fds) >= 1
        if len(ach) >= 3 and was_fed:
            # fed, then wiped, then hungry again: an addiction, the loop never opens
            span = ach[-1][0] - ach[0][0]
            out.append(Finding(
                "a hunger the world keeps wiping", ach[0][0],
                min(0.95, 0.6 + 0.03 * len(ach)),
                f"'{name}' ached {len(ach)} times across {_fmt_t(span)}: a want the "
                f"world feeds and then erases, so it must be bought again -- and "
                f"fed just often enough to keep coming back. The loop never opens; "
                f"the relief is rented, never owned.",
                {"quale": ach[0][1], "n": len(ach), "fate": "wiped"}))
        elif len(ach) >= 3 and not was_fed:
            # never fed: a standing longing, not an addiction
            span = ach[-1][0] - ach[0][0]
            out.append(Finding(
                "a want the world will not feed", ach[0][0],
                min(0.95, 0.55 + 0.03 * len(ach)),
                f"'{name}' ached {len(ach)} times across {_fmt_t(span)} and was "
                f"never once fed -- one small thing wanted for no reason, and a "
                f"world that wanted the hands instead. Not an addiction; a longing "
                f"left standing open.",
                {"quale": ach[0][1], "n": len(ach), "fate": "unfed"}))
        elif was_fed and len(fds) >= 3 and len(ach) < 3:
            # fed, and it stayed fed: the healthy case, and the one that makes the
            # others legible -- the same hunger another character is destroyed by,
            # here quietly met, so it hardly aches at all (Ink's reading beside
            # Blade's rank). A satisfaction, not a dependency.
            span = fds[-1] - fds[0]
            out.append(Finding(
                "a hunger the world keeps fed", fds[0],
                0.72,
                f"'{name}' was fed {len(fds)} times across {_fmt_t(span)} and "
                f"ached only {len(ach)} -- a real hunger, quietly met, by a supply "
                f"that does not erase. The same want that starves another self is, "
                f"in this one, simply fed. The loop opens.",
                {"n": len(fds), "aches": len(ach), "fate": "fed"}))
    return out


def sift_held_in_the_dark(chron):
    """Co-regulation working: a distress loop whose alarm was flooding, and then
    a steady presence arrived and the *trust* in the alarm fell -- not the belief,
    the precision. The signature is a loop whose pi_s starts high, drops sharply
    partway through and stays low, while the thing it senses does NOT go quiet.
    The person still sees what they saw; they are simply no longer alone with it.
    Rover's biscuit, the grip in the black galleries, no one alone in the dark."""
    out = []
    by_loop = {}
    for e in chron:
        if e.kind == "settle":
            by_loop.setdefault(e.who, []).append(e)
    for loop, evs in by_loop.items():
        if len(evs) < 6:
            continue
        ps = [e.detail.get("pi_s", 0) for e in evs]
        senses = [e.detail.get("sense", 0) for e in evs]
        hi = max(ps)
        if hi < 0.3:
            continue
        # find a sustained drop: early high, late low
        n = len(ps)
        early = max(ps[:n // 3]) if n >= 3 else hi
        late = max(ps[2 * n // 3:]) if n >= 3 else ps[-1]
        if early < 0.3 or late > early * 0.4:
            continue                      # precision did not fall and stay down
        # the signal it senses did NOT go quiet (the distress is still there)
        early_sense = sum(abs(s) for s in senses[:n // 3]) / max(1, n // 3)
        late_sense = sum(abs(s) for s in senses[2 * n // 3:]) / max(1, n - 2 * n // 3)
        if late_sense < early_sense * 0.5:
            continue                      # the world quieted; that's not tending
        pretty = loop.replace("appraising_", "").replace("_", " ")
        out.append(Finding(
            "held in the dark", evs[0].t, 0.9,
            f"The alarm at '{pretty}' was believed at {early:.2f} and then, with "
            f"the signal still coming, fell to {late:.2f} and stayed -- not "
            f"argued away but carried: someone steady came into reach and the "
            f"trust placed in the fear went down while the fear's cause did not. "
            f"Not persuasion. Presence.",
            {"loop": loop, "from": round(early, 2), "to": round(late, 2)}))
    return out


def sift_the_run(chron):
    """Confidence collapsing: a belief many held only because the others held it,
    letting go all at once. The signature is a cluster of `holding_*` loops each
    emitting `resolve` while it holds, whose holdings all cease inside a narrow
    window -- one first, then the rest in a rush. Belief about other people's
    belief, and its cascade: the doctrine on the perches, the run on war-paper,
    the market that unfreezes the hour one man acts."""
    out = []
    stops = {}
    for e in chron:
        if e.kind == "emit" and e.who.split(".")[-1].startswith("holding_") \
                and "resolve" in str(e.detail.get("quale", "")):
            stops.setdefault(e.who, []).append(e.t)
    if len(stops) < 3:
        return out
    # last time each holder was still holding
    last = {loop: max(ts) for loop, ts in stops.items()}
    span_all = max(t for ts in stops.values() for t in ts) - \
        min(t for ts in stops.values() for t in ts)
    ends = sorted(last.values())
    # the collapse window: from the first holder to stop to the last
    window = ends[-1] - ends[0]
    if span_all <= 0:
        return out
    # a run: everyone stops inside a window much shorter than how long they held
    if window > 0.34 * span_all:
        return out
    first = min(last, key=lambda k: last[k])
    name = first.split("holding_")[-1].replace("_", " ")
    out.append(Finding(
        "the run", ends[0], 0.93,
        f"{len(stops)} holders kept '{name}' aloft for {_fmt_t(span_all)} -- and "
        f"then let go together inside {_fmt_t(window)}, each one going the moment "
        f"it saw the others go. What they held was never evidence; it was belief "
        f"about each other's belief, and it fell far faster than any fact could "
        f"move it.",
        {"holders": len(stops), "window": round(window, 2)}))
    return out


def sift_the_lie(chron):
    """The Lie a character believes, and its arc. A high-conviction belief that
    reads the evidence against it and suppresses it -- self-deception -- either
    breaks under the accumulated weight of what it will not look at (the self-
    revelation, a positive arc) or never does (it only hardens: the tragic arc,
    the self that meets the truth and doubles down). Read from `the_lie_*` loops:
    their suppressions (a settle that acts on a real error) and their revelations.
    """
    out = []
    lies = {}
    for e in chron:
        tail = e.who.split(".")[-1]
        if not tail.startswith("the_lie_"):
            continue
        d = lies.setdefault(e.who, {
            "suppress": 0, "reveal": [], "t0": e.t,
            "owner": e.who.split(".")[0] if "." in e.who else None})
        if e.kind == "revelation":
            d["reveal"].append(e.t)
        elif e.kind == "settle" and e.detail.get("route") == "act" \
                and abs(e.detail.get("error", 0)) > 0.5:
            d["suppress"] += 1
    for loop, d in lies.items():
        name = loop.split("the_lie_")[-1].replace("_", " ")
        who = f"{d['owner']}: " if d["owner"] else ""
        if d["reveal"]:
            t0 = d["reveal"][0]
            out.append(Finding(
                "the lie seen", t0, 0.94,
                f"{who}the lie '{name}' held while it could -- it suppressed the "
                f"evidence against it {d['suppress']} times -- and then the weight "
                f"of what it would not look at overwhelmed it, and it broke at "
                f"{_fmt_t(t0)}. The self-revelation: not argued out of the belief, "
                f"but forced by reality to see it.",
                {"loop": loop, "suppressed": d["suppress"], "seen_at": t0}))
        elif d["suppress"] >= 3:
            out.append(Finding(
                "the lie kept", d["t0"], 0.9,
                f"{who}the lie '{name}' suppressed the evidence against it "
                f"{d['suppress']} times and never broke -- each denial hardening "
                f"the next. The tragic arc: the self that meets the truth and "
                f"doubles down. What it defends stays defended, and unhealed.",
                {"loop": loop, "suppressed": d["suppress"]}))
    return out


def sift_want_need(chron):
    """Want vs Need -- the collision at the heart of an inner story. The Need is an
    ache that runs the whole time the Lie holds and is met only when the Lie is
    seen; it is *not* fed by getting the want. Read from `the_need_*` loops: if the
    ache is answered by a second, fed feeling, the need was met (the want could
    never do it; the truth did); if it aches to the end, the want never touched it.
    """
    out = []
    needs = {}
    for e in chron:
        tail = e.who.split(".")[-1]
        if e.kind == "emit" and tail.startswith("the_need_"):
            owner = e.who.split(".")[0] if "." in e.who else None
            needs.setdefault(e.who, {"q": [], "owner": owner})["q"].append(
                (e.t, _quale(e)))
    for loop, d in needs.items():
        qs = [q for _, q in d["q"]]
        distinct = list(dict.fromkeys(qs))
        name = loop.split("the_need_")[-1].replace("_", " ")
        who = f"{d['owner']}: " if d["owner"] else ""
        ache = distinct[0]
        if len(distinct) > 1:
            out.append(Finding(
                "the need met", d["q"][0][0], 0.9,
                f"{who}the need '{name}' ached as '{ache}' the whole time the lie "
                f"held, and then -- once the lie was seen -- was met at last. What "
                f"the want could never feed, the truth did.",
                {"need": name, "was": ache, "became": distinct[-1]}))
        else:
            span = d["q"][-1][0] - d["q"][0][0]
            out.append(Finding(
                "a need the want never feeds", d["q"][0][0], 0.86,
                f"{who}the need '{name}' ached as '{ache}' {len(qs)} times across "
                f"{_fmt_t(span)} and was never met -- not the kind of hunger a want "
                f"can fill. Whatever they reached for, this went on aching underneath.",
                {"need": name, "n": len(qs), "quale": ache}))
    return out


ALL_PATTERNS = {
    "learned-not-to-feel": sift_learned_deference,
    "body-knew-first": sift_body_knew_first,
    "confabulation": sift_confabulation,
    "precision-pathology": sift_precision_pathology,
    "retained-residual": sift_retained_residual,
    "delight-in-error": sift_delight_in_error,
    "love-curdling": sift_love_curdling,
    "rupture-repair": sift_crash_and_repair,
    "schema-image-conflict": sift_schema_image_conflict,
    "ownership-migration": sift_ownership_migration,
    "never-ignited": sift_unignited,
    "body-remembers-alone": sift_somatic_without_episodic,
    "attention-starved": sift_attention_starved,
    "ambivalence": sift_ambivalence,
    "self-betrayal": sift_self_betrayal,
    "defended-core": sift_defended_core,
    "the-person-they-became": sift_change_of_self,
    "mood-trajectory": sift_mood_trajectory,
    "fed-by-erasure": sift_fed_by_erasure,
    "held-in-the-dark": sift_held_in_the_dark,
    "the-run": sift_the_run,
    "the-lie": sift_the_lie,
    "want-need": sift_want_need,
}


def sift_all(chron):
    findings = []
    for fn in ALL_PATTERNS.values():
        findings.extend(fn(chron))
    # dedupe near-identical + rank by score
    findings.sort(key=lambda f: (-f.score, f.t))
    return findings


def sift(chron, pattern=None):
    if pattern is None:
        return sift_all(chron)
    if pattern not in ALL_PATTERNS:
        raise KeyError(f"unknown pattern {pattern!r}; choose from {list(ALL_PATTERNS)}")
    res = ALL_PATTERNS[pattern](chron)
    res.sort(key=lambda f: (-f.score, f.t))
    return res
