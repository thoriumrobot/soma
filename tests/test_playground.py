"""
Tests for the playground bridge (web_bridge): the workspace file API that lets
a user write SOMA files in one editor and use them through the library on the
same page, and the shipped predictive-characterization library examples
(0.15-0.22), each executed exactly as the browser would execute it.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import web_bridge as wb  # noqa: E402


SOMA_SRC = (
    "sim { duration: 3s dt: 1s }\n"
    "body B @cardiac { intero heart : BPM baseline 70 }\n"
    "stimulus heart { at 2s: 120 }\n"
    "loop l @cardiac { prior: predict(70) sense: heart precision: 0.9 "
    "conviction: 0.3 act { emit feel(surprise) } }\n")


# ---------------------------------------------------------------------------
# the workspace: save / list / read / delete, and safety
# ---------------------------------------------------------------------------

def test_workspace_roundtrip():
    r = json.loads(wb.ws_save("t_roundtrip.soma", SOMA_SRC))
    assert r["name"] == "t_roundtrip.soma" and r["size"] == len(SOMA_SRC)
    names = [f["name"] for f in json.loads(wb.ws_list())]
    assert "t_roundtrip.soma" in names
    rd = json.loads(wb.ws_read("t_roundtrip.soma"))
    assert rd["content"] == SOMA_SRC
    assert json.loads(wb.ws_delete("t_roundtrip.soma")).get("ok")
    names = [f["name"] for f in json.loads(wb.ws_list())]
    assert "t_roundtrip.soma" not in names


def test_workspace_contains_unsafe_names():
    """Path-carrying names are basenamed into the workspace (no traversal);
    hidden and empty names are rejected outright."""
    for tricky, landed in (("../evil.soma", "evil.soma"),
                           ("/etc/passwd", "passwd"),
                           ("a/b.soma", "b.soma")):
        r = json.loads(wb.ws_save(tricky, "x"))
        assert r.get("name") == landed and "/" not in r.get("name", "/")
        assert not os.path.exists(os.path.join(os.path.dirname(wb._workdir()),
                                               landed))   # never a level up
        wb.ws_delete(landed)
    for bad in (".hidden", ""):
        assert "error" in json.loads(wb.ws_save(bad, "x")), bad


def test_library_code_can_run_a_saved_soma_file():
    """The page's core loop: save a .soma file, then drive it from library
    Python via run_file -- and cwd is restored afterwards."""
    wb.ws_save("t_bridge.soma", SOMA_SRC)
    cwd = os.getcwd()
    out = wb.run_python(
        "r = run_file('t_bridge.soma')\n"
        "print('emits:', sum(1 for e in r.chronicle if e.kind == 'emit'))\n",
        width=80)
    assert "emits:" in out and "\u2717" not in out
    assert os.getcwd() == cwd
    wb.ws_delete("t_bridge.soma")


def test_library_code_can_write_files_the_rail_will_list():
    out = wb.run_python(
        "open('t_written.soma', 'w').write('sim { duration: 1s dt: 1s }')\n"
        "print(workspace())\n", width=80)
    assert "t_written.soma" in out
    names = [f["name"] for f in json.loads(wb.ws_list())]
    assert "t_written.soma" in names
    wb.ws_delete("t_written.soma")


# ---------------------------------------------------------------------------
# the shipped predictive-characterization examples run clean
# ---------------------------------------------------------------------------

def _payload_examples():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from examples.library._manifest import as_payload
    return {e["key"]: e["code"] for e in as_payload()}


@pytest.mark.parametrize("key", [
    "lib/pc_signature", "lib/pc_portrait", "lib/pc_network", "lib/pc_diary",
    "lib/pc_choice", "lib/pc_other_mind", "lib/pc_tell", "lib/pc_files",
])
def test_shipped_pc_example_runs_clean(key):
    code = _payload_examples()[key]
    out = wb.run_python(code, width=88)
    assert "\u2717" not in out, out[:400]
    assert out.strip(), "example printed nothing"


def test_pc_examples_state_their_key_results():
    ex = _payload_examples()
    out = wb.run_python(ex["lib/pc_signature"], width=88)
    assert "mean levels equal: True" in out       # the Wediko point
    out = wb.run_python(ex["lib/pc_portrait"], width=88)
    assert "GONE" in out                          # reappraisal bifurcation
    out = wb.run_python(ex["lib/pc_diary"], width=88)
    assert out.count("OK") >= 2                   # both hubs recovered
    out = wb.run_python(ex["lib/pc_network"], width=88)
    assert "holds itself down" in out             # true non-recovery, shown
    assert "releases only" in out                 # vs mere hysteresis
    out = wb.run_python(ex["lib/pc_files"], width=88)
    assert "unfelt" in out                        # the dial changed the ending
