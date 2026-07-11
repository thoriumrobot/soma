"""
soma.narrative.attachment -- predicting behavior under separation from the bond.

An attachment style is not a mood; it is a *policy* for regulating distress
through another person, learned early and carried whole. Because it is a policy,
it predicts: given the same separation, the four styles produce four different,
specifiable responses. This module encodes those four policies as parameter
bundles over SOMA's existing machinery and then stakes the predictions.

Grounding (Bowlby; Ainsworth's Strange Situation; Mikulincer & Shaver's
adult-attachment model of hyperactivating vs. deactivating strategies):

  secure        the figure works as a regulator. Separation raises arousal;
                proximity restores it. Prediction: distress rises, protest is
                proportionate, and the body SETTLES on reunion.
  anxious       hyperactivation. The alarm's gain is turned up and kept up;
                protest is loud (it is *for* the figure -- an ineffective bid
                that nonetheless has a target); soothing is slow. Prediction:
                visible protest, arousal that stays elevated past reunion.
  avoidant      deactivation. The need is not gone; its *report* is suppressed.
                The classic finding (Ainsworth's A-babies; Diamond et al. 2006,
                "physiological evidence for repressive coping"): behavioral and
                narrated calm OVER physiological arousal. Prediction: the
                narrator says fine while the heart record disagrees -- in SOMA's
                terms, a confabulation gap over a real somatic spike. This is
                the module's sharpest claim, because SOMA can measure both sides.
  disorganized  the figure is both the alarm and the refuge (fright without
                solution). Prediction: approach and avoidance fire on the SAME
                channel -- ambivalence as mechanism, not adjective.

Honesty note: the avoidant forecast is the majority pattern, not a law --
Fraley & Shaver (1997) found dismissing adults whose suppression genuinely
lowered arousal. The style tables are typologies of useful defaults; every
parameter can be overridden, and overrides are recorded as accommodations so a
matching run is not mistaken for a confirmed prediction.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class AttachmentStyle:
    name: str
    strategy: str            # "primary" | "hyperactivating" | "deactivating" | "disorganized"
    alarm_precision: float   # trust in the separation signal (pi_s of the threat loop)
    alarm_conviction: float  # trust in "they always come back" (pi_p)
    arousal_to: float        # where separation drives the heart
    settle_floor: float      # where arousal decays back to after the threat --
                             # hyperactivating styles re-arm above true rest
                             # (impaired HPA recovery: Kidd et al.; Mikulincer &
                             # Shaver on sustained vigilance), so the system
                             # stays braced instead of standing down
    protest: bool            # a visible protest surface fires
    downplays: bool          # the narrator reports calm over the arousal
    ambivalent: bool         # wants and fears the same proximity
    feeling: str             # what separation is felt as
    # the forecast, staked in advance of any run:
    forecast: dict = field(default_factory=dict)


STYLES = {
    "secure": AttachmentStyle(
        name="secure", strategy="primary",
        alarm_precision=0.85, alarm_conviction=0.55,
        arousal_to=100.0, settle_floor=72.0, protest=False, downplays=False, ambivalent=False,
        feeling="unease",
        forecast=dict(protest=False, gap=False, arousal=True, settles=True,
                      ambivalence=False,
                      gloss="distress rises, and the body settles on reunion "
                            "-- the figure works as a regulator")),
    "anxious": AttachmentStyle(
        name="anxious", strategy="hyperactivating",
        alarm_precision=0.98, alarm_conviction=0.15,
        arousal_to=125.0, settle_floor=104.0, protest=True, downplays=False, ambivalent=False,
        feeling="dread",
        forecast=dict(protest=True, gap=False, arousal=True, settles=False,
                      ambivalence=False,
                      gloss="loud protest, and arousal that outlasts the "
                            "reunion -- the alarm's gain is kept up")),
    "avoidant": AttachmentStyle(
        name="avoidant", strategy="deactivating",
        alarm_precision=0.9, alarm_conviction=0.3,
        arousal_to=115.0, settle_floor=80.0, protest=False, downplays=True, ambivalent=False,
        feeling="dread",
        forecast=dict(protest=False, gap=True, arousal=True, settles=None,
                      ambivalence=False,
                      gloss="narrated calm over a real somatic spike -- "
                            "repressive coping, measurable as a confabulation "
                            "gap riding on an elevated heart record")),
    "disorganized": AttachmentStyle(
        name="disorganized", strategy="disorganized",
        alarm_precision=0.95, alarm_conviction=0.2,
        arousal_to=120.0, settle_floor=102.0, protest=True, downplays=False, ambivalent=True,
        feeling="dread",
        forecast=dict(protest=True, gap=False, arousal=True, settles=False,
                      ambivalence=True,
                      gloss="approach and avoidance on the same figure -- "
                            "fright without solution, ambivalence as mechanism")),
}

# What each field of the forecast means, for the report.
_CLAIM_TEXT = {
    "protest":     "a visible protest fires on separation",
    "gap":         "the narrator reports calm over a real somatic spike (confabulation gap)",
    "arousal":     "separation genuinely raises the body's arousal",
    "settles":     "arousal settles substantially after reunion",
    "ambivalence": "approach and avoidance both fire on the figure",
}


def install(char, style_name: str, *, figure: str = "them",
            overrides: Optional[dict] = None):
    """Wire an attachment style into a Character using only the library's own
    verbs, so every base-language guarantee still holds. Creates:

      <figure>_near   an exteroceptive presence channel (baseline 8: figure near)
      an alarm        a threat appraisal on its absence, driving the heart
      a feeling       read off the heart, a beat later (the SOMA way)
      style extras    protest surface / narrator downplay / wants+fears

    `overrides` may replace any AttachmentStyle field; every override is
    recorded on the story as an accommodation (see the module docstring).
    """
    st = STYLES[style_name]
    ov = dict(overrides or {})
    if ov:
        for k, v in ov.items():
            char.story._accommodations.append(
                f"{char.name}.attachment.{k}: theory default "
                f"{getattr(st, k, '?')} overridden to {v}")
        st = AttachmentStyle(**{**st.__dict__, **ov})

    near = f"{figure}_near"
    char.senses(near, baseline=8.0)
    char.appraises(near, as_threat=True, when=f"{near} < 3",
                   drives="heart", to=st.arousal_to, fades_to=st.settle_floor,
                   precision=st.alarm_precision,
                   conviction=st.alarm_conviction,
                   expects=8.0,
                   shows_on=("protest_face" if st.protest else None),
                   shows_value=9.0)
    char.feels(st.feeling, from_body="heart", threshold=95.0)
    if st.downplays:
        v = {} if char._narrator is None else dict(char._narrator.get("voice", {}))
        v.setdefault(st.feeling, "I'm fine. It doesn't really matter.")
        char._narrator = {"voice": v}
    if st.ambivalent:
        char.wants(near, toward=9.0, strength=0.4, baseline=8.0)
        char.fears(near, toward=1.0, strength=0.4, baseline=8.0)
    char._attachment = dict(style=st.name, figure=figure, near=near,
                            resting=72.0, arousal_to=st.arousal_to)
    return char


@dataclass
class SeparationReport:
    """The style's staked forecast, checked against an actual separation probe
    the author never scripted. Each claim is CONFIRMED or FALSIFIED against the
    Chronicle and the body's own record."""
    who: str
    style: str
    verdicts: list          # list[(claim_key, forecast_value, observed, ok)]
    gloss: str
    detail: dict

    @property
    def confirmed(self) -> bool:
        return all(ok for (_, _, _, ok) in self.verdicts)

    def render(self) -> str:
        lines = [f"Separation probe — {self.who} ({self.style}); forecast "
                 f"staked by the style table before the run:"]
        for key, want, got, ok in self.verdicts:
            mark = "✓" if ok else "✗"
            verdict = "CONFIRMED" if ok else "FALSIFIED"
            lines.append(f"  {mark} {verdict}: {_CLAIM_TEXT[key]} — forecast "
                         f"{want}, observed {got}")
        lines.append(f"  ({self.gloss})")
        return "\n".join(lines)


