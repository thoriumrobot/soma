# Tutorial examples

These three tiny programs are used in `TUTORIAL.md` (in the project root) to
teach the basics. Run them from the project root:

```bash
python -m soma check tutorial/01_hello.soma
python -m soma run   tutorial/01_hello.soma --no-color
python -m soma trace tutorial/02_arbitration.soma --no-color --kinds settle
python -m soma check tutorial/03_opaque.soma        # designed to FAIL, on purpose
```

- **01_hello.soma** — a body, one loop, one stimulus: the smallest useful program.
- **02_arbitration.soma** — two loops differing only in conviction: perceive vs act.
- **03_opaque.soma** — an intentional type error, showing qualia opacity.

The seventeen full simulations are in `../examples/`.
