"""
SOMA parser: tokens -> Program AST.

Recursive descent, deliberately forgiving. Because every field and statement is
keyword-led, we never depend on newlines or separators.
"""

from __future__ import annotations
from .lexer import tokenize, Token
from . import ast_nodes as A


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, toks: list[Token], title: str = "untitled"):
        self.toks = toks
        self.i = 0
        self.prog = A.Program(title=title)
        self.scope = None      # current `character` name, or None

    # ---- token helpers ----
    @property
    def cur(self) -> Token:
        return self.toks[self.i]

    def at(self, value: str) -> bool:
        return self.cur.value == value

    def at_type(self, t: str) -> bool:
        return self.cur.type == t

    def peek_is(self, value: str) -> bool:
        """Is the token AFTER the current one this value? Used to disambiguate a
        builtin used as a call (`feel(x)`) from the same word used as a plain
        name (`error(feel)`)."""
        nxt = self.toks[self.i + 1] if self.i + 1 < len(self.toks) else None
        return nxt is not None and nxt.value == value

    def advance(self) -> Token:
        t = self.toks[self.i]
        self.i += 1
        return t

    def expect(self, value: str) -> Token:
        if not self.at(value):
            raise ParseError(f"expected {value!r} but got {self.cur.value!r} at line {self.cur.line}")
        return self.advance()

    def expect_type(self, t: str) -> Token:
        if not self.at_type(t):
            raise ParseError(f"expected {t} but got {self.cur.type} {self.cur.value!r} at line {self.cur.line}")
        return self.advance()

    def name(self) -> str:
        """A declaration name. Soft keywords are allowed: `attention spotlight`
        binds the name 'spotlight' even though `spotlight` is a keyword. Only
        structurally-positioned keywords are truly reserved."""
        if self.cur.type in ("ID", "KW"):
            return self.advance().value
        raise ParseError(f"expected a name but got {self.cur.value!r} at line {self.cur.line}")

    def q(self, n: str) -> str:
        """Qualify a name with the enclosing character scope.

        Inside `character Alice { ... }`, a bare `heart` means `Alice.heart`.
        A name that already carries a dot (`Bob.face`) is cross-character and is
        left exactly as written -- which is what makes the look, and the misread
        face, expressible."""
        if self.scope and "." not in n:
            return f"{self.scope}.{n}"
        return n

    def opt(self, value: str) -> bool:
        if self.at(value):
            self.advance()
            return True
        return False

    # ---- entry ----
    def parse(self) -> A.Program:
        while not self.at_type("EOF"):
            self.decl()
        return self.prog

    def decl(self):
        v = self.cur.value
        # @consent(...) is lexed as a CLOCK token with value "consent"
        if self.at_type("CLOCK") and v == "consent":
            self.advance()
            self.expect("(")
            strings = [self.expect_type("STR").value]
            while self.opt(","):
                strings.append(self.expect_type("STR").value)
            self.expect(")")
            self.prog.consent.extend(strings)
            return
        if v == "sim":
            return self.sim_decl()
        if v == "let":
            return self.let_decl()
        if v == "body":
            return self.body_decl()
        if v == "resource":
            return self.resource_decl()
        if v == "stimulus":
            return self.stimulus_decl()
        if v == "loop":
            return self.loop_decl()
        if v == "mood":
            return self.mood_decl()
        if v == "narrator":
            return self.narrator_decl()
        if v == "handle":
            return self.handler_decl()
        if v == "flow":
            return self.flow_decl()
        if v == "embodiment":
            return self.embodiment_decl()
        if v == "memory":
            return self.memory_decl()
        if v == "attention":
            return self.attention_decl()
        if v == "workspace":
            return self.workspace_decl()
        if v == "awareness":
            return self.awareness_decl()
        if v == "allostat":
            return self.allostat_decl()
        if v == "intervene":
            return self.intervene_decl()
        if v == "ownership":
            return self.ownership_decl()
        if v == "query":
            return self.query_decl()
        if v == "character":
            return self.character_decl()
        if v == "couple":
            return self.couple_decl()
        if v == "scene":
            return self.scene_decl()
        raise ParseError(f"unexpected top-level {v!r} at line {self.cur.line}")

    # ---- 0.4: characters, coupling, scenes ----
    def character_decl(self):
        self.expect("character")
        who = self.name()
        if self.scope:
            raise ParseError("characters may not be nested")
        self.prog.characters.append(who)
        self.scope = who
        self.expect("{")
        while not self.at("}"):
            self.decl()
        self.expect("}")
        self.scope = None

    def couple_decl(self):
        """couple Alice.face -> Bob.sees_face { gain 0.9  lag 0.4s }

        One body's state becomes another's sensation. This is the whole of
        intersubjectivity in SOMA: B never touches A's interior, only the
        surface A presents, delayed, attenuated, and open to misreading."""
        self.expect("couple")
        src = self.name()
        self.expect("->")
        dst = self.name()
        gain, lag = 1.0, 0.0
        if self.opt("{"):
            while not self.at("}"):
                k = self.advance().value
                self.opt(":")
                v = self._num()
                if k == "gain":
                    gain = v
                elif k == "lag":
                    lag = v
            self.expect("}")
        self.prog.couples.append(A.Couple(src, dst, gain, lag))

    def scene_decl(self):
        """scene "The Kitchen" from 0s to 40s"""
        self.expect("scene")
        title = self.expect_type("STR").value
        self.expect("from"); t0 = self._num()
        self.expect("to");   t1 = self._num()
        self.prog.scenes.append(A.Scene(title, t0, t1))

    # ---- sim ----
    def sim_decl(self):
        self.expect("sim"); self.expect("{")
        s = A.Sim()
        while not self.at("}"):
            key = self.advance().value
            self.opt(":")
            if key == "cadence":
                s.cadence = self.advance().value == "true"
                continue
            tok = self.advance()
            val = tok.num if tok.num is not None else float(tok.value)
            if key == "duration":
                s.duration = val
            elif key == "dt":
                s.dt = val
        self.expect("}")
        self.prog.sim = s

    # ---- let ----
    def let_decl(self):
        self.expect("let")
        # soft keywords: `let tolerance = ...` should bind, not fail
        name = self.advance().value
        self.expect("=")
        self.prog.lets.append(A.Let(name, self.expr()))

    # ---- body ----
    def body_decl(self):
        self.expect("body")
        name = self.q(self.name())
        clock = self.expect_type("CLOCK").value
        self.expect("{")
        chans = []
        while not self.at("}"):
            modality = self.advance().value   # intero/extero/proprio
            cname = self.q(self.name())
            self.expect(":")
            ctype = self.advance().value
            ch = A.Channel(modality, cname, ctype)
            while self.cur.value in ("baseline", "retention", "protention",
                                     "efference", "gain"):
                kw = self.advance().value
                if kw == "efference":
                    ch.efference = self.q(self.advance().value)
                    continue
                tok = self.advance()
                num = tok.num if tok.num is not None else float(tok.value)
                if kw == "baseline":
                    ch.baseline = num
                elif kw == "retention":
                    ch.retention = num
                elif kw == "gain":
                    ch.gain = num
                else:
                    ch.protention = num
            chans.append(ch)
        self.expect("}")
        self.prog.bodies.append(A.Body(name, clock, chans, owner=self.scope))

    # ---- resource ----
    def resource_decl(self):
        self.expect("resource")
        name = self.q(self.name())
        self.expect(":")
        # optional type annotation like Affine<Joule>
        unit = "Joule"
        if self.at_type("ID"):
            tyname = self.advance().value
            if self.opt("<"):
                unit = self.advance().value
                self.expect(">")
            if tyname != "Affine":
                unit = tyname
        self.expect("=")
        # metabolic_reserve(1200) or a number
        amount = 0.0
        if self.at_type("ID"):
            self.advance()  # fn name
            self.expect("(")
            amount = self.advance().num or 0.0
            self.expect(")")
        else:
            amount = self.advance().num or 0.0
        self.prog.resources.append(A.Resource(name, amount, unit))

    # ---- stimulus ----
    def stimulus_decl(self):
        self.expect("stimulus")
        ch = self.q(self.name())
        self.expect("{")
        events = []
        while not self.at("}"):
            self.expect("at")
            tok = self.advance()
            t = tok.num if tok.num is not None else float(tok.value)
            self.expect(":")
            vtok = self.advance()
            val = vtok.num if vtok.num is not None else float(vtok.value)
            events.append((t, val))
        self.expect("}")
        self.prog.stimuli.append(A.Stimulus(ch, events))

    # ---- loop ----
    def loop_decl(self):
        self.expect("loop")
        name = self.q(self.name())
        clock = self.expect_type("CLOCK").value
        self.expect("{")
        prior = sense = precision = conviction = None
        act = []
        mode = "deliberate"
        efference = None
        learn = 0.0
        overwhelm = 0.0
        overwhelm_auto = False
        while not self.at("}"):
            key = self.advance().value
            if key == "prior":
                self.opt(":"); prior = self.expr()
            elif key == "sense":
                self.opt(":"); sense = self.q(self.name())
            elif key == "precision":
                self.opt(":"); precision = self.prec_expr()
            elif key == "conviction":
                self.opt(":"); conviction = self.prec_expr()
            elif key == "mode":
                self.opt(":"); mode = self.advance().value
            elif key == "efference":
                self.opt(":"); efference = self.q(self.advance().value)
            elif key == "learn":
                self.opt(":"); learn = self._num()
            elif key == "overwhelm":
                self.opt(":")
                # `overwhelm: auto` derives the threshold from conviction vs the
                # trust in the evidence; `overwhelm: <n>` is an absolute debt bound.
                if self.cur.value == "auto":
                    self.advance(); overwhelm_auto = True
                else:
                    overwhelm = self._num()
            elif key == "act":
                act = self.act_block()
            else:
                raise ParseError(f"unknown loop field {key!r} at line {self.cur.line}")
        self.expect("}")
        if precision is None:
            precision = A.PrecConst(0.9)
        if conviction is None:
            conviction = A.PrecConst(0.5)
        self.prog.loops.append(A.Loop(name, clock, prior, sense, precision,
                                      conviction, act, mode=mode,
                                      efference=efference, learn=learn,
                                      overwhelm=overwhelm,
                                      overwhelm_auto=overwhelm_auto,
                                      owner=self.scope))

    def prec_expr(self):
        if self.at("ramp"):
            self.advance(); self.expect("(")
            start = self.advance().num
            self.expect("->")
            end = self.advance().num
            self.expect("over")
            clock = self.expect_type("CLOCK").value if self.at_type("CLOCK") else self.advance().value
            self.expect(")")
            return A.PrecRamp(start, end, clock)
        if self.at("schedule"):
            # schedule { clock => n ... } -> reduce to the last value (documented)
            self.advance(); self.expect("{")
            last = 0.9
            while not self.at("}"):
                self.advance()          # clock key
                self.expect("=>")
                last = self.advance().num
            self.expect("}")
            return A.PrecConst(last)
        # Anything else is an expression, re-read every moment in the loop's own
        # scope. This is what lets affect govern precision: a mood, a hormone, or
        # another person's certainty can now set how much the senses are trusted.
        e = self.expr()
        if isinstance(e, A.Num):
            return A.PrecConst(e.value)
        return A.PrecExpr(e)

    def act_block(self):
        self.expect("{")
        stmts = []
        while not self.at("}"):
            self.opt(";")
            if self.at("}"):
                break
            stmt = self.act_stmt()
            # a guard: `emit feel(delight) when her_face > 1`
            if self.at("when"):
                self.advance()
                stmt = A.Guard(self.expr(), stmt)
            stmts.append(stmt)
        self.expect("}")
        return stmts

    def act_stmt(self):
            kw = self.advance().value
            if kw == "update":
                self.expect("->")
                return A.Update(self.expr())
            if kw == "move":
                self.expect("!")
                return A.Move(self.call_expr())
            if kw == "ignore":
                return A.Ignore()
            if kw == "emit":
                self.expect("feel"); self.expect("(")
                q = self.advance().value
                self.expect(")")
                return A.Emit(A.Feel(q))
            if kw == "broadcast":
                content = self.expr()
                sal = None
                if self.opt("salience"):
                    self.opt(":"); sal = self.expr()
                return A.Broadcast(content, sal)
            if kw == "attend":
                target = self.advance().value
                cost = None
                if self.cur.value in ("spend",):
                    self.advance(); cost = self.expr()
                elif self.at_type("NUM") or self.at_type("DUR"):
                    cost = self.expr()
                return A.Attend(target, cost)
            raise ParseError(f"unknown act statement {kw!r} at line {self.cur.line}")

    # ---- mood ----
    def mood_decl(self):
        self.expect("mood")
        name = self.q(self.name())
        # optional ': Type'
        if self.opt(":"):
            self.advance()
        clock = self.expect_type("CLOCK").value if self.at_type("CLOCK") else "mood"
        self.expect("integrates"); self.expect("{")
        srcs = []
        while not self.at("}"):
            src = self.advance().value
            w = 1.0
            if self.opt("*"):
                # signed weights: a mood may be *relieved* by a quale, not only
                # fed by one.   integrates { dread * 1.0, calm * -0.6 }
                w = self._num()
            srcs.append((src, w))
        self.expect("}")
        decay = 0.98
        if self.opt("decay"):
            decay = self.advance().num
        self.prog.moods.append(A.Mood(name, clock, srcs, decay))

    # ---- narrator ----
    def narrator_decl(self):
        self.expect("narrator")
        name = self.q(self.name())
        self.expect("subscribes"); self.expect("{")
        subs = []
        while not self.at("}"):
            subs.append(self.q(self.advance().value))
            self.opt(",")
        self.expect("}")
        confab = True
        if self.opt("confabulates"):
            confab = self.advance().value == "true"
        voice = {}
        if self.opt("voice"):
            self.expect("{")
            while not self.at("}"):
                key = self.advance().value
                self.expect(":")
                line = self.expect_type("STR").value
                voice[key] = line
                self.opt(",")
            self.expect("}")
        self.prog.narrators.append(A.Narrator(name, subs, confab, voice,
                                              owner=self.scope))

    # ---- handler ----
    def handler_decl(self):
        self.expect("handle")
        name = self.expect_type("ID").value
        self.expect("with"); self.expect("{")
        h = A.Handler(name)
        while not self.at("}"):
            if self.at("when"):
                self.advance()
                h.when = self.expr()
                self.expect(":")
                h.on_crash = self._handler_stmts()
            elif self.at("after"):
                self.advance()
                tok = self.advance()
                h.after = tok.num if tok.num is not None else float(tok.value)
                self.opt(":")
                if self.at("repair"):
                    self.advance()
                    self.expect("{")
                    h.repair = self._handler_stmts()
                    self.expect("}")
                else:
                    h.repair = self._handler_stmts()
            else:
                raise ParseError(f"unknown handler clause {self.cur.value!r}")
        self.expect("}")
        self.prog.handlers.append(h)

    def _handler_stmts(self):
        stmts = []
        # a small set: dissociate(x) / reattach(x) [with precision -> titrate(n)]
        while self.cur.value in ("dissociate", "reattach"):
            kind = self.advance().value
            self.expect("(")
            scope = self.advance().value
            self.expect(")")
            titr = None
            if self.opt("with"):
                self.opt("precision"); self.opt("->")
                if self.opt("titrate"):
                    self.expect("(")
                    titr = self.advance().num
                    self.expect(")")
            stmts.append((kind, scope, titr))
        return stmts

    # ---- expressions ----
    def expr(self):
        return self.comparison()

    def comparison(self):
        left = self.addsub()
        while self.cur.value in ("<", ">", "<=", ">=", "==", "!="):
            op = self.advance().value
            right = self.addsub()
            left = A.Bin(op, left, right)
        return left

    def addsub(self):
        left = self.muldiv()
        while self.cur.value in ("+", "-"):
            op = self.advance().value
            left = A.Bin(op, left, self.muldiv())
        return left

    def muldiv(self):
        left = self.unary()
        while self.cur.value in ("*", "/"):
            op = self.advance().value
            left = A.Bin(op, left, self.unary())
        return left

    def unary(self):
        if self.at("-"):
            self.advance()
            return A.Bin("-", A.Num(0.0), self.unary())
        if self.at("+"):
            self.advance()
            return self.unary()
        return self.atom()

    def atom(self):
        t = self.cur
        if t.type in ("NUM", "DUR"):
            self.advance()
            return A.Num(t.num)
        if t.type == "STR":
            self.advance()
            return A.Str(t.value)
        if t.type == "VAR":
            self.advance()
            return A.Ref(t.value)          # ?x query variable
        if self.at("("):
            self.advance()
            e = self.expr()
            self.expect(")")
            return e
        if t.value == "predict":
            self.advance(); self.expect("(")
            args = self.arglist()
            self.expect(")")
            return A.Call("predict", args)
        if t.value == "feel" and self.peek_is("("):
            self.advance(); self.expect("(")
            q = self.advance().value
            self.expect(")")
            return A.Feel(q)
        # generic id -> maybe call
        if t.type in ("ID", "KW"):
            self.advance()
            if self.at("("):
                self.advance()
                args = self.arglist()
                self.expect(")")
                return A.Call(t.value, args)
            return A.Ref(t.value)
        raise ParseError(f"unexpected token {t.value!r} in expression at line {t.line}")

    def call_expr(self) -> A.Call:
        """Parse a move action: name(args...)."""
        name = self.advance().value
        args = []
        if self.opt("("):
            args = self.arglist()
            self.expect(")")
        return A.Call(name, args)

    def arglist(self):
        args = []
        if self.at(")"):
            return args
        args.append(self.expr())
        while self.opt(","):
            args.append(self.expr())
        return args

    # ---- 0.3 declarations ----
    def _num(self):
        sign = 1.0
        while self.at("-") or self.at("+"):
            if self.advance().value == "-":
                sign = -sign
        tok = self.advance()
        v = tok.num if tok.num is not None else float(tok.value)
        return sign * v

    def flow_decl(self):
        self.expect("flow")
        ch = self.q(self.name())
        clock = self.expect_type("CLOCK").value if self.at_type("CLOCK") else "cardiac"
        self.expect("{")
        dyn = None
        while not self.at("}"):
            key = self.advance().value
            self.opt(":")
            if key == "dynamics":
                dyn = self.expr()
        self.expect("}")
        self.prog.flows.append(A.Flow(ch, dyn, clock, owner=self.scope))

    def embodiment_decl(self):
        self.expect("embodiment")
        name = self.q(self.name())
        self.expect("{")
        pairs = []
        while not self.at("}"):
            self.expect("pair")
            pname = self.q(self.name())
            self.opt(":")
            self.expect("schema"); self.opt("=")
            sval = self._num()
            self.expect("image"); self.opt("=")
            ival = self._num()
            tol = 2.0
            if self.opt("tolerance"):
                self.opt("="); tol = self._num()
            pairs.append((pname, sval, ival, tol))
        self.expect("}")
        self.prog.embodiments.append(A.Embodiment(name, pairs))

    def memory_decl(self):
        self.expect("memory")
        register = self.advance().value      # episodic|semantic|procedural|somatic
        name = self.q(self.name())
        self.expect("{")
        cue = when = evoke = None
        strength = 1.0
        while not self.at("}"):
            key = self.advance().value
            self.opt(":")
            if key == "cue":
                cue = self.q(self.advance().value)
            elif key == "when":
                when = self.expr()
            elif key == "evoke":
                self.expect("feel"); self.expect("(")
                evoke = self.advance().value
                self.expect(")")
            elif key == "strength":
                strength = self._num()
        self.expect("}")
        self.prog.memories.append(A.Memory(register, name, cue, when, evoke,
                                          strength, owner=self.scope))

    def attention_decl(self):
        self.expect("attention")
        name = self.q(self.name())
        self.opt(":")
        if self.at_type("ID") and self.cur.value == "Spotlight":
            self.advance()          # optional type annotation
        self.expect("=")
        if self.opt("capacity"):
            self.opt("(")
        cap = self._num()
        self.opt(")")
        self.prog.attentions.append(A.Attention(name, cap))

    def workspace_decl(self):
        self.expect("workspace")
        name = self.expect_type("ID").value
        thr = 0.5
        self.expect("{")
        while not self.at("}"):
            key = self.advance().value
            self.opt(":")
            if key in ("ignite", "threshold"):
                if self.opt("at"):
                    pass
                thr = self._num()
        self.expect("}")
        self.prog.workspaces.append(A.Workspace(name, thr))

    def awareness_decl(self):
        self.expect("awareness")
        name = self.q(self.name())
        self.expect("tracks")
        tracks = self.q(self.advance().value)
        tau = 0.1
        if self.opt("with"):
            self.opt("tolerance"); tau = self._num()
        self.prog.awarenesses.append(A.Awareness(name, tracks, tau))

    def allostat_decl(self):
        self.expect("allostat")
        name = self.q(self.name())
        self.expect("{")
        regulate = None; setpoint = 0.0; gain = 0.5; resource = None
        while not self.at("}"):
            key = self.advance().value
            self.opt(":")
            if key == "regulate":
                regulate = self.q(self.advance().value)
            elif key == "setpoint":
                setpoint = self._num()
            elif key == "gain":
                gain = self._num()
            elif key == "spend":
                resource = self.q(self.advance().value)
        self.expect("}")
        self.prog.allostats.append(A.Allostat(name, regulate, setpoint, gain,
                                              resource, owner=self.scope))

    def intervene_decl(self):
        self.expect("intervene")
        kind = self.advance().value          # rebus
        self.expect("{")
        at = 0.0; strength = 0.5
        while not self.at("}"):
            key = self.advance().value
            self.opt(":")
            if key == "at":
                at = self._num()
            elif key == "strength":
                strength = self._num()
        self.expect("}")
        self.prog.interventions.append(A.Intervene(kind, at, strength))

    def ownership_decl(self):
        self.expect("ownership")
        name = self.q(self.name())
        self.expect("{")
        predicted = observed = None; tol = 2.0; initial = True
        while not self.at("}"):
            key = self.advance().value
            self.opt(":")
            if key == "predicted":
                predicted = self.q(self.advance().value)
            elif key == "observed":
                observed = self.q(self.advance().value)
            elif key == "tolerance":
                tol = self._num()
            elif key == "initial":
                # `initial: alien` -- a rubber hand is not yours until the
                # stroking synchronizes it. Default `owned`.
                initial = self.advance().value not in ("alien", "disowned", "false")
        self.expect("}")
        self.prog.ownerships.append(A.Ownership(name, predicted, observed, tol, initial))

    def query_decl(self):
        self.expect("query")
        name = self.expect_type("STR").value if self.at_type("STR") else self.advance().value
        self.expect("{")
        preds, wheres, surface = [], [], ""
        while not self.at("}"):
            if self.at("where"):
                self.advance()
                wheres.append(self.expr())
            elif self.at("surface"):
                self.advance()
                surface = self.expect_type("STR").value
            elif self.at("find"):
                self.advance()            # optional 'find' lead-in
            else:
                rel = self.advance().value
                terms = []
                while self.at_type("VAR") or self.at_type("STR") or \
                        self.at_type("NUM") or self.at_type("DUR") or \
                        (self.at_type("ID") and not self.at("where")):
                    tk = self.advance()
                    if tk.type == "VAR":
                        terms.append(("var", tk.value))
                    elif tk.type in ("NUM", "DUR"):
                        terms.append(("num", tk.num))
                    else:
                        terms.append(("lit", tk.value))
                preds.append(A.QueryPred(rel, terms))
        self.expect("}")
        self.prog.queries.append(A.Query(name, preds, wheres, surface))


def parse(src: str, title: str = "untitled") -> A.Program:
    return Parser(tokenize(src), title=title).parse()
