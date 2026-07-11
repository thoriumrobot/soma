"""
soma.mathlib -- scalar builtins usable anywhere in a SOMA expression.

The general-purpose functions (sigmoid, log, ...) plus a set of named,
theory-bearing functions adapted from the ilion standard library
(github.com/thoriumrobot/ilion), modified to suit SOMA:

  * intero_precision  -- interoceptive precision falls with arousal and noise
  * exafference       -- reafference principle: subtract the self-caused signal
  * ignition_index    -- Dehaene global-workspace ignition read-out
  * attention_strength-- Graziano attention as a softmax over salience
  * epistemic_value / pragmatic_value / policy_prob -- active-inference policy
    selection by expected free energy

These are the equations ilion wrote as stdlib `fn`s; here they are Python so any
SOMA prior/precision/dynamics expression can call them by name.
"""

from __future__ import annotations
import math


def sigmoid(x):
    if x < -60:
        return 0.0
    if x > 60:
        return 1.0
    return 1.0 / (1.0 + math.exp(-x))


# ---- ilion: interoception.ili ----
def intero_precision(arousal, noise):
    """Precision = 1 / (noise^2 (1+arousal)): a noisy, aroused body trusts its
    own signals less. (von Holst-adjacent; ilion InteroChannel.)"""
    return 1.0 / (noise * noise * (1.0 + arousal) + 1e-9)


def exafference(afferent, efference_copy, gain=0.35):
    """Reafference principle (von Holst & Mittelstaedt 1950): the world-caused
    part of a signal is the afferent minus the self-caused (reafferent) part.
    Getting the sign wrong is why you cannot tickle yourself."""
    return afferent - gain * efference_copy


# ---- ilion: workspace.ili ----
def ignition_index(a, b, c=0.0, d=0.0):
    """Dehaene ignition read-out: mean activity x pairwise coherence. Separates
    the local (sub-threshold) regime from the broadcast (ignited) one."""
    mean = 0.25 * (a + b + c + d)
    incoherence = 0.25 * (abs(a - b) + abs(b - c) + abs(c - d) + abs(d - a))
    return mean * (1.0 - incoherence)


# ---- ilion: attentionschema.ili ----
def attention_strength(salience, competing, beta=4.0):
    """How strongly attention is directed at a target, as a softmax margin."""
    return sigmoid(beta * (salience - competing))


# ---- ilion: activeinference.ili ----
def epistemic_value(sigma_prior, sigma_post):
    """Expected uncertainty reduction from an observation; >0 means 'worth
    looking'."""
    return math.log((sigma_prior + 1e-9) / (sigma_post + 1e-9))


def pragmatic_value(pred, pref, sigma=1.0):
    """Closeness of a predicted outcome to preference (negative squared error)."""
    return -0.5 * ((pred - pref) / sigma) ** 2


def policy_prob(g_a, g_b, gamma=4.0):
    """Probability of policy A under expected-free-energy softmax."""
    return sigmoid(gamma * (g_b - g_a))


BUILTINS = {
    "sigmoid": sigmoid,
    "tanh": math.tanh,
    "exp": lambda x: math.exp(min(60.0, x)),
    "log": lambda x: math.log(abs(x) + 1e-9),
    "sqrt": lambda x: math.sqrt(abs(x)),
    "abs": abs,
    "min": min,
    "max": max,
    "clamp": lambda x, lo, hi: max(lo, min(hi, x)),
    "intero_precision": intero_precision,
    "exafference": exafference,
    "ignition_index": ignition_index,
    "attention_strength": attention_strength,
    "epistemic_value": epistemic_value,
    "pragmatic_value": pragmatic_value,
    "policy_prob": policy_prob,
}


# names handled specially by the interpreter (not pure functions)
SPECIAL = ("predict", "feel", "ret", "pro", "belief", "field", "acting", "perceiving")
