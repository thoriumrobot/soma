"""
soma.narrative.mentalizing -- choice under another mind.

The 0.20 choice layer predicts what a character does at a fork whose outcomes
are fixed. This layer takes the harder fork -- the SOCIAL one, where the value
of my move depends on what you will do, and what you will do depends on what
you believe about me. That regress ("I think that you think that I think...")
is not a philosopher's curiosity: it is the computational structure of
mentalizing, and its DEPTH is a measurable character trait. This module
implements the recursive theory-of-mind (k-ToM) framework of Devaine, Hollard
& Daunizeau ("The Social Bayesian Brain", PLoS Comput Biol 2014; "Theory of
Mind: Did Evolution Fool Us?", PLoS ONE 2014; cf. Camerer's cognitive
hierarchy, and the tomsup package):

  * a 0-ToM mind does not mentalize at all: it tracks the other's overt
    behavioural tendency (a running frequency) and best-responds to it;
  * a k-ToM mind (k >= 1) attributes a MIND to the other: it holds simulations
    of the opponent at every lower level 0..k-1, a belief about WHICH level it
    is facing (updated each round by how well each simulation predicted the
    opponent's actual move), and best-responds to the mixture. Mentalizing, in
    this framework, is literally running a smaller model of the other person
    and inverting it from their behaviour.

This is also SOMA's oldest metaphysical commitment made computational: a
character never senses another's interior -- other minds arrive only as
surfaces, as moves. A k-ToM mind is exactly what modelling-an-interior-from-
surfaces IS, and the module's inverse instrument (`detect_depth`) does to a
mind what 0.19's idiographic layer does to a symptom network: reads its hidden
structure -- here, its DEPTH -- from nothing but its behaviour.

The literature's load-bearing predictions, all reproduced as generated results
(see `examples/narrative/the_other_mind.py`):

  1. THE LADDER. In competitive games (hide-and-seek), expected performance
     increases with ToM sophistication: the deeper mind exploits the shallower.
  2. THE COST OF OVER-MENTALIZING. A strict level-k mind that always models the
     other as exactly (k-1) is CATASTROPHICALLY wrong about a naive opponent --
     modelling a simple person as a schemer makes you predictable to them. The
     level-INFERRING mind (Devaine's) avoids this by learning what it faces.
     Both modes are implemented (`infer_level`).
  3. WASTED SOPHISTICATION. Against a truly random opponent there is no mind to
     read, and every depth earns the same: sophistication only pays against
     structure.
  4. READING DEPTH FROM MOVES. An opponent's k is inferable from their move
     sequence alone, by per-level likelihood -- the inverse problem for minds.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Callable
import math
import random


# ---------------------------------------------------------------------------
# games: payoff(seat, my_action, opp_action) -> utility in [0, 1]
# ---------------------------------------------------------------------------

def hide_and_seek(seat: int, a: int, o: int) -> float:
    """The competitive benchmark (Devaine et al. 2014): seat 0 is the SEEKER,
    who wins on a match; seat 1 the HIDER, who wins on a mismatch. Zero-sum:
    every point the seeker gains the hider loses."""
    match = (a == o)
    return (1.0 if match else 0.0) if seat == 0 else (0.0 if match else 1.0)


def coordination(seat: int, a: int, o: int) -> float:
    """The cooperative benchmark: both win when they match (choosing the same
    café), both lose when they miss. Not zero-sum: the other's success is
    yours."""
    return 1.0 if a == o else 0.0


GAMES = {"hide_and_seek": hide_and_seek, "coordination": coordination}


# ---------------------------------------------------------------------------
# a mind
# ---------------------------------------------------------------------------

class Mind:
    """A mentalizer of depth `k` for repeated binary games.

    k = 0: no mentalizing -- tracks the opponent's frequency of playing 1 with
    learning rate `alpha` and best-responds (softmax `beta`: how decisively the
    better move is taken).

    k >= 1, infer_level=True (default; Devaine-style): holds simulations of the
    opponent at every level 0..k-1 and a belief `w` over which it faces,
    updated each round by each simulation's likelihood of the opponent's actual
    move; predicts the opponent as the belief-weighted mixture. Deeper minds
    weakly dominate shallower ones in competitive play.

    k >= 1, infer_level=False (strict level-k / cognitive-hierarchy): assumes
    the opponent is EXACTLY (k-1)-ToM. Cheaper, and famously wrong two levels
    up -- kept because the failure is itself a character insight (see study II
    of the_other_mind.py: the paranoid mind loses to the simple one).
    """

    def __init__(self, k: int, *, alpha: float = 0.25, beta: float = 5.0,
                 payoff: Callable = hide_and_seek, seat: int = 0,
                 infer_level: bool = True):
        self.k, self.alpha, self.beta = k, alpha, beta
        self.payoff, self.seat, self.infer_level = payoff, seat, infer_level
        if k == 0:
            self.p_opp = 0.5
        elif infer_level:
            # hypothesis set: [the COIN] + [agents of depth 0..k-1]. The coin
            # hypothesis -- "there is no mind here, only a bias" -- is what
            # lets a mentalizer face a mindless process without attributing
            # strategy to it (the over-attribution cost otherwise: a 1-ToM
            # LOSES to a biased coin, because it models best-response behaviour
            # that is not there). Cf. tomsup's random-bias agents.
            self.coin_p = 0.5
            self.sims = [Mind(j, alpha=alpha, beta=beta, payoff=payoff,
                              seat=1 - seat, infer_level=infer_level)
                         for j in range(k)]
            self.w = [1.0 / (k + 1)] * (k + 1)   # w[0] = coin, w[1+j] = j-ToM
        else:
            self.sim = Mind(k - 1, alpha=alpha, beta=beta, payoff=payoff,
                            seat=1 - seat, infer_level=infer_level)

    # ---- prediction and action ----
    def predict_opp(self) -> float:
        """P(the opponent plays 1), by whatever model of them this mind holds."""
        if self.k == 0:
            return self.p_opp
        if self.infer_level:
            preds = [self.coin_p] + [s.policy() for s in self.sims]
            return sum(w * p for w, p in zip(self.w, preds))
        return self.sim.policy()

    def policy(self) -> float:
        """P(this mind plays 1): softmax best-response to its prediction."""
        p1 = self.predict_opp()
        ev = [p1 * self.payoff(self.seat, a, 1)
              + (1 - p1) * self.payoff(self.seat, a, 0) for a in (0, 1)]
        x = self.beta * (ev[1] - ev[0])
        if x < -60:
            return 0.0
        if x > 60:
            return 1.0
        return 1.0 / (1.0 + math.exp(-x))

    def act(self, rng: random.Random) -> int:
        return 1 if rng.random() < self.policy() else 0

    # ---- learning ----
    def observe(self, my_a: int, opp_a: int):
        """After a round: the naive mind updates its frequency; a mentalizing
        mind scores each simulation by how well it predicted the opponent's
        actual move (Bayesian level inference, with a small floor so no
        hypothesis dies forever), then lets each simulation live the round from
        the opponent's seat -- its 'self' move is the real opponent's, its
        'opponent' is me."""
        if self.k == 0:
            self.p_opp += self.alpha * (opp_a - self.p_opp)
            return
        if self.infer_level:
            preds = [self.coin_p] + [s.policy() for s in self.sims]
            for j, pj in enumerate(preds):
                lik = pj if opp_a == 1 else 1.0 - pj
                self.w[j] *= max(1e-6, lik)
            z = sum(self.w) or 1.0
            self.w = [max(0.02, x / z) for x in self.w]
            z = sum(self.w)
            self.w = [x / z for x in self.w]
            self.coin_p += self.alpha * (opp_a - self.coin_p)
            for s in self.sims:
                s.observe(opp_a, my_a)
        else:
            self.sim.observe(opp_a, my_a)

    def believed_opponent_level(self):
        """What this mind currently believes it faces: 'coin' (no mind, just
        a bias) or a depth 0..k-1 (argmax of its hypothesis posterior); None
        for non-inferring minds."""
        if self.k == 0 or not self.infer_level:
            return None
        j = max(range(len(self.w)), key=lambda i: self.w[i])
        return "coin" if j == 0 else j - 1


class RandomMind:
    """No mind at all: plays 1 with fixed probability `p`. The control for
    study III -- sophistication against noise."""
    k = None

    def __init__(self, p: float = 0.5, seat: int = 1):
        self.p, self.seat = p, seat

    def policy(self):
        return self.p

    def act(self, rng):
        return 1 if rng.random() < self.p else 0

    def observe(self, my_a, opp_a):
        pass


# ---------------------------------------------------------------------------
# playing
# ---------------------------------------------------------------------------

@dataclass
class Match:
    game: str
    rounds: int
    reps: int
    score_a: float                 # mean payoff per round, seat 0
    score_b: float
    history: list = field(default_factory=list)   # last rep's (a, b) moves

    def render(self) -> str:
        return (f"{self.game}: seat0 {self.score_a:.2f} vs "
                f"seat1 {self.score_b:.2f} per round "
                f"({self.rounds}r × {self.reps} reps)")


def play(mind_a_k, mind_b_k, *, game: str = "hide_and_seek", rounds: int = 60,
         reps: int = 40, seed: int = 0, alpha: float = 0.25,
         beta: float = 5.0, infer_level: bool = True,
         random_b: Optional[float] = None,
         alpha_a: Optional[float] = None, beta_a: Optional[float] = None,
         alpha_b: Optional[float] = None, beta_b: Optional[float] = None
         ) -> Match:
    """Repeated play between a seat-0 mind of depth `mind_a_k` and a seat-1
    mind of depth `mind_b_k` (or a RandomMind with P(1)=`random_b`). Fresh
    minds each repetition; returns mean payoffs per round and the last
    repetition's move history (for depth-reading). `alpha_a`/`beta_a`/
    `alpha_b`/`beta_b` override the shared `alpha`/`beta` per seat, so two
    differently-tempered minds can meet (see `face_off`)."""
    payoff = GAMES[game]
    tot_a = tot_b = 0.0
    history = []
    for r in range(reps):
        rng = random.Random(seed * 997 + r)
        A = Mind(mind_a_k, alpha=alpha_a if alpha_a is not None else alpha,
                 beta=beta_a if beta_a is not None else beta,
                 payoff=payoff, seat=0, infer_level=infer_level)
        if random_b is not None:
            B = RandomMind(random_b, seat=1)
        else:
            B = Mind(mind_b_k, alpha=alpha_b if alpha_b is not None else alpha,
                     beta=beta_b if beta_b is not None else beta,
                     payoff=payoff, seat=1, infer_level=infer_level)
        history = []
        for t in range(rounds):
            a, b = A.act(rng), B.act(rng)
            A.observe(a, b)
            B.observe(b, a)
            tot_a += payoff(0, a, b)
            tot_b += payoff(1, b, a)
            history.append((a, b))
    n = rounds * reps
    return Match(game=game, rounds=rounds, reps=reps,
                 score_a=tot_a / n, score_b=tot_b / n, history=history)


# ---------------------------------------------------------------------------
# the tournament: performance by depth
# ---------------------------------------------------------------------------

@dataclass
class Tournament:
    game: str
    levels: list
    matrix: dict                   # (kA, kB) -> seat-0 mean payoff

    def render(self) -> str:
        head = ("TOURNAMENT — " + self.game + " (cell = seat-0 payoff/round; "
                "0.50 = even)")
        cols = "            " + "  ".join(f"k={k}" for k in self.levels)
        rows = []
        for ka in self.levels:
            cells = "  ".join(f"{self.matrix[(ka, kb)]:.2f}"
                              for kb in self.levels)
            rows.append(f"  seat0 k={ka}: {cells}")
        return "\n".join([head, cols] + rows)

    def ladder_holds(self) -> bool:
        """Deeper beats shallower: every below-diagonal cell >= 0.5 and every
        one-step gap strictly above 0.5 (the competitive-game prediction)."""
        ok = True
        for ka in self.levels:
            for kb in self.levels:
                v = self.matrix[(ka, kb)]
                if ka > kb and v < 0.5 - 0.03:
                    ok = False
                if ka == kb + 1 and v <= 0.5:
                    ok = False
        return ok


def tournament(levels=(0, 1, 2, 3), *, game: str = "hide_and_seek",
               rounds: int = 60, reps: int = 40, seed: int = 0,
               infer_level: bool = True, **kw) -> Tournament:
    matrix = {}
    for ka in levels:
        for kb in levels:
            m = play(ka, kb, game=game, rounds=rounds, reps=reps, seed=seed,
                     infer_level=infer_level, **kw)
            matrix[(ka, kb)] = round(m.score_a, 3)
    return Tournament(game=game, levels=list(levels), matrix=matrix)


def depth_advantage(max_k: int = 3, *, game: str = "hide_and_seek",
                    **kw) -> list:
    """The one-step ladder: [(k, payoff of (k+1) vs k)]. In competitive games
    each rung is above 0.5 -- being one level deeper pays."""
    return [(k, play(k + 1, k, game=game, **kw).score_a)
            for k in range(max_k)]


# ---------------------------------------------------------------------------
# the inverse problem for minds: read depth from moves
# ---------------------------------------------------------------------------

@dataclass
class DepthReading:
    """Which sophistication best explains an opponent's move sequence: the
    log-likelihood of the observed moves under a simulated mind of each
    candidate depth, replayed through the same history."""
    loglik: dict                   # k -> total log-likelihood
    inferred: int

    def render(self) -> str:
        rows = "\n".join(
            f"    {k}-ToM: logL = {v:8.2f}"
            + ("   <- best account of their moves" if k == self.inferred
               else "")
            for k, v in sorted(self.loglik.items()))
        return f"DEPTH READING — whose mind fits the moves?\n{rows}"


def detect_depth(history, *, seat: int = 1, candidates=(0, 1, 2),
                 game: str = "hide_and_seek", alpha: float = 0.25,
                 beta: float = 5.0, infer_level: bool = True,
                 penalty: float = 2.0) -> DepthReading:
    """Given a move history [(a_seat0, a_seat1), ...], infer the depth of the
    mind in `seat`: replay the history through a candidate mind of each depth
    sitting in that seat, scoring the log-likelihood of the moves that mind
    actually made. The inverse move of 0.19, applied to minds: hidden structure
    (here, recursion depth) read from behaviour alone."""
    payoff = GAMES[game]
    loglik = {}
    for k in candidates:
        M = Mind(k, alpha=alpha, beta=beta, payoff=payoff, seat=seat,
                 infer_level=infer_level)
        ll = 0.0
        for (a0, a1) in history:
            mine, theirs = (a1, a0) if seat == 1 else (a0, a1)
            p1 = M.policy()
            p = p1 if mine == 1 else 1.0 - p1
            ll += math.log(max(1e-9, p))
            M.observe(mine, theirs)
        loglik[k] = round(ll, 3)
    # Occam: a deeper mind NESTS every shallower one (its hypothesis set
    # contains theirs), so raw likelihood can never prefer the shallower truth.
    # A per-level complexity penalty (BIC-flavoured) makes the comparison fair.
    scored = {k: loglik[k] - penalty * k for k in loglik}
    inferred = max(scored, key=scored.get)
    return DepthReading(loglik=loglik, inferred=inferred)


# ---------------------------------------------------------------------------
# the tell: decisiveness is legibility
# ---------------------------------------------------------------------------

@dataclass
class LegibilityReport:
    """How exploitable a shallower mind is to a deeper one, as a function of
    the shallower mind's own decisiveness (softmax beta). The finding this
    stages: the more decisively a mind converts its model into action, the
    crisper -- and hence the more readable -- its pattern is to a mind one
    level deeper. Wavering is armor; conviction is a tell."""
    shallow_k: int
    deep_k: int
    curve: list                    # (shallow beta, deep player's take)

    def render(self) -> str:
        rows = "\n".join(
            f"    their decisiveness β={b:>4.1f}: the deeper mind takes "
            + "█" * round(v * 24) + f" {v:.2f}"
            for b, v in self.curve)
        return (f"THE TELL — a {self.deep_k}-ToM reader vs a {self.shallow_k}"
                f"-ToM of varying decisiveness\n{rows}")

    def monotone(self) -> bool:
        vals = [v for _, v in self.curve]
        return all(b >= a - 0.02 for a, b in zip(vals, vals[1:]))


def legibility(shallow_k: int = 1, deep_k: int = 2, *,
               betas=(2, 3, 5, 8, 12), deep_beta: float = 5.0,
               game: str = "hide_and_seek", rounds: int = 60, reps: int = 30,
               seed: int = 0, alpha: float = 0.25) -> LegibilityReport:
    """Hold a deeper mind fixed and sweep the SHALLOWER mind's decisiveness:
    its exploitability rises with its own beta. At low beta the shallow mind
    nearly escapes the deeper one -- hesitation hides the pattern that
    conviction hands over."""
    curve = []
    for b in betas:
        m = play(deep_k, shallow_k, game=game, rounds=rounds, reps=reps,
                 seed=seed, alpha=alpha, beta_a=deep_beta, beta_b=float(b),
                 alpha_a=alpha, alpha_b=alpha)
        curve.append((float(b), m.score_a))
    return LegibilityReport(shallow_k=shallow_k, deep_k=deep_k, curve=curve)


# ---------------------------------------------------------------------------
# the bridge to character: temperament-derived minds
# ---------------------------------------------------------------------------

def social_params_of(temperament) -> tuple:
    """Derive a Mind's learning rate and decisiveness from the same two dials
    that drive a character's feelings (0.15) and choices (0.20):

      alpha (how fast their model of the other updates from moves) rises with
            PRECISION -- trust in evidence is trust in evidence about people;
      beta  (how decisively the model is converted into action) rises with
            CONVICTION -- the grip that armors beliefs also commits behaviour.

    The emergent, unauthored consequence (see the_other_mind.py study VI): the
    same conviction that protects a character's interior from evidence EXPOSES
    their surface to a deeper mind. The guarded are legible."""
    precision = getattr(temperament, "precision", 0.85)
    conviction = getattr(temperament, "conviction", 0.35)
    alpha = round(0.1 + 0.3 * precision, 3)
    beta = round(2.0 + 6.0 * conviction, 2)
    return alpha, beta


def mind_of(character, k: int = 1, *, seat: int = 0,
            game: str = "hide_and_seek", infer_level: bool = True) -> Mind:
    """A k-deep Mind whose volatility and decisiveness come from the
    character's temperament (see `social_params_of`). Accepts a narrative
    Character or a bare Temperament."""
    temp = getattr(character, "temp", character)
    alpha, beta = social_params_of(temp)
    return Mind(k, alpha=alpha, beta=beta, payoff=GAMES[game], seat=seat,
                infer_level=infer_level)


def face_off(char_a, char_b, *, k_a: int = 1, k_b: int = 1,
             game: str = "hide_and_seek", rounds: int = 60, reps: int = 30,
             seed: int = 0, infer_level: bool = True) -> Match:
    """Repeated play between two CHARACTERS: each seat's Mind takes its
    learning rate and decisiveness from that character's temperament, so who
    exploits whom is decided by disposition and depth together -- the social
    fate of two people, derived rather than authored."""
    ta = getattr(char_a, "temp", char_a)
    tb = getattr(char_b, "temp", char_b)
    aa, ba = social_params_of(ta)
    ab, bb = social_params_of(tb)
    return play(k_a, k_b, game=game, rounds=rounds, reps=reps, seed=seed,
                infer_level=infer_level,
                alpha_a=aa, beta_a=ba, alpha_b=ab, beta_b=bb)
