"""
soma.narrative.choice -- how a character chooses, and the space of their choices.

Every earlier layer predicts what a character FEELS or BECOMES. This one
predicts what they DO when they must pick -- and it does so with the one
account of choice that unifies the two things a chooser wants at once:
exploration and exploitation. Under active inference (Friston, FitzGerald,
Rigoli, Schwartenbeck, O'Doherty & Pezzulo, "Active inference and learning",
Neurosci Biobehav Rev 2016; Friston et al., "Active inference and epistemic
value", Cogn Neurosci 2015), an agent selects the policy that minimizes
EXPECTED FREE ENERGY, and expected free energy decomposes into exactly two
terms:

    G(option)  =  pragmatic value        (closeness to what I prefer)
               +  curiosity x epistemic value   (how much I'd learn)

A chooser is therefore never purely a maximizer of reward nor purely a seeker
of novelty; they are both, traded off by a single coefficient -- CURIOSITY --
that the literature identifies with precision/dopamine: confident agents
exploit, uncertain agents explore. This module makes that coefficient a
character trait and reads the whole space of a character's choices off it.

The dormant machinery this activates: `epistemic_value`, `pragmatic_value`,
and `sigmoid` have shipped in soma.mathlib (ported from ilion's
activeinference.ili) since the beginning, usable inside any SOMA expression but
never lifted to the narrative layer. `choice` is that lift.

  Option(name, reward, uncertainty)   a thing the character could choose:
                                       `reward` is where it's believed to land,
                                       `uncertainty` how unsure they are (which
                                       is both the risk AND the information on
                                       offer).

  decide(character_or_prefs, options) the probability the character picks each
                                       option, from expected free energy. A
                                       distribution, not a pick: the space of
                                       what they might do.

  explore_exploit(...)                 the signature study: the SAME options,
                                       swept over curiosity, showing a character
                                       cross from exploiting the safe bet to
                                       exploring the uncertain one -- the
                                       exploration/exploitation curve, per person.

  temptation(...)                      a preferred-but-known option vs a
                                       higher-reward-but-uncertain one: at what
                                       curiosity does the character risk it? A
                                       falsifiable threshold on a named person.

  curiosity_of(character)              derive the trait from the character's own
                                       arbitration: a high-conviction, low-
                                       sensory-precision person trusts their
                                       model and exploits (low curiosity); an
                                       open, uncertain person explores (high).
                                       So a character authored for the feeling
                                       layers already implies how they choose.

Everything is falsifiable in the usual sense: the choice distribution is a
deterministic function of the options and the trait, so it reproduces, and a
staked prediction ("this character, offered this gamble, takes it with p>0.5")
either holds when computed or does not.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import math

from soma.mathlib import epistemic_value, pragmatic_value, sigmoid


# ---------------------------------------------------------------------------
# an option
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Option:
    """Something a character could choose. `reward` is where they believe it
    lands (on the same scale as their preference); `uncertainty` is how unsure
    they are about that -- which is at once the RISK (it might be worse than
    believed) and the EPISTEMIC VALUE (choosing it would teach them where it
    really lands). A familiar option has low uncertainty; a novel one high."""
    name: str
    reward: float
    uncertainty: float = 1.0

    def posterior_uncertainty(self, obs_noise: float = 0.5) -> float:
        """How unsure they'd remain AFTER choosing it once. A choice is an
        observation with its own noise floor `obs_noise`: Bayesian updating of a
        Gaussian gives posterior variance = (1/prior_var + 1/obs_var)^-1, so a
        VAGUE prior (high uncertainty) collapses most, a SHARP one barely moves.
        This is why a novel option offers more information than a familiar one:
        both end near the same floor, but the novel one fell further to get
        there -- the epistemic value is that fall."""
        pv = self.uncertainty ** 2
        ov = obs_noise ** 2
        post_var = 1.0 / (1.0 / pv + 1.0 / ov)
        return max(1e-3, math.sqrt(post_var))


# ---------------------------------------------------------------------------
# expected free energy of an option
# ---------------------------------------------------------------------------

def expected_free_energy(option: Option, *, preference: float,
                         curiosity: float = 1.0, sigma_pref: float = 3.0,
                         obs_noise: float = 0.5) -> dict:
    """The (negative) expected free energy of choosing `option`: pragmatic value
    (how close its believed reward is to what the character prefers) plus
    curiosity-weighted epistemic value (how much choosing it would reduce their
    uncertainty). Higher is more choiceworthy. Returns the parts, so a study can
    show WHY, not just which."""
    prag = pragmatic_value(option.reward, preference, sigma=sigma_pref)
    epis = epistemic_value(option.uncertainty,
                           option.posterior_uncertainty(obs_noise))
    return {"pragmatic": prag, "epistemic": epis,
            "G": prag + curiosity * epis}


# ---------------------------------------------------------------------------
# deciding
# ---------------------------------------------------------------------------

@dataclass
class Decision:
    """The space of a character's choice: the probability of each option, and
    the free-energy breakdown behind it."""
    who: str
    preference: float
    curiosity: float
    probs: dict                    # option name -> probability
    parts: dict                    # option name -> {pragmatic, epistemic, G}

    @property
    def choice(self) -> str:
        return max(self.probs, key=self.probs.get)

    def p(self, name: str) -> float:
        return self.probs.get(name, 0.0)

    def render(self) -> str:
        lines = [f"DECISION — {self.who} (prefers {self.preference:g}, "
                 f"curiosity {self.curiosity:g}):"]
        for name in sorted(self.probs, key=self.probs.get, reverse=True):
            pt = self.parts[name]
            bar = "█" * max(1, round(self.probs[name] * 24))
            lines.append(f"  {name:<12} {bar:<24} {self.probs[name]:.0%}  "
                         f"(want {pt['pragmatic']:+.2f} + learn "
                         f"{self.curiosity:g}×{pt['epistemic']:+.2f})")
        lines.append(f"  -> chooses '{self.choice}'")
        return "\n".join(lines)


def _resolve_prefs(character_or_prefs):
    """Accept a Character, a (preference, curiosity) pair, or a dict."""
    if isinstance(character_or_prefs, dict):
        return (character_or_prefs.get("preference", 8.0),
                character_or_prefs.get("curiosity", 1.0),
                character_or_prefs.get("name", "chooser"),
                character_or_prefs.get("decisiveness", 3.0))
    if isinstance(character_or_prefs, (tuple, list)):
        pref, cur = character_or_prefs[0], character_or_prefs[1]
        return pref, cur, "chooser", 3.0
    # a narrative Character
    ch = character_or_prefs
    name = getattr(ch, "name", "chooser")
    cur = curiosity_of(ch)
    pref = getattr(ch, "_preference", 8.0)
    return pref, cur, name, 3.0


def decide(character_or_prefs, options, *, preference: float = None,
           curiosity: float = None, decisiveness: float = None,
           sigma_pref: float = 3.0, obs_noise: float = 0.5) -> Decision:
    """The probability the character picks each option, from expected free
    energy softmaxed by `decisiveness` (the inverse-temperature γ: high =
    decisive, always the best G; low = wavering; default 3.0). Pass a Character
    (traits derived), a (preference, curiosity) pair, or a dict — explicit
    keywords override whatever the first argument supplied."""
    pref, cur, name, dec = _resolve_prefs(character_or_prefs)
    if preference is not None:
        pref = preference
    if curiosity is not None:
        cur = curiosity
    if decisiveness is not None:
        dec = decisiveness

    parts = {o.name: expected_free_energy(o, preference=pref, curiosity=cur,
                                          sigma_pref=sigma_pref,
                                          obs_noise=obs_noise)
             for o in options}
    gs = {n: p["G"] for n, p in parts.items()}
    m = max(gs.values())
    exp = {n: math.exp(dec * (g - m)) for n, g in gs.items()}
    z = sum(exp.values()) or 1.0
    probs = {n: exp[n] / z for n in exp}
    return Decision(who=name, preference=pref, curiosity=cur,
                    probs=probs, parts=parts)


# ---------------------------------------------------------------------------
# deriving curiosity from a character's arbitration
# ---------------------------------------------------------------------------

def curiosity_of(character, *, floor: float = 0.1, ceil: float = 6.0) -> float:
    """Derive a character's curiosity from the same dials that drive their
    feelings. Active inference identifies the exploration/exploitation balance
    with precision: an agent confident in its model (high conviction, low trust
    in new evidence) EXPLOITS -- low curiosity; an agent that holds beliefs
    loosely and trusts what it senses EXPLORES -- high curiosity.

    So a character authored for the feeling layers already implies how they
    choose. We read conviction (trust in the prior) and precision (trust in the
    senses) off their temperament: curiosity rises with sensory precision and
    falls with conviction."""
    temp = getattr(character, "temp", None)
    if temp is None:
        return 1.0
    precision = getattr(temp, "precision", 0.85)
    conviction = getattr(temp, "conviction", 0.35)
    # openness: trusts evidence, holds priors loosely. Map to a curiosity in
    # [floor, ceil]; a balanced person (~0.85 / ~0.35) lands near 1.5.
    openness = precision * (1.0 - conviction)
    cur = floor + (ceil - floor) * max(0.0, min(1.0, openness))
    return round(cur, 3)


# ---------------------------------------------------------------------------
# the signature study: the exploration/exploitation curve
# ---------------------------------------------------------------------------

@dataclass
class ExploreExploitReport:
    who: str
    safe: str
    risky: str
    curve: list                    # (curiosity, P(risky))
    crossover: Optional[float]     # curiosity where P(risky) first exceeds 0.5

    def render(self) -> str:
        rows = "\n".join(
            f"    curiosity {c:>4.1f}: P({self.risky}) "
            + "█" * round(p * 20) + f" {p:.0%}"
            for c, p in self.curve)
        tail = (f"\n  crosses to exploring at curiosity ≈ {self.crossover:g}"
                if self.crossover is not None
                else "\n  never crosses: exploits at every curiosity in range")
        return (f"EXPLORE/EXPLOIT — {self.who}: the safe bet '{self.safe}' vs "
                f"the uncertain '{self.risky}'\n{rows}{tail}")


def explore_exploit(safe: Option, risky: Option, *, preference: float = 8.0,
                    curiosities=(0, 0.5, 1, 2, 3, 4, 5), who: str = "chooser",
                    decisiveness: float = 3.0) -> ExploreExploitReport:
    """The signature: hold two options fixed -- a safe, known one and an
    uncertain, information-rich one -- and sweep curiosity. A character crosses
    from exploiting the safe bet to exploring the risky one as curiosity rises,
    and the crossover point is where their disposition tips. Same options, a
    different chooser at each curiosity."""
    curve, crossover = [], None
    for cur in curiosities:
        d = decide((preference, cur), [safe, risky], decisiveness=decisiveness)
        p = d.p(risky.name)
        curve.append((float(cur), p))
        if crossover is None and p > 0.5:
            crossover = float(cur)
    return ExploreExploitReport(who=who, safe=safe.name, risky=risky.name,
                                curve=curve, crossover=crossover)


# ---------------------------------------------------------------------------
# temptation: the reward the character would risk their preference for
# ---------------------------------------------------------------------------

@dataclass
class TemptationReport:
    who: str
    curiosity: float
    curve: list                    # (risky_reward, P(risky))
    threshold: Optional[float]     # least risky reward that tips them

    def render(self) -> str:
        rows = "\n".join(f"    risky reward {r:>4.1f}: "
                         + "█" * round(p * 20) + f" {p:.0%}"
                         for r, p in self.curve)
        tail = (f"\n  tips at a risky reward of ≈ {self.threshold:g}"
                if self.threshold is not None
                else "\n  never tempted in range: holds the safe option")
        return (f"TEMPTATION — {self.who} (curiosity {self.curiosity:g}): how "
                f"good must the gamble look?\n{rows}{tail}")


def temptation(character_or_prefs, safe: Option, risky_uncertainty: float = 3.0,
               *, preference: float = None, rewards=(4, 5, 6, 7, 8, 9, 10),
               decisiveness: float = 3.0) -> TemptationReport:
    """Fix a safe option and a character; vary how good the UNCERTAIN option's
    believed reward is, and find the least reward at which the character risks
    it. A quantitative, falsifiable claim about a named person's boldness."""
    pref, cur, name, dec = _resolve_prefs(character_or_prefs)
    if preference is not None:
        pref = preference
    curve, threshold = [], None
    for rew in rewards:
        risky = Option(f"gamble", reward=rew, uncertainty=risky_uncertainty)
        d = decide((pref, cur), [safe, risky], decisiveness=decisiveness)
        p = d.p("gamble")
        curve.append((float(rew), p))
        if threshold is None and p > 0.5:
            threshold = float(rew)
    return TemptationReport(who=name, curiosity=cur, curve=curve,
                            threshold=threshold)
