"""
SOMA lexer.

Turns SOMA source text into a flat list of tokens. The language is free-form
(whitespace and newlines are insignificant); structure comes from keywords and
braces. Every construct in an act-block or a loop-body is keyword-led, so we
never need statement separators -- though `;` is accepted and ignored.

Language improvement over the 0.1 manifesto: the pretty Unicode forms from the
spec (the loop brackets and the down/up arrows) are hard to type, so the
canonical surface syntax is ASCII. The Unicode forms are still accepted as
aliases, so spec-flavoured code keeps working.
"""

from __future__ import annotations
from dataclasses import dataclass

# Duration suffixes -> seconds
_UNITS = {"ms": 1e-3, "s": 1.0, "m": 60.0, "h": 3600.0, "d": 86400.0, "y": 31_536_000.0}

KEYWORDS = {
    "sim", "let", "body", "intero", "extero", "proprio", "resource",
    "stimulus", "loop", "prior", "sense", "precision", "conviction", "act",
    "update", "move", "ignore", "emit", "feel", "predict", "mood",
    "integrates", "decay", "narrator", "subscribes", "confabulates", "voice",
    "handle", "with", "when", "after", "dissociate", "reattach", "repair",
    "baseline", "retention", "protention", "ramp", "over", "schedule",
    "true", "false", "at", "split", "spend", "set", "titrate",
    # --- 0.3 additions ---
    "flow", "dynamics", "embodiment", "schema", "image", "pair", "tolerance",
    "memory", "episodic", "semantic", "procedural", "somatic", "cue", "evoke",
    "strength", "attention", "spotlight", "salience", "attend", "mode",
    "habit", "deliberate", "workspace", "ignite", "broadcast", "threshold",
    "awareness", "tracks", "introspect", "transparent", "allostat", "regulate",
    "setpoint", "gain", "efference", "rebus", "intervene", "ownership",
    "predicted", "observed", "query", "find", "where", "surface", "phi",
    "of", "capacity",
    # --- 0.4: intersubjectivity, narrative structure, learning ---
    "character", "couple", "lag", "scene", "from", "to", "learn",
    "contagion", "trust", "regard",
}
# NB: `overwhelm` is a *soft* loop-field keyword (matched by string in the loop
# parser), deliberately NOT reserved here, so it stays usable as a feeling or
# channel name ("emit feel(overwhelm)").

# Unicode aliases -> canonical ASCII token text
_ALIASES = {
    "◜": "{", "◞": "}",  # loop brackets
    "⤋": "->",           # update / belief flows down
    "⤊": "^",            # error rises (rarely used directly)
}


@dataclass
class Token:
    type: str      # 'KW', 'ID', 'NUM', 'DUR', 'STR', 'OP', 'EOF'
    value: str
    num: float | None = None   # for NUM / DUR
    line: int = 0
    col: int = 0

    def __repr__(self):
        return f"Token({self.type},{self.value!r},L{self.line})"


class LexError(Exception):
    pass


# Multi-char operators, longest first
_OPS = ["<=", ">=", "==", "!=", "->", "=>", ":", ",", ";", "(", ")",
        "{", "}", "@", "=", "+", "-", "*", "/", "<", ">", "!", "^", "."]


def tokenize(src: str) -> list[Token]:
    toks: list[Token] = []
    i, line, col = 0, 1, 1
    n = len(src)

    def emit(t, v, **kw):
        toks.append(Token(t, v, line=line, col=col, **kw))

    while i < n:
        c = src[i]

        # newlines / whitespace
        if c == "\n":
            line += 1; col = 1; i += 1; continue
        if c in " \t\r":
            i += 1; col += 1; continue

        # comments: // ... or # ...
        if src.startswith("//", i) or c == "#":
            while i < n and src[i] != "\n":
                i += 1
            continue

        # unicode aliases
        if c in _ALIASES:
            rep = _ALIASES[c]
            emit("OP", rep)
            i += 1; col += 1
            continue

        # strings
        if c == '"':
            j = i + 1
            buf = []
            while j < n and src[j] != '"':
                if src[j] == "\\" and j + 1 < n:
                    esc = src[j + 1]
                    buf.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(esc, esc))
                    j += 2
                else:
                    buf.append(src[j]); j += 1
            if j >= n:
                raise LexError(f"unterminated string at line {line}")
            emit("STR", "".join(buf))
            col += (j - i + 1); i = j + 1
            continue

        # numbers (with optional duration unit)
        if c.isdigit() or (c == "." and i + 1 < n and src[i + 1].isdigit()):
            j = i
            while j < n and (src[j].isdigit() or src[j] == "."):
                j += 1
            numtext = src[i:j]
            # duration unit?
            unit = ""
            k = j
            while k < n and src[k].isalpha():
                unit += src[k]; k += 1
            if unit in _UNITS:
                emit("DUR", numtext + unit, num=float(numtext) * _UNITS[unit])
                col += (k - i); i = k
            else:
                emit("NUM", numtext, num=float(numtext))
                col += (j - i); i = j
            continue

        # @clock and identifiers/keywords
        if c == "@":
            j = i + 1
            while j < n and (src[j].isalnum() or src[j] == "_"):
                j += 1
            emit("CLOCK", src[i + 1:j])
            col += (j - i); i = j
            continue

        # query variables: ?name
        if c == "?":
            j = i + 1
            while j < n and (src[j].isalnum() or src[j] == "_"):
                j += 1
            emit("VAR", src[i:j])
            col += (j - i); i = j
            continue

        if c.isalpha() or c == "_":
            j = i
            while j < n and (src[j].isalnum() or src[j] == "_"):
                j += 1
            # a dotted name (Bob.face) is a single identifier, provided the dot
            # is followed by a letter -- so `1.5` and `x.` never get swallowed
            while j + 1 < n and src[j] == "." and (src[j+1].isalpha() or src[j+1] == "_"):
                j += 1
                while j < n and (src[j].isalnum() or src[j] == "_"):
                    j += 1
            word = src[i:j]
            emit("KW" if word in KEYWORDS else "ID", word)
            col += (j - i); i = j
            continue

        # operators
        for op in _OPS:
            if src.startswith(op, i):
                emit("OP", op)
                col += len(op); i += len(op)
                break
        else:
            raise LexError(f"unexpected char {c!r} at line {line} col {col}")

    toks.append(Token("EOF", "", line=line, col=col))
    return toks
