"""
soma.narrative.signature -- the if...then behavioral signature (CAPS).

Mischel & Shoda's Cognitive-Affective Personality System (CAPS; Psychological
Review, 1995) resolved the person-situation debate with one move: personality is
not a bundle of average traits but a STABLE PROFILE OF SITUATION -> BEHAVIOR
CONTINGENCIES -- "if situation A, then X; if situation B, then Y." The decisive
evidence is the Wediko summer-camp field study (Shoda, Mischel & Wright, 1994):
children whose average trait scores were indistinguishable had wildly different,
highly stable if...then profiles. The profile -- not the mean -- is the person's
"behavioral signature". Variability across situations is not noise around a
trait; it IS the trait's structure.

SOMA is unusually well placed to make this literal, because a character already
IS the thing CAPS says a person is: a stable network of cognitive-affective
units (loops, precisions, convictions, defended beliefs) that a situation
activates differently depending on which units read it. This module extracts
the signature the network implies:

  signature(story, who, situations)   probe the character with each situation in
                                      a battery (via Story.probe -- every
                                      scripted event stripped, one unseen input
                                      at a time) and record, per situation, what
                                      their arbitration did with it (suppress /
                                      take-in / unmoved), what they felt, and
                                      whether anything broke. The result is the
                                      if...then profile, and it is a PREDICTION:
                                      none of these situations was authored.

  similarity(a, b)                    how alike two signatures are, situation by
                                      situation -- Shoda's profile-stability
                                      question turned into a number. Two
                                      characters can be MEAN-LEVEL IDENTICAL
                                      (same fraction of suppressions overall)
                                      and signature-different, which is exactly
                                      the Wediko result; `mean_level` exposes
                                      the average so a test can assert both.

  diagnostic_situation(story, a, b,   the situation in a battery that maximally
                       situations)    separates two characters -- the probe an
                                      author (or a scene) should stage to make
                                      the difference between two people visible.
                                      A discrimination study at the level of
                                      situations rather than parameters.

The signature is falsifiable twice over: re-run the same battery and the profile
must reproduce (stability -- CAPS's core empirical claim), and stage any single
if...then in the story proper and the predicted response must appear in the
Chronicle.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# one cell of the profile: if <situation>, then <response>
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IfThen:
    """One contingency of the signature: the situation presented, and what the
    character's arbitration did with it."""
    situation: str          # the battery label
    stimulus: dict          # the {channel: value} actually presented
    route: str              # suppress | take-in | mixed | unmoved
    feelings: tuple         # qualia that fired, in order of first firing
    breaks_lie: Optional[str]   # a lie the situation overwhelmed, if any
    break_time: Optional[float]

    def then_clause(self) -> str:
        felt = f", feeling {'/'.join(self.feelings)}" if self.feelings else ""
        if self.breaks_lie:
            return (f"it BREAKS '{self.breaks_lie.replace('the_lie_', '').replace('_', ' ')}'"
                    f" at ~{self.break_time:.0f}s{felt}")
        return {"suppress": "they SUPPRESS it",
                "take-in": "they TAKE IT IN",
                "mixed": "it divides them",
                "unmoved": "it does not reach them"}[self.route] + felt

    def render(self) -> str:
        return f"if {self.situation:<24} then {self.then_clause()}"


