"""
soma.observables -- integrated information over a running SOMA character.

Adapted from ilion's observables.py (github.com/thoriumrobot/ilion) and
modified for SOMA's discrete loop network. The bet is the same: the runtime
already knows the causal graph, so a consciousness-relevant measure need not be
bolted onto a separate model. We build a transition probability matrix (TPM)
over a chosen set of nodes by *intervening* on the simulation -- writing the
nodes to representative binary states, stepping the loop network once with a
little stochasticity, and reading the coarse-grained outcome -- then compute
effective information and phi at the minimum-information bipartition.

HONESTY (inherited from ilion, and non-negotiable in SOMA): this is phi_approx,
not IIT 3.0/4.0 phi. Binary coarse-graining, uniform interventions, bipartition
search rather than the full cause-effect structure. Exact phi is NP-hard. Treat
every reading as a property of a *model*, never as evidence about sentience --
which is exactly the stance SOMA's opaque Qualia type already enforces.
"""

from __future__ import annotations
import itertools
import math

try:
    import numpy as np
    _HAVE_NUMPY = True
except Exception:
    _HAVE_NUMPY = False

MAX_NODES = 6
LN2 = math.log(2.0)

# clock ordering, mirrored from the interpreter (fastest first)
_CLOCK = {"neural": 0.01, "cardiac": 1.0, "breath": 4.0, "mood": 60.0,
          "hormonal": 3600.0, "circadian": 86400.0, "biography": 31_536_000.0,
          "lineage": 3.15e9}


def _entropy(p):
    p = p[p > 1e-15]
    return float(-(p * np.log(p)).sum())


def effective_information(tpm):
    """EI in nats. tpm[s, s'] = p(s'|do(s)). Uniform intervention on s."""
    ns = tpm.shape[0]
    marg = tpm.mean(axis=0)
    return _entropy(marg) - float(np.mean([_entropy(tpm[s]) for s in range(ns)]))


def ei_decomposition(tpm):
    """Hoel's determinism - degeneracy decomposition (normalised EI)."""
    ns = tpm.shape[0]
    logN = math.log(ns)
    marg = tpm.mean(axis=0)
    h_cond = float(np.mean([_entropy(tpm[s]) for s in range(ns)]))
    h_marg = _entropy(marg)
    ei = h_marg - h_cond
    return {
        "EI_bits": ei / LN2,
        "determinism": 1.0 - h_cond / logN if logN > 0 else 0.0,
        "degeneracy": 1.0 - h_marg / logN if logN > 0 else 0.0,
        "effectiveness": ei / logN if logN > 0 else 0.0,
    }


def _digits(state, n, k):
    out = []
    for _ in range(n):
        out.append(state % k); state //= k
    return out[::-1]


def _project(state, n, subset, k=2):
    d = _digits(state, n, k)
    v = 0
    for i in subset:
        v = v * k + d[i]
    return v


def _marginal_tpm(tpm, n, subset, k=2):
    m = len(subset)
    out = np.zeros((k ** m, k ** m))
    cnt = np.zeros(k ** m)
    proj = [_project(s, n, subset, k) for s in range(k ** n)]
    for s in range(k ** n):
        sa = proj[s]
        for sp in range(k ** n):
            out[sa, proj[sp]] += tpm[s, sp]
        cnt[sa] += 1
    out /= np.maximum(cnt[:, None], 1)
    return out


