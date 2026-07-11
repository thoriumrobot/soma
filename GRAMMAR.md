# SOMA 0.14.2 — Grammar Reference

The canonical surface syntax is ASCII. The spec's Unicode forms are accepted as
aliases: `◜`→`{`, `◞`→`}`, `⤋`→`->`, `⤊`→`^`.

Whitespace and newlines are insignificant; `;` is accepted and ignored.
Comments run to end of line after `//` or `#`.

```ebnf
program      ::= { decl } ;

decl         ::= consent | sim | let | body | resource | stimulus | flow
               | loop | mood | narrator | handler | embodiment | memory
               | attention | workspace | awareness | allostat | intervene
               | ownership | query | character | couple | scene ;

(* ---------- 0.4: more than one person in the room ---------- *)

(* Everything declared inside a character is qualified with their name:
   inside `character Ana`, `heart` means `Ana.heart`. A name written with a dot
   (`Ivo.face`) is cross-character and is left exactly as written. *)
character    ::= "character" name "{" { decl } "}" ;   (* may not nest *)

(* One body's surface becomes another's sensation, attenuated and late.
   This is the ONLY channel between two minds. *)
couple       ::= "couple" name "->" name
                 [ "{" { "gain" number | "lag" duration } "}" ] ;

(* A named window of the Chronicle. Changes no physics; gives the trace beats. *)
scene        ::= "scene" string "from" duration "to" duration ;

(* ---------- ethics gate ---------- *)
consent      ::= "@consent" "(" string { "," string } ")" ;

(* ---------- the multi-clock ---------- *)
sim          ::= "sim" "{" { sim_field } "}" ;
sim_field    ::= "duration" [":"] duration
               | "dt"       [":"] duration
               | "cadence"  [":"] bool ;       (* each loop ticks at its clock *)

clock        ::= "@" ("neural"|"cardiac"|"breath"|"mood"
                     |"hormonal"|"circadian"|"biography"|"lineage") ;

(* ---------- bindings ---------- *)
let          ::= "let" name "=" expr ;

(* ---------- the body ---------- *)
body         ::= "body" name clock "{" { channel } "}" ;
channel      ::= modality name ":" type { chan_opt } ;
modality     ::= "intero" | "extero" | "proprio" ;
chan_opt     ::= "baseline"   number
               | "retention"  duration
               | "protention" duration
               | "efference"  name        (* the loop whose action self-causes *)
               | "gain"       number ;    (* reafference subtraction gain *)

(* affine: movable, splittable, never copied, never conjured *)
resource     ::= "resource" name ":" [ "Affine" "<" name ">" ] "="
                 ( name "(" number ")" | number ) ;

(* the affine spotlight: spent within a moment, recovers across them *)
attention    ::= "attention" name [":" "Spotlight"] "=" [ "capacity" ] "(" number ")" ;

stimulus     ::= "stimulus" name "{" { "at" duration ":" number } "}" ;

(* continuous physiology, integrated by Heun's method *)
flow         ::= "flow" name [ clock ] "{" "dynamics" [":"] expr "}" ;

(* predictive (allostatic) regulation: spends budget ahead of demand *)
allostat     ::= "allostat" name "{" { allo_field } "}" ;
allo_field   ::= "regulate" [":"] name | "setpoint" [":"] number
               | "gain" [":"] number    | "spend"    [":"] name ;

(* ---------- the loop: SOMA's primitive ---------- *)
loop         ::= "loop" name clock "{" { loop_field } "}" ;
loop_field   ::= "prior"      [":"] expr
               | "sense"      [":"] name
               | "precision"  [":"] prec      (* pi_s : trust in the senses *)
               | "conviction" [":"] prec      (* pi_p : trust in the prior  *)
               | "mode"       [":"] ("habit" | "deliberate")
               | "efference"  [":"] name      (* cancel this loop's reafference *)
               | "learn"      [":"] number    (* each firing hardens the prior *)
               | "overwhelm"  [":"] (number | "auto")
                                              (* a defended belief's breaking point:
                                                 suppressed disconfirming surprise
                                                 accumulates until it forces perceive
                                                 -- the self-revelation. `auto`
                                                 derives the threshold from
                                                 conviction / trust-in-evidence *)
               | "act" act_block ;

prec         ::= number
               | "ramp" "(" number "->" number "over" clock ")"
               | "schedule" "{" { clock "=>" number } "}"
               | expr ;      (* dynamic: re-evaluated each moment in the loop's
                                own scope, clamped >= 0. A Qualia here is a
                                static error. This is how affect governs the
                                gain on the senses. *)

act_block    ::= "{" { guarded } "}" ;
guarded      ::= act_stmt [ "when" expr ] ;    (* an act that only sometimes happens *)
act_stmt     ::= "update" "->" expr            (* perceptual inference *)
               | "move" "!" call               (* active inference *)
               | "ignore"                      (* suppress, iff prior outranks *)
               | "emit" "feel" "(" name ")"    (* the only legal home of feel() *)
               | "broadcast" expr [ "salience" [":"] expr ]
               | "attend" name [ [ "spend" ] expr ] ;

(* built-in move actions: spend(res, n), set(chan, n); anything else is a
   labelled decision the narrator will have to explain. *)

(* ---------- affect, memory, self ---------- *)
mood         ::= "mood" name [":" type] clock
                 "integrates" "{" { name [ "*" signed ] } "}"
                 [ "decay" number ] ;
signed       ::= [ "-" | "+" ] number ;   (* a negative weight lets a quale
                                             relieve a mood, not only feed it *)

memory       ::= "memory" register name "{" { mem_field } "}" ;
register     ::= "episodic" | "semantic" | "procedural" | "somatic" ;
mem_field    ::= "cue" [":"] name | "when" [":"] expr
               | "evoke" [":"] "feel" "(" name ")" | "strength" [":"] number ;

narrator     ::= "narrator" name "subscribes" "{" { name [","] } "}"
                 [ "confabulates" bool ]
                 [ "voice" "{" { name ":" string [","] } "}" ] ;

(* ---------- global workspace & the attention schema ---------- *)
workspace    ::= "workspace" name "{" ("ignite"|"threshold") [ "at" ] number "}" ;
awareness    ::= "awareness" name "tracks" name [ "with" "tolerance" number ] ;
(* `introspect(<awareness>)` is a STATIC ERROR: the schema is transparent. *)

(* ---------- the seams of embodiment ---------- *)
embodiment   ::= "embodiment" name "{" { pair } "}" ;
pair         ::= "pair" name [":"] "schema" ["="] number
                                  "image"  ["="] number
                                  [ "tolerance" ["="] number ] ;
(* declares channels <pair>_schema and <pair>_image; divergence past tolerance
   emits a `conflict` event -- phantom limb, anorexia, depersonalization. *)

ownership    ::= "ownership" name "{" { own_field } "}" ;
own_field    ::= "predicted" [":"] name | "observed" [":"] name
               | "tolerance" [":"] number ;

(* ---------- crash & repair ---------- *)
handler      ::= "handle" name "with" "{" { handler_clause } "}" ;
handler_clause ::= "when" hcond ":" { hstmt }
                 | "after" duration [":"] [ "repair" "{" { hstmt } "}" | { hstmt } ] ;
hcond        ::= expr ;    (* may reference `error` (the frame's worst) or
                              `error(loop)` (one loop's error), so each
                              supervision band watches its own subsystem *)
hstmt        ::= ("dissociate" | "reattach") "(" scope ")"
                 [ "with" [ "precision" ] [ "->" ] "titrate" "(" number ")" ] ;
scope        ::= "interoception" | "proprioception" | "exteroception" | "self"
               | name ;    (* a modality band, or any author-named scope.
                              Crash and repair form a cycle: a band that
                              reattaches can detach again if pressed again. *)

(* ---------- global perturbation ---------- *)
intervene    ::= "intervene" "rebus" "{" "at" [":"] duration
                                          "strength" [":"] number "}" ;

(* ---------- Winnow-S: the novelist's query language ---------- *)
query        ::= "query" ( string | name ) "{" { q_clause } "}" ;
q_clause     ::= [ "find" ] relation { qterm }
               | "where" expr
               | "surface" string ;
relation     ::= "feel" | "somatic" | "act" | "drive" | "spend" | "narrate"
               | "crash" | "repair" | "conflict" | "ignite" | "ignore"
               | "own" | "spike" ;
qterm        ::= qvar | string | number ;
qvar         ::= "?" name ;

(* ---------- expressions ---------- *)
expr         ::= comparison ;
comparison   ::= addsub { ("<"|">"|"<="|">="|"=="|"!=") addsub } ;
addsub       ::= muldiv { ("+"|"-") muldiv } ;
muldiv       ::= unary { ("*"|"/") unary } ;
unary        ::= ("-"|"+") unary | atom ;
atom         ::= number | duration | string | qvar
               | "(" expr ")"
               | "predict" "(" expr ")"
               | "feel" "(" name ")"
               | "belief" "(" name ")"    (* what a loop currently expects *)
               | "acting" | "perceiving"  (* this loop's arbitration outcome *)
               | name [ "(" [ expr { "," expr } ] ")" ] ;

(* ---------- builtins callable in any expression ---------- *)
(* general:  sigmoid tanh exp log sqrt abs min max clamp                     *)
(* temporal: ret(chan, n)   pro(chan)      -- retention / protention         *)
(* ported from the ilion stdlib:                                            *)
(*   intero_precision(arousal, noise)                                        *)
(*   exafference(afferent, efference_copy, gain)                             *)
(*   ignition_index(a, b, c, d)                                              *)
(*   attention_strength(salience, competing, beta)                           *)
(*   epistemic_value(sigma_prior, sigma_post)                                *)
(*   pragmatic_value(pred, pref, sigma)                                      *)
(*   policy_prob(G_a, G_b, gamma)                                            *)

(* ---------- lexical ---------- *)
duration     ::= number ("ms"|"s"|"m"|"h"|"d"|"y") ;
bool         ::= "true" | "false" ;
name         ::= letter { letter | digit | "_" } ;   (* soft keywords allowed *)
```