@dataclass
class SignatureReport:
    """A character's behavioral signature over a battery of situations: the
    stable if...then profile CAPS says the person IS."""
    who: str
    cells: list                  # list[IfThen], in battery order

    # -- mean level: what a trait score would see -------------------------------
    def mean_level(self) -> dict:
        """The situation-free average -- the 'trait score' view of the same runs.
        CAPS's point is that this can be identical across two people whose
        signatures differ; keeping it here lets a study assert both halves."""
        n = max(1, len(self.cells))
        routes = [c.route for c in self.cells]
        return {
            "suppress_rate": routes.count("suppress") / n,
            "take_in_rate": routes.count("take-in") / n,
            "break_rate": sum(1 for c in self.cells if c.breaks_lie) / n,
            "feeling_rate": sum(1 for c in self.cells if c.feelings) / n,
        }

    def cell(self, situation: str) -> Optional[IfThen]:
        for c in self.cells:
            if c.situation == situation:
                return c
        return None

    def render(self) -> str:
        head = f"Behavioral signature -- {self.who} (if...then profile; every situation unseen):"
        body = "\n".join("  " + c.render() for c in self.cells)
        m = self.mean_level()
        foot = (f"  mean level (the trait-score view): suppresses {m['suppress_rate']:.0%},"
                f" takes in {m['take_in_rate']:.0%}, breaks {m['break_rate']:.0%}")
        return "\n".join([head, body, foot])


# ---------------------------------------------------------------------------
# extracting the signature
# ---------------------------------------------------------------------------

def signature(story, who, situations: dict, *, beats: int = 6) -> SignatureReport:
    """Probe `who` with each situation in `situations` ({label: {channel: value}}
    or {label: (channel, value)}) and return the if...then profile.

    Each probe uses Story.predict's machinery (scripted events stripped, one
    unseen input sustained for `beats` beats), so every cell is a positive
    prediction, and the whole profile is CAPS's claim about the person: not what
    they do on average, but what they do WHEN."""
    name = who.name if hasattr(who, "name") else who
    cells = []
    for label, stim in situations.items():
        if isinstance(stim, tuple):
            stim = {stim[0]: stim[1]}
        p = story.predict(name, dict(stim), beats=beats)
        cells.append(IfThen(situation=label, stimulus=dict(stim),
                            route=p.route, feelings=tuple(p.feelings),
                            breaks_lie=p.breaks_lie, break_time=p.break_time))
    return SignatureReport(who=name, cells=cells)


# ---------------------------------------------------------------------------
# comparing signatures
# ---------------------------------------------------------------------------

def _cell_agreement(a: IfThen, b: IfThen) -> float:
    """How alike two responses to the same situation are: route (weight 0.6),
    whether a lie broke (0.25), and overlap of what was felt (0.15)."""
    s = 0.0
    if a.route == b.route:
        s += 0.6
    if (a.breaks_lie is None) == (b.breaks_lie is None):
        s += 0.25
    fa, fb = set(a.feelings), set(b.feelings)
    if fa or fb:
        s += 0.15 * (len(fa & fb) / len(fa | fb))
    else:
        s += 0.15
    return s


def similarity(a: SignatureReport, b: SignatureReport) -> float:
    """Profile similarity in [0, 1], computed situation by situation over the
    battery the two signatures share. 1.0 = the same if...then profile. Two
    characters with equal `mean_level` and low `similarity` are the Wediko
    finding: trait-identical, signature-different."""
    shared = [(ca, b.cell(ca.situation)) for ca in a.cells
              if b.cell(ca.situation) is not None]
    if not shared:
        return 0.0
    return sum(_cell_agreement(ca, cb) for ca, cb in shared) / len(shared)


def diagnostic_situation(story, a, b, situations: dict, *, beats: int = 6) -> dict:
    """The situation in the battery that maximally separates two characters --
    the single probe that makes the difference between them visible. Returns
    {situation, separation, a: IfThen, b: IfThen, similarity} where `separation`
    is 1 - cell agreement at the most-separating situation and `similarity` is
    the whole-profile similarity for context."""
    sig_a = signature(story, a, situations, beats=beats)
    sig_b = signature(story, b, situations, beats=beats)
    best = None
    for ca in sig_a.cells:
        cb = sig_b.cell(ca.situation)
        sep = 1.0 - _cell_agreement(ca, cb)
        if best is None or sep > best["separation"]:
            best = {"situation": ca.situation, "separation": round(sep, 3),
                    "a": ca, "b": cb}
    best["similarity"] = round(similarity(sig_a, sig_b), 3)
    return best
