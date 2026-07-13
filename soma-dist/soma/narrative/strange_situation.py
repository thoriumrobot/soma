"""
soma.narrative.strange_situation -- the canonical probe, run whole.

The Strange Situation (Ainsworth et al., 1978) is the most consequential
standardized experiment in the study of character: eight scripted episodes of
roughly equal length -- introduction, play, a stranger's entrance, a first
separation with the stranger present, a first reunion, a second separation
alone, the stranger's return, a second reunion -- and a coding scheme that
reads the child's attachment pattern not from what the child says or feels but
from four interactive behaviors in the two reunion episodes: proximity/contact
seeking, contact maintaining, avoidance of proximity, and resistance to
comforting. From those codes fall the classifications: secure (B) protests
proportionately, seeks contact on reunion, settles, returns to play; avoidant
(A) shows little overt protest and avoids the caregiver on reunion while
physiologically stressed; resistant/ambivalent (C) is intensely distressed,
seeks contact AND angrily resists it, fails to settle; disorganized (D)
approaches and avoids at once -- fright without solution.

This module runs the entire protocol on a SOMA character and codes the run the
way a trained observer codes the tape: from the behavior stream alone. The
classifier never sees which style was installed. That blindness is the point,
because it makes the instrument's central claim testable as PARAMETER RECOVERY
(the identifiability standard of computational modeling): install a style,
run the protocol, classify from behavior, and the classification must recover
the installed style -- for all four styles, from one shared script. A model
whose types cannot be recovered from its own behavior was never predicting;
it was labeling.

    child.attaches("avoidant", to="mother")
    report = run_protocol(story, child)
    report.classification          # -> "avoidant" -- read from the tape
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .insight import run_with, series


# the eight episodes, in order, with (caregiver_present, stranger_present).
# Episode 1 (intro, <1 min) is folded into episode 2 as in common practice.
EPISODES = [
    ("play",              True,  False),   # 2: caregiver & child
    ("stranger_enters",   True,  True),    # 3
    ("first_separation",  False, True),    # 4: stranger stays
    ("first_reunion",     True,  False),   # 5: caregiver back, stranger leaves
    ("alone",             False, False),   # 6: second separation, child alone
    ("stranger_returns",  False, True),    # 7
    ("second_reunion",    True,  False),   # 8
]

REUNIONS = ("first_reunion", "second_reunion")


@dataclass
class EpisodeCode:
    """Ainsworth's four interactive scales for one reunion episode, each 1-7,
    coded from the run's behavior stream."""
    episode: str
    seeking: float        # proximity/contact seeking (clings peak)
    maintaining: float    # contact maintaining (clings sustained)
    avoidance: float      # stressed but not seeking: the A signature
    resistance: float     # protest continuing INTO contact: the C signature

    def row(self):
        return (f"    {self.episode:<16s} seek {self.seeking:.1f}  "
                f"maintain {self.maintaining:.1f}  avoid {self.avoidance:.1f}  "
                f"resist {self.resistance:.1f}")


@dataclass
class SSReport:
    child: str
    codes: list                    # [EpisodeCode] for the two reunions
    disorganization: bool          # approach & avoidance pulling at once
    physio_over_display: bool      # somatic arousal + narrated calm (gap)
    settled_after: bool            # arousal recovered by the end
    classification: str            # "secure" | "avoidant" | "anxious" | "disorganized"
    detail: dict = field(default_factory=dict)

    def render(self) -> str:
        lines = [f"STRANGE SITUATION — {self.child}, coded from the behavior "
                 f"stream alone:"]
        for c in self.codes:
            lines.append(c.row())
        lines.append(f"    disorganization index: "
                     f"{'PRESENT' if self.disorganization else 'absent'}"
                     f" | physiological arousal over displayed calm: "
                     f"{'PRESENT' if self.physio_over_display else 'absent'}"
                     f" | settles by the end: "
                     f"{'yes' if self.settled_after else 'NO'}")
        lines.append(f"    -> CLASSIFICATION: {self.classification.upper()}")
        return "\n".join(lines)


def _script(story, child_name, caregiver, ep_beats, multi):
    """Compile the eight-episode timeline onto the presence channels."""
    near = f"{child_name}.{caregiver}_near" if multi else f"{caregiver}_near"
    strg = f"{child_name}.stranger_near" if multi else "stranger_near"
    cg_beats, st_beats = [], []
    t = 1
    windows = {}
    for name, cg, st in EPISODES:
        windows[name] = (t, t + ep_beats)
        for i in range(ep_beats):
            cg_beats.append(f"at {t + i}s: {8 if cg else 0}")
            st_beats.append(f"at {t + i}s: {7 if st else 0}")
        t += ep_beats
    lines = [f"stimulus {near} {{ at 0s: 8  {'  '.join(cg_beats)} }}",
             f"stimulus {strg} {{ at 0s: 0  {'  '.join(st_beats)} }}"]
    return lines, windows, t


