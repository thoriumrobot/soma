"""
fusion.py -- identity fusion: the bond that shared suffering makes.

Grounded in identity fusion theory and the ritual-modes research:

  * Swann, Jetten, Gómez, Whitehouse & Bastian (2012), "When group membership
    gets personal": fusion is the visceral overlap of personal and social
    identity -- not liking the group, BEING it -- and it is the standout
    predictor of costly pro-group action, up to fighting and dying (Swann &
    Gómez's fight-and-die studies; Whitehouse et al., 2014, on Libyan
    revolutionaries who bond "like family").
  * Whitehouse & Lanman (2014), the two modes of ritual: the IMAGISTIC mode --
    rare, intense, dysphoric shared ordeals -- produces fusion in small, tight
    cohorts; the DOCTRINAL mode -- frequent, routinized, low-arousal
    observance -- produces identification with large anonymous communities.
    Same word "loyalty," two different machines.
  * Jong, Whitehouse, Kavanagh & Lane (2015): shared negative experience leads
    to fusion VIA PERSONAL REFLECTION -- the suffering must be turned over and
    made part of the self's story. Intensity without reflection washes out.
  * Zabala et al. (2024) and successors: fusion, once formed, is markedly
    STABLE -- resilient to group setbacks that erode mere identification --
    though over long horizons it wants refreshing cues ("...but not forever").

The layer derives a bond from how it was made, and then predicts what the
bond will do -- what its holder will pay, and whether it survives defeat:

  * derived_fusion(intensity, reflection, shared=)   -- the imagistic path
  * derived_identification(participation)            -- the doctrinal path
  * sacrifice_willingness(bond, kind, threat)        -- what they will pay
  * loyalty_under_defeat(bond, kind, defeats)        -- what defeat costs it
  * fuses(char, group, ...) / identifies_with(...)   -- wire it into a body
  * two studies: sacrifice_table, defeat_curve

The two bonds look identical on a calm day. The layer's predictions are about
the other days.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from .story import Story, Character


# ---------------------------------------------------------------------------
# the two derivations: how the bond was made decides what it is
# ---------------------------------------------------------------------------

def derived_fusion(*, intensity: float, reflection: float,
                   shared: bool = True) -> float:
    """The imagistic path (Whitehouse & Lanman, 2014). `intensity` is the
    dysphoric weight of the ordeal(s) in [0, 1]; `reflection` is how much the
    person has turned the experience over and made it part of their story
    (Jong et al., 2015 -- the mediator; intensity without reflection washes
    out). `shared` marks whether the ordeal was lived WITH the group: a
    private trauma transforms a person without fusing them to anyone.

    Fusion is multiplicative in intensity and reflection -- both are needed --
    and capped below 1: even the Libyan brigades kept a person inside the
    bond."""
    for name, v in (("intensity", intensity), ("reflection", reflection)):
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"{name} must be in [0, 1], got {v}")
    f = 0.08 + 0.80 * intensity * reflection
    if not shared:
        f *= 0.35            # transformation without communion
    return round(min(f, 0.95), 3)


def derived_identification(*, participation: float) -> float:
    """The doctrinal path: frequent, routinized, low-arousal observance. It
    scales with participation and needs no reflection -- and that is exactly
    its weakness under defeat (see loyalty_under_defeat)."""
    if not (0.0 <= participation <= 1.0):
        raise ValueError(f"participation must be in [0, 1], got {participation}")
    return round(min(0.15 + 0.65 * participation, 0.85), 3)


# ---------------------------------------------------------------------------
# what the bond will pay
# ---------------------------------------------------------------------------

def sacrifice_willingness(bond: float, *, kind: str = "fused",
                          threat: float = 0.5) -> float:
    """Willingness [0, 1] to perform a costly act for the group, at a given
    level of group threat. The fusion literature's core finding: fused members
    endorse costly, personal sacrifice (fight-and-die items, trolley-style
    self-sacrifice) at rates identification never reaches; and threat AMPLIFIES
    the fused response (fusion evolved for the group's worst hours -- Whitehouse
    et al., 2017) while barely moving the identified one."""
    if kind == "fused":
        w = bond * (0.30 + 0.70 * threat)
    elif kind == "identified":
        w = bond * (0.12 + 0.22 * threat)
    else:
        raise ValueError("kind must be 'fused' or 'identified'")
    return round(min(w, 0.98), 3)


# ---------------------------------------------------------------------------
# what defeat costs the bond
# ---------------------------------------------------------------------------

def loyalty_under_defeat(bond: float, *, kind: str = "fused",
                         defeats: int = 3, reflection: float = 0.5) -> list:
    """The bond after each successive group defeat (a lost battle, a hard
    year, a public failure). Identification is instrumental -- the group as a
    good bet -- so each defeat discounts it steeply. Fusion is constitutive --
    the group as self -- so it is resilient to defeat (Zabala et al.: markedly
    stable), and among the strongly fused a shared defeat, REFLECTED ON, is
    itself one more dysphoric shared experience: it can hold the bond level or
    even feed it. Returns [(defeat_n, bond)] including n=0."""
    rows = [(0, round(bond, 3))]
    b = bond
    for n in range(1, defeats + 1):
        if kind == "identified":
            b *= 0.62                          # a bad bet, re-priced
        elif kind == "fused":
            b = b * 0.97 + 0.04 * reflection * (1 - b)   # near-stable; reflection feeds it
        else:
            raise ValueError("kind must be 'fused' or 'identified'")
        rows.append((n, round(min(b, 0.95), 3)))
    return rows


# ---------------------------------------------------------------------------
# wiring a bond into a character
# ---------------------------------------------------------------------------

@dataclass
class Bond:
    who: str
    group: str
    kind: str
    strength: float

    def gloss(self) -> str:
        mode = ("fused (imagistic: shared ordeal, reflected on)"
                if self.kind == "fused"
                else "identified (doctrinal: routinized observance)")
        return f"{self.who} — {self.group}: {self.strength:.3f}, {mode}"


def fuses(char: Character, group: str, *, intensity: float,
          reflection: float, shared: bool = True) -> Bond:
    """Wire an imagistic bond into `char`: a `<group>_threat` channel, and a
    for-the-group drive whose ceiling is the derived fusion. When the group is
    threatened, the fused body mobilizes -- the drive is visceral, not
    calculated."""
    f = derived_fusion(intensity=intensity, reflection=reflection,
                       shared=shared)
    char.has_body_signal("for_the_group", baseline=10.0)
    char.senses(f"{group}_threat", baseline=0.0)
    char.appraises(f"{group}_threat", when=f"{group}_threat > 4",
                   drives="for_the_group",
                   to=round(10.0 + 85.0 * f, 1), fades_to=10.0,
                   precision=0.9, conviction=0.2, feeling="oneness")
    return Bond(who=char.name, group=group, kind="fused", strength=f)


def identifies_with(char: Character, group: str, *,
                    participation: float) -> Bond:
    """Wire a doctrinal bond: same channels, lower ceiling, and (the mode's
    signature) the response to threat is muted -- observance mobilizes
    attendance, not sacrifice."""
    i = derived_identification(participation=participation)
    char.has_body_signal("for_the_group", baseline=10.0)
    char.senses(f"{group}_threat", baseline=0.0)
    char.appraises(f"{group}_threat", when=f"{group}_threat > 4",
                   drives="for_the_group",
                   to=round(10.0 + 30.0 * i, 1), fades_to=10.0,
                   precision=0.9, conviction=0.2, feeling="allegiance")
    return Bond(who=char.name, group=group, kind="identified", strength=i)


# ---------------------------------------------------------------------------
# studies
# ---------------------------------------------------------------------------

@dataclass
class SacrificeReport:
    rows: list          # (label, kind, bond, willingness_low, willingness_high)

    def render(self) -> str:
        from soma.viz import bar
        out = ["THE PRICE THEY WILL PAY — willingness to costly sacrifice, "
               "calm vs. the worst hour",
               "  bond                              calm          "
               "the worst hour"]
        for label, kind, b, lo, hi in self.rows:
            out.append(f"  {label[:30]:<30} {lo:.2f} {bar(lo, 8)}  "
                       f"{hi:.2f} {bar(hi, 8)}")
        out.append("  Identification attends; fusion pays. The difference "
                   "only shows when it costs.")
        return "\n".join(out)


def sacrifice_table(bonds: list) -> SacrificeReport:
    """`bonds` is [(label, kind, bond_strength)]. Reports each bond's
    sacrifice willingness at low threat (0.1) and at the worst hour (0.95)."""
    rows = []
    for label, kind, b in bonds:
        lo = sacrifice_willingness(b, kind=kind, threat=0.1)
        hi = sacrifice_willingness(b, kind=kind, threat=0.95)
        rows.append((label, kind, b, lo, hi))
    return SacrificeReport(rows=rows)


@dataclass
class DefeatReport:
    rows: dict          # label -> [(n, bond)]

    def render(self) -> str:
        from soma.viz import bar
        out = ["LOYALTY UNDER DEFEAT — the bond after each successive loss"]
        ns = sorted({n for series in self.rows.values() for n, _ in series})
        for label, series in self.rows.items():
            out.append(f"  {label}:")
            for n, b in series:
                tag = "  <- the hard year" if n == 1 else ""
                out.append(f"    after {n} defeat{'s' if n != 1 else ' '}: "
                           f"{bar(b, 16)} {b:.3f}{tag}")
        out.append("  A bond made of observance is a bet, and defeat re-prices "
                   "it. A bond made\n  of shared suffering IS the sufferers, "
                   "and one more defeat is one more share.")
        return "\n".join(out)


def defeat_curve(bonds: list, *, defeats: int = 3,
                 reflection: float = 0.5) -> DefeatReport:
    """`bonds` is [(label, kind, strength)]. The novel's two loyalties, priced
    through the same losses."""
    rows = {}
    for label, kind, b in bonds:
        rows[label] = loyalty_under_defeat(b, kind=kind, defeats=defeats,
                                           reflection=reflection)
    return DefeatReport(rows=rows)