def phi_mip(tpm, n, k=2):
    """(phi_at_MIP, EI_whole, MIP) in nats. Exhaustive bipartition search,
    normalised by the smaller part (IIT 3.0-style)."""
    ei = effective_information(tpm)
    if n < 2:
        return 0.0, ei, ((), ())
    best = (float("inf"), 0.0, ((), ()))
    idx = list(range(n))
    for r in range(1, n // 2 + 1):
        for A in itertools.combinations(idx, r):
            B = tuple(i for i in idx if i not in A)
            if r == n - r and A[0] != 0:
                continue
            eia = effective_information(_marginal_tpm(tpm, n, A, k))
            eib = effective_information(_marginal_tpm(tpm, n, B, k))
            raw = ei - (eia + eib)
            norm = raw / (min(len(A), len(B)) * math.log(k))
            if norm < best[0]:
                best = (norm, raw, (A, B))
    return max(best[1], 0.0), ei, best[2]


def build_tpm(interp, node_channels, samples=30, jitter=0.12, seed=0):
    """Estimate p(s'|do(s)) by intervening on the *live* interpreter.

    Each node is coarse-grained to binary about the midpoint of its observed
    range. We write the nodes to representative values (with a little noise, so
    the TPM is a distribution rather than a permutation matrix), step the real
    dynamics once -- continuous flows, then loop settling, then allostatic
    regulation, which is exactly the coupling that makes the parts a whole --
    and read the coarse-grained outcome.

    The interpreter's Chronicle is swapped out for a scratch log during the
    intervention: a counterfactual must not appear in the character's history.
    """
    import random
    from .chronicle import Chronicle as _Chron

    n = len(node_channels)
    rng = random.Random(seed)
    mids = {}
    for c in node_channels:
        hist = interp.channel_hist.get(c, [])
        lo, hi = (min(hist), max(hist)) if hist else (0.0, 1.0)
        span = (hi - lo) if hi > lo else 1.0
        mids[c] = ((lo + hi) / 2.0, span)

    dt = interp.prog.sim.dt
    order = sorted(interp.loops,
                   key=lambda l: _CLOCK.get(l.decl.clock, 1.0))

    tpm = np.zeros((2 ** n, 2 ** n))
    for s in range(2 ** n):
        bits = _digits(s, n, 2)
        for _ in range(samples):
            # --- snapshot everything the step can touch
            snap_ch = {c: dict(v) for c, v in interp.channels.items()}
            snap_bel = {ls.decl.name: ls.belief for ls in interp.loops}
            snap_res = {r: dict(v) for r, v in interp.resources.items()}
            real_chron, interp.chron = interp.chron, _Chron()
            try:
                # --- do(s)
                for c, b in zip(node_channels, bits):
                    mid, span = mids[c]
                    interp.channels[c]["value"] = (
                        mid + (0.35 if b else -0.35) * span
                        + rng.uniform(-jitter, jitter) * span)
                # --- one step of the real dynamics
                interp.integrate_flows(dt, 0.0, -1)
                for ls in order:
                    interp.settle(ls, 1.0, 0.0, -1)
                interp.update_allostats(dt, 0.0, -1)
                # --- read s'
                sp = 0
                for c in node_channels:
                    mid, _span = mids[c]
                    sp = sp * 2 + (1 if interp.channels[c]["value"] >= mid else 0)
                tpm[s, sp] += 1
            finally:
                interp.chron = real_chron
                for c, v in snap_ch.items():
                    interp.channels[c] = v
                for ls in interp.loops:
                    ls.belief = snap_bel[ls.decl.name]
                for r, v in snap_res.items():
                    interp.resources[r] = v
    tpm /= np.maximum(tpm.sum(axis=1, keepdims=True), 1)
    return tpm


def integrated_information(interp, node_channels=None):
    """Top-level: pick up to MAX_NODES interoceptive/exteroceptive channels and
    return a dict with phi, EI, and Hoel's decomposition -- or a reason it could
    not be computed."""
    if not _HAVE_NUMPY:
        return {"ok": False, "reason": "numpy not available"}
    if node_channels is None:
        node_channels = [c for c in interp.channels][:MAX_NODES]
    node_channels = list(node_channels)[:MAX_NODES]
    n = len(node_channels)
    if n < 2:
        return {"ok": False, "reason": "need >= 2 channels for a partition"}
    tpm = build_tpm(interp, node_channels)
    phi, ei, mip = phi_mip(tpm, n)
    dec = ei_decomposition(tpm)
    return {
        "ok": True, "nodes": node_channels, "phi_bits": phi / LN2,
        "EI_bits": ei / LN2, "mip": mip, **dec,
    }