def run_protocol(story, child, *, caregiver=None, ep_beats: int = 3):
    """Run the full Strange Situation on `child` (who must have an attachment
    style installed) and code the tape. The classifier reads only behavior:
    clings/protest surfaces, the heart's record, the narrator's gaps, and the
    want/fear allostats -- never the style name or its dials."""
    name = child if isinstance(child, str) else child.name
    ch = next(c for c in story.characters if c.name == name)
    att = getattr(ch, "_attachment", None)
    if att is None:
        raise ValueError(f"{name} has no attachment style installed; call "
                         f"character.attaches(style, to=...) first.")
    caregiver = caregiver or att["figure"]

    # the child needs a stranger channel and ordinary stranger wariness --
    # identical for every child (the protocol supplies the stranger, not the
    # style). Idempotent: _add_sense skips existing channels.
    ch.senses("stranger_near", baseline=0.0)
    ch.appraises("stranger_near", as_threat=True, when="stranger_near > 4",
                 drives="heart", to=90.0, fades_to=None, expects=0.0)

    multi = len(story.characters) > 1
    src = story.source()
    kept = [ln for ln in src.splitlines()
            if not ln.lstrip().startswith("stimulus ")]
    probe_lines, windows, t_end = _script(story, name, caregiver,
                                          ep_beats, multi)
    probe_src = "\n".join(kept + [""] + probe_lines) + "\n"

    from soma import run_source
    r = run_source(probe_src, title=f"{story.title}__strange_situation")

    def surf(channel):
        key = f"{name}.{channel}" if multi else channel
        return r.channel_hist.get(key, [])

    clings = surf("clings")
    protest = surf("protest_face")
    heart = surf("heart")
    times = r.times

    def window_vals(hist, ep):
        lo, hi = windows[ep]
        return [v for v, t in zip(hist, times) if lo <= t < hi] or [0.0]

    def scale(x, hi=9.0):
        """map a surface value to Ainsworth's 1-7."""
        return round(max(1.0, min(7.0, 1.0 + 6.0 * x / hi)), 1)

    # arousal: was the preceding separation somatically real?
    resting = att["resting"]
    sep_arousal = {}
    for reunion, sep in (("first_reunion", "first_separation"),
                         ("second_reunion", "stranger_returns")):
        pk = max(window_vals(heart, sep) + window_vals(heart, "alone")
                 if sep == "stranger_returns" else window_vals(heart, sep))
        sep_arousal[reunion] = pk > resting + 12

    codes = []
    for ep in REUNIONS:
        cw = window_vals(clings, ep)
        pw = window_vals(protest, ep)
        seek = scale(max(cw))
        maintain = scale(sum(cw) / len(cw))
        # avoidance: the separation genuinely aroused the body, yet the child
        # does not seek -- stressed non-seeking is Ainsworth's A signature
        avoid = scale((9.0 - max(cw)) * (1.0 if sep_arousal[ep] else 0.25))
        # resistance: protest continuing INTO the contact window
        resist = scale(max(pw))
        codes.append(EpisodeCode(ep, seek, maintain, avoid, resist))

    # disorganization: the want and the fear both actually pulled
    near_ch = att["near"]
    pulled = {e.who for e in r.chronicle
              if e.kind == "allostat" and abs(e.detail.get("drive", 0)) > 0.05}
    disorg = (f"{name}_wants_{near_ch}" in pulled and
              f"{name}_fears_{near_ch}" in pulled)

    # physiology over display: a real somatic spike with narrated calm
    gaps = [e for e in r.chronicle if e.kind == "narrate"
            and (not multi or e.who.split(".")[0] == name)
            and e.detail.get("gap", 0) >= 0.4]
    peak = max(heart) if heart else resting
    physio_over_display = bool(gaps) and peak > resting + 15

    # settling: arousal recovered by the protocol's end
    final = sum(heart[-3:]) / min(3, len(heart)) if heart else resting
    settled = ((peak - final) / (peak - resting) >= 0.6) if peak > resting else True

    classification = _classify(codes, disorg, physio_over_display, settled)
    return SSReport(child=name, codes=codes, disorganization=disorg,
                    physio_over_display=physio_over_display,
                    settled_after=settled, classification=classification,
                    detail=dict(peak=round(peak, 1), final=round(final, 1),
                                windows=windows))


def _classify(codes, disorg, physio_over_display, settled) -> str:
    """Ainsworth-style decision rules, reading only the codes. Order matters,
    as in the coding manuals: D is checked first (disorganization overrides an
    otherwise-classifiable pattern), then A, then C, then B."""
    mean_seek = sum(c.seeking for c in codes) / len(codes)
    mean_avoid = sum(c.avoidance for c in codes) / len(codes)
    mean_resist = sum(c.resistance for c in codes) / len(codes)
    if disorg:
        return "disorganized"
    if mean_avoid >= 5.0 and mean_seek <= 3.0:
        # stressed non-seeking; the narrated-calm-over-arousal signature, when
        # present, corroborates but is not required (the codes suffice)
        return "avoidant"
    if mean_resist >= 4.0 and not settled:
        return "anxious"
    if mean_seek >= 3.5 and settled:
        return "secure"
    # a fallback the coding manuals also need: seeking without settling leans
    # anxious; settled non-seekers with no arousal were never stressed enough
    # to classify hard, and read secure by default
    return "anxious" if not settled else "secure"


def validate_instrument(story_builder) -> dict:
    """Construct validity as parameter recovery: for each of the four styles,
    build a fresh child, run the protocol, classify blind, and report whether
    every installed style was recovered from behavior alone.

    `story_builder(style)` must return (story, child) with the style installed."""
    results = {}
    for style in ("secure", "anxious", "avoidant", "disorganized"):
        story, child = story_builder(style)
        rep = run_protocol(story, child)
        results[style] = rep.classification
    results["recovered"] = all(results[s] == s for s in
                               ("secure", "anxious", "avoidant", "disorganized"))
    return results