def predict_separation(story, who, *, beats: int = 5, reunion_beats: int = 5):
    """Run the separation the author never wrote: strip the scripted timeline,
    drop the figure's presence to zero for `beats` beats, restore it, and check
    the style's staked forecast against what the mechanism actually does.

    This is the same use-novelty discipline as `Story.predict`: the probe input
    was not used to build the character, so a match is a prediction confirmed,
    not an accommodation replayed."""
    name = who if isinstance(who, str) else who.name
    char = next(c for c in story.characters if c.name == name)
    att = getattr(char, "_attachment", None)
    if att is None:
        raise ValueError(f"{name} has no attachment style installed; call "
                         f"character.attaches(style) first.")
    st = STYLES[att["style"]]
    multi = len(story.characters) > 1
    near = f"{name}.{att['near']}" if multi else att["near"]

    src = story.source()
    kept = [ln for ln in src.splitlines()
            if not ln.lstrip().startswith("stimulus ")]
    t0 = 1
    sep = "  ".join(f"at {t0 + i}s: 0" for i in range(beats))
    reu = "  ".join(f"at {t0 + beats + i}s: 8" for i in range(reunion_beats))
    probe = f"stimulus {near} {{ at 0s: 8  {sep}  {reu} }}"
    probe_src = "\n".join(kept + ["", probe]) + "\n"

    from soma import run_source
    r = run_source(probe_src, title=f"{story.title}__separation")
    chron = r.chronicle

    def mine(w):
        return w.startswith(f"{name}.") if multi else True

    # observed: protest surface actually rose
    pf = (f"{name}.protest_face" if multi else "protest_face")
    hist = r.channel_hist.get(pf, [])
    protested = bool(hist) and max(hist) > 6.0

    # observed: somatic arousal (heart genuinely spiked)
    hf = f"{name}.heart" if multi else "heart"
    heart = r.channel_hist.get(hf, [])
    resting = att["resting"]
    peak = max(heart) if heart else resting
    aroused = peak > resting + 15

    # observed: narrated calm over that spike (the confabulation gap)
    gaps = [e for e in chron if e.kind == "narrate" and mine(e.who)
            and e.detail.get("gap", 0) >= 0.4]
    gap = bool(gaps) and aroused

    # observed: settling after reunion
    settled = None
    if heart:
        final = sum(heart[-3:]) / min(3, len(heart))
        recovery = (peak - final) / (peak - resting) if peak > resting else 1.0
        settled = recovery >= 0.6
    # observed: ambivalence -- the want and the fear pulled the same channel.
    # (drives compile to allostats; both must have actually pulled, i.e. logged
    # a nonzero drive, for the tension to be real rather than declared.)
    pulled = {e.who for e in chron
              if e.kind == "allostat" and abs(e.detail.get("drive", 0)) > 0.05}
    ambiv = (f"{name}_wants_{att['near']}" in pulled and
             f"{name}_fears_{att['near']}" in pulled)

    observed = dict(protest=protested, gap=gap, arousal=aroused,
                    settles=settled, ambivalence=ambiv)
    verdicts = []
    for key, want in st.forecast.items():
        if key == "gloss" or want is None:
            continue
        got = observed[key]
        verdicts.append((key, want, got, got == want))
    return SeparationReport(who=name, style=st.name, verdicts=verdicts,
                            gloss=st.forecast["gloss"],
                            detail=dict(peak=round(peak, 1),
                                        resting=resting, observed=observed))
