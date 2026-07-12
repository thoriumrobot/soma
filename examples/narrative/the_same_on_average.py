"""
the_same_on_average.py -- three studies in telling people apart.

Three characters-studies, one theme: the ways two people can be identical by
every average and still be different people -- and how the 0.15
characterization layers make each difference a measured, falsifiable claim.

  1. THE SIGNATURE (CAPS; Mischel & Shoda 1995). Ren and Sol suppress exactly
     as often, feel exactly as often. But Ren defends against judgment and
     takes in warmth; Sol takes in judgment and defends against warmth. Their
     if...then profiles are near-inverses, and `diagnostic_situation` names the
     scene an author should stage to make the difference visible.

  2. THE GUIDES (self-discrepancy; Higgins 1987). Nora and Theo suffer the same
     failure. Nora holds an ideal (who she longs to be); Theo holds an ought
     (who he is obliged to be). The library predicts -- with no emotion term in
     the spec -- that the same shortfall DEJECTS her and AGITATES him, and the
     probe confirms both qualia in the Chronicle.

  3. THE WIDTH (Whole Trait Theory; Fleeson 2001). Wren and Moss are both
     'anxious about the news'. Moss hums at the same pitch whatever comes; Wren
     is serene until the news is strong and then her heart is a hammer. The
     density distribution says which is which: the width is itself a trait, and
     the reactivity is what the width is made of.

Run:  python3 examples/narrative/the_same_on_average.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from soma.narrative import Story, anxious, stoic, guarded
from soma.narrative.signature import (signature, similarity,
                                      diagnostic_situation)
from soma.narrative import selfguides
from soma.narrative.density import density, compare as compare_density


def study_signatures():
    print("=" * 72)
    print("1. THE SIGNATURE -- trait-identical, profile-different")
    print("=" * 72)
    story = Story("wediko", span="8s", step="1s", about="acute distress")
    ren = story.character("Ren", temperament=guarded)
    ren.senses("judgment"); ren.senses("warmth")
    ren.appraises("judgment", as_threat=True, feeling="fear",
                  precision=0.3, conviction=0.9)
    ren.appraises("warmth", feeling="comfort",
                  precision=0.9, conviction=0.2, updates=True)
    sol = story.character("Sol", temperament=guarded)
    sol.senses("judgment"); sol.senses("warmth")
    sol.appraises("judgment", feeling="fear",
                  precision=0.9, conviction=0.2, updates=True)
    sol.appraises("warmth", as_threat=True, feeling="wariness",
                  precision=0.3, conviction=0.9)

    battery = {"a judging eye": {"judgment": 8},
               "an open warmth": {"warmth": 8}}
    sr, ss = signature(story, ren, battery), signature(story, sol, battery)
    print(sr.render(), "\n")
    print(ss.render(), "\n")
    print(f"profile similarity: {similarity(sr, ss):.2f} "
          f"(mean levels equal: {sr.mean_level() == ss.mean_level()})")
    d = diagnostic_situation(story, ren, sol, battery)
    print(f"the diagnostic situation -- stage this to tell them apart: "
          f"'{d['situation']}' (separation {d['separation']})\n")


def study_selfguides():
    print("=" * 72)
    print("2. THE GUIDES -- the same failure, two different sufferings")
    print("=" * 72)
    story = Story("guides", span="8s", step="1s", about="acute distress")
    nora = story.character("Nora", temperament=anxious)
    theo = story.character("Theo", temperament=anxious)
    pi = selfguides.ideal(nora, "her_craft", standard=9.0)
    po = selfguides.ought(theo, "providing", standard=9.0)
    print(pi.gloss())
    print(po.gloss())
    out = selfguides.contrast(story, nora, theo, severity=4.0)
    for who, v in out.items():
        mark = "CONFIRMED" if v["confirmed"] else "FALSIFIED"
        print(f"  {who}: predicted {v['predicted_family']} "
              f"('{v['predicted_quale']}'), felt {v['felt']} -- {mark}")
    print()


def study_density():
    print("=" * 72)
    print("3. THE WIDTH -- the distribution is the person")
    print("=" * 72)
    story = Story("widths", span="8s", step="1s", about="acute distress")
    wren = story.character("Wren", temperament=anxious)
    wren.senses("news")
    wren.appraises("news", as_threat=True, drives="heart", to=118,
                   when="news > 6", fades_to=70)
    moss = story.character("Moss", temperament=stoic)
    moss.senses("news")
    moss.appraises("news", as_threat=True, drives="heart", to=94,
                   fades_to=70)
    dw = density(story, wren, "news", samples=16, seed=3)
    dm = density(story, moss, "news", samples=16, seed=3)
    print(dw.render(), "\n")
    print(dm.render(), "\n")
    cmp = compare_density(dw, dm)
    print(f"the wider life: {cmp['wider']}  "
          f"(sd {cmp['sd'][0]} vs {cmp['sd'][1]}; "
          f"reactivity {cmp['reactivity'][0]} vs {cmp['reactivity'][1]})")


if __name__ == "__main__":
    study_signatures()
    study_selfguides()
    study_density()
