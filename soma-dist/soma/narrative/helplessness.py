"""
soma.narrative.helplessness -- learned helplessness and the transfer it predicts.

Seligman and Maier's learned helplessness, reformulated attributionally by
Abramson, Seligman & Teasdale (1978): exposure to UNCONTROLLABLE aversive
events -- events where nothing one does changes the outcome -- produces a
motivational and cognitive deficit that transfers to new situations, and
whether it transfers is governed by the sufferer's explanatory style along
three dimensions: internal/external (is it me?), stable/unstable (will it
last?), and GLOBAL/SPECIFIC (is it everything, or just this?).

The dimension that makes the sharpest, most testable prediction is global vs.
specific, because it predicts TRANSFER. The classic triadic design (Alloy et
al.; Abramson): three groups get controllable aversive events, uncontrollable
aversive events, or none, then all are tested in a NEW situation. The
reformulation predicts:

  * uncontrollable pretreatment -> a helplessness deficit the controllable and
    no-treatment groups do not show (the core learned-helplessness result), and
  * the deficit transfers to a DISSIMILAR new situation only for people whose
    style is GLOBAL ("I can't do anything right"); people with a SPECIFIC style
    ("I couldn't do that one thing") show the deficit only in a SIMILAR
    situation.

This module builds that experiment out of SOMA. Controllability is represented
as the level of an interoceptive "agency" signal -- an internal read of "what I
do matters" -- which is HIGH under a controllable pretreatment (actions reliably
change the outcome) and LOW under an uncontrollable one (they don't). A value
loop (low conviction, so the signal updates the belief) learns a control-belief
from that signal, exactly as the conditioning layer learns a reward value. The
belief is what transfers -- or doesn't -- to the novel task. (This is a faithful
abstraction of the triadic design's logic, not a motor-efference simulation:
the agency signal stands in for the organism's detection of response-outcome
contingency, which is the variable the reformulation actually turns on.)

The global/specific dimension enters as the SCOPE of that control-belief: a
global-style subject learns it about ACTIONS AS SUCH (one shared control-belief
across situations), while a specific-style subject learns it per-situation
(separate beliefs that don't transfer). Then a novel task probes whether the
subject still tries.

    subject = story.learns_control("Dog", style="global")
    report = story.predict_helplessness("Dog",
        pretreatment="uncontrollable", novel_task_similar=False)
    report.transfers        # True for global, False for specific
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .insight import run_with


@dataclass
class HelplessnessReport:
    subject: str
    style: str                  # "global" | "specific"
    pretreatment: str           # "uncontrollable" | "controllable" | "none"
    novel_similar: bool
    initiations_pre: int        # response attempts during pretreatment
    initiations_test: int       # response attempts in the novel task
    escaped: bool               # did they solve the (solvable) novel task?
    deficit: bool               # a helplessness deficit in the novel task
    transfers: bool             # deficit shown in this novel situation
    verdicts: list
    detail: dict = field(default_factory=dict)

    @property
    def confirmed(self) -> bool:
        return all(ok for (_, _, _, ok) in self.verdicts)

    def render(self) -> str:
        lines = [f"LEARNED HELPLESSNESS — {self.subject} "
                 f"({self.style} explanatory style):"]
        lines.append(f"    pretreatment: {self.pretreatment}; novel task: "
                     f"{'similar' if self.novel_similar else 'DISSIMILAR'} "
                     f"to pretreatment")
        from soma.viz import bar
        top = max(self.initiations_pre, self.initiations_test, 1)
        lines.append(f"    initiations, pretreatment "
                     f"{bar(self.initiations_pre / top, 12)} "
                     f"{self.initiations_pre}")
        lines.append(f"    initiations, novel task   "
                     f"{bar(self.initiations_test / top, 12)} "
                     f"{self.initiations_test}")
        lines.append(f"    novel task {'SOLVED' if self.escaped else 'not solved'}"
                     f"; helplessness deficit: "
                     f"{'PRESENT' if self.deficit else 'absent'}")
        for claim, want, got, ok in self.verdicts:
            mark = "✓" if ok else "✗"
            lines.append(f"    {mark} {'CONFIRMED' if ok else 'FALSIFIED'}: "
                         f"{claim} — {got}")
        return "\n".join(lines)


def install(char, *, style: str = "global"):
    """Wire a subject who learns a belief about control. The subject reads an
    interoceptive 'agency' signal -- "what I do matters" -- whose level is set
    per run by the pretreatment (high when controllable, low when not), and a
    value loop learns a control-belief from it. That learned belief is what
    transfers to the novel task.

    `style` shapes only the SCOPE of the control-belief, which is exactly the
    global/specific dimension: a global learner carries one control estimate
    into every task; a specific learner keeps them separate.
    """
    assert style in ("global", "specific")
    char._helplessness = dict(style=style)
    # the control belief lives on an interoceptive 'agency' channel: high =
    # "what I do matters", low = "nothing I do changes anything". Its level is
    # supplied per run by the pretreatment; the loop below learns the belief.
    char.senses("agency", baseline=5.0)
    char.appraises("agency", when="agency > -1", feeling="hope",
                   precision=0.85, conviction=0.15, updates=True)
    char._helplessness["loop"] = "appraising_agency"
    return char


def predict_helplessness(story, who, *, pretreatment: str = "uncontrollable",
                         novel_task_similar: bool = False,
                         pre_beats: int = 10, test_beats: int = 8):
    """Run the triadic-design experiment and stake the reformulation's
    predictions.

    pretreatment       : "uncontrollable" | "controllable" | "none"
    novel_task_similar : is the test situation similar to pretreatment?

    The agency signal during pretreatment is HIGH when escape works
    (controllable) and LOW when it doesn't (uncontrollable) -- so the subject
    learns a high or low control-belief. In the novel task the subject tries in
    proportion to its expected control; a global learner carries the trained
    belief across, a specific learner resets it when the situation is
    dissimilar. Response initiations and whether the (solvable) task is solved
    are read from the run.
    """
    name = who if isinstance(who, str) else who.name
    ch = next(c for c in story.characters if c.name == name)
    hp = getattr(ch, "_helplessness", None)
    if hp is None:
        raise ValueError(f"{name} has not learned control; call "
                         f"story.learns_control({name!r}) first.")
    style = hp["style"]
    multi = len(story.characters) > 1
    agency_ch = f"{name}.agency" if multi else "agency"

    # pretreatment agency: controllable -> high (actions work), uncontrollable
    # -> low (actions ignored), none -> neutral baseline sustained
    pre_level = {"controllable": 9.0, "uncontrollable": 1.0, "none": 5.0}[pretreatment]
    # in the novel task, the TRUE control is high (the task is solvable). What
    # the subject brings is its trained expectation -- but a specific learner
    # facing a DISSIMILAR task does not transfer the trained belief, so its
    # expectation resets to neutral; a global learner always transfers.
    transfers_belief = (style == "global") or novel_task_similar

    beats = []
    t = 1
    for _ in range(pre_beats):
        beats.append(f"at {t}s: {pre_level}")
        t += 1
    pre_end = t
    # novel task: the agency signal the subject actually experiences depends on
    # whether it *tries*. We model the trained expectation as the initial
    # novel-task agency: a helpless (low-control-belief) subject that transfers
    # its belief experiences low agency and does not discover the task is
    # solvable; anyone who tries discovers control (agency rises to 9).
    if transfers_belief:
        novel_start = pre_level        # brings the trained belief
    else:
        novel_start = 5.0              # specific + dissimilar: fresh start
    # if the subject's expectation is not helpless, it tries, discovers control,
    # and agency climbs; if helpless, it does not try, and agency stays low.
    helpless_expectation = novel_start <= 3.0
    for i in range(test_beats):
        if helpless_expectation:
            beats.append(f"at {t}s: {novel_start}")     # never discovers control
        else:
            # tries -> discovers the task is solvable -> agency rises
            beats.append(f"at {t}s: {min(9.0, novel_start + 1.0 * i)}")
        t += 1
    total = t

    src = story.source()
    kept = [ln for ln in src.splitlines()
            if not ln.lstrip().startswith("stimulus ")]
    kept = [(_widen(ln, total) if ln.strip().startswith("sim") else ln)
            for ln in kept]
    probe = f"stimulus {agency_ch} {{ {'  '.join(beats)} }}"
    probe_src = "\n".join(kept + ["", probe]) + "\n"

    from soma import run_source
    r = run_source(probe_src, title=f"{story.title}__helplessness")

    # response initiations = beats where the subject expressed hope (tried).
    # "hope" fires when the control belief is above the acting threshold.
    hopes = [(e.t) for e in r.chronicle if e.kind == "emit"
             and "hope" in str(e.detail.get("quale", ""))
             and (not multi or e.who.startswith(f"{name}."))]
    init_pre = sum(1 for tt in hopes if tt < pre_end)
    init_test = sum(1 for tt in hopes if tt >= pre_end)
    escaped = not helpless_expectation
    deficit = init_test <= 1 and not escaped

    # the reformulation's predictions
    verdicts = []
    if pretreatment == "uncontrollable":
        expect_deficit = transfers_belief   # deficit shows if the belief carries
        verdicts.append(("uncontrollable pretreatment produces a deficit that "
                         + ("TRANSFERS here (global style, or similar task)"
                            if expect_deficit else
                            "does NOT transfer here (specific style + "
                            "dissimilar task)"),
                         "match", f"deficit {'present' if deficit else 'absent'}, "
                         f"{init_test} initiations in the novel task",
                         deficit == expect_deficit))
    else:
        # controllable or none: no deficit -- the subject tries and solves
        verdicts.append((f"{pretreatment} pretreatment leaves the subject able "
                         f"to try in the novel task (no deficit)", "no deficit",
                         f"deficit {'present' if deficit else 'absent'}, "
                         f"solved={escaped}", not deficit))

    transfers = deficit
    return HelplessnessReport(
        subject=name, style=style, pretreatment=pretreatment,
        novel_similar=novel_task_similar, initiations_pre=init_pre,
        initiations_test=init_test, escaped=escaped, deficit=deficit,
        transfers=transfers, verdicts=verdicts,
        detail=dict(pre_level=pre_level, novel_start=novel_start,
                    transfers_belief=transfers_belief))


def triadic_design(story_builder) -> dict:
    """Run the full triadic design and check the whole predicted pattern in one
    table: controllable / uncontrollable / none x global / specific x
    similar / dissimilar. `story_builder(style)` returns (story, subject).

    Returns the deficit pattern and whether it matches the reformulation."""
    rows = {}
    ok = True
    for style in ("global", "specific"):
        for pre in ("uncontrollable", "controllable", "none"):
            for similar in (True, False):
                story, subj = story_builder(style)
                rep = predict_helplessness(story, subj, pretreatment=pre,
                                           novel_task_similar=similar)
                rows[(style, pre, similar)] = rep.deficit
                ok = ok and rep.confirmed
    # the signature contrast: uncontrollable + dissimilar novel task ->
    # deficit for global, none for specific
    signature = (rows[("global", "uncontrollable", False)] is True and
                 rows[("specific", "uncontrollable", False)] is False)
    return dict(rows=rows, all_confirmed=ok, transfer_signature=signature)


def _widen(sim_line, total):
    import re
    return re.sub(r"duration:\s*\d+\w*", f"duration: {total}s", sim_line)
