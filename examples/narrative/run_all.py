"""
run_all.py -- reproduce every output block in TUTORIAL.md.

For each worked simulation, prints the dashboard, the sift findings, and (where
it applies) the synthesized character portrait. This is the script behind the
tutorial's claim that every block of output was generated, not hand-written.

    python examples/narrative/run_all.py            # everything
    python examples/narrative/run_all.py bad_news   # just one
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

EXAMPLES = ["bad_news", "the_look", "a_marriage", "the_house",
            "the_diplomat", "two_sisters", "the_negotiator", "the_unmooring"]


def show(name):
    mod = __import__(name)
    # a module may expose several named studies (BUILDS) instead of one build()
    builds = getattr(mod, "BUILDS", None)
    if builds:
        for key, fn in builds.items():
            _show_one(f"{name}:{key}", fn())
    else:
        _show_one(name, mod.build())


def _show_one(name, story):
    bar = "=" * 72
    print(f"\n{bar}\n  {name}\n{bar}\n")
    print(story.run(width=78))
    print("\n--- findings ---")
    for f in story.sift():
        print(f"  [{f.pattern}] {f.text}")
    # a portrait is meaningful once a character has an interior worth reading
    portrait = story.characterize(width=78)
    if "Torn:" in portrait or "Holds:" in portrait or "Carries" in portrait:
        print("\n--- portrait ---")
        print(portrait)


if __name__ == "__main__":
    wanted = [a for a in sys.argv[1:] if not a.startswith("-")]
    for name in (wanted or EXAMPLES):
        show(name)