## Soft keywords

Keywords are reserved only where they are structurally positioned. A name in a
binding position may shadow one: `attention spotlight = capacity(6)` and
`let tolerance = 6` both parse. Only `body` used as a *loop name* would collide,
because `loop` fields are keyword-led.

## Static rules (the ones the compiler enforces)

| rule | violation |
|---|---|
| **Qualia opacity** | `feel(x)` anywhere but as the whole argument of `emit` |
| **Transparency** | `introspect(<awareness>)` — the attention schema cannot see itself |
| **Consent gating** | `emit feel(<distress>)`, distress-evoking `memory`, `dissociate`, or `intervene rebus` without `@consent(...)` |
| **Affine resources** | re-binding a `resource` with `let` |
| **Register discipline** | `memory <register>` outside {episodic, semantic, procedural, somatic} |
| **Dual-process** | `mode` outside {habit, deliberate} |
| **Name resolution** | `awareness … tracks` an undeclared attention; `ownership` or `memory` referencing an undeclared channel |
| **Sense resolution** | a loop whose `sense:` names a channel that is not declared, stimulus-targeted, or coupled (a typo that would leave the loop silently inert) |
| **Clock names** | a `loop`, `body`, `flow`, or `mood` on a clock outside the eight (`neural`, `cardiac`, `breath`, `mood`, `hormonal`, `circadian`, `biography`, `lineage`) — almost always a typo like `@carfiac` |
| **Other minds** | a loop owned by Bob that `sense`s an `intero` channel of Alice's |
| **Other minds** | a `couple` whose source is an `intero` channel of another character |
| **Precision opacity** | a `Qualia` (`feel(x)`) used inside a dynamic `precision:` expression |

## The other-minds rule

No character may read another's interior. A loop belonging to Bob may sense
Bob's own channels, or an **exteroceptive** channel of Alice's — a face, a
voice, a hand — but never her interoception. Other minds are reached only
through surfaces, and only via `couple`, which imposes gain and lag.

```soma
character Ana { body b @cardiac { intero gut : T baseline 1
                                  proprio face : Affect baseline 5 } }
character Ivo { body b @cardiac { extero her_face : Affect baseline 5 } }

couple Ana.face -> Ivo.her_face { gain 0.9  lag 1s }   // legal
couple Ana.gut  -> Ivo.her_face { gain 1.0 }           // static error
```

This is the formal content of Sartre's look and Levinas's face: the other is
given to me as an exterior I must interpret, never as an interior I can read.
Every misunderstanding in `the_look.soma` follows from this one rule.
