# certreach

Certificates for reachability in packet-labelled directed graphs: small, independently checkable witnesses for "reachable" and "unreachable" answers, plus algorithms to keep those witnesses valid as configurations change.

**Status: research prototype, started October 2026.** The Python reference implementation is tested but not formally verified. A staged Lean 4 formalization of the checkers is planned (see Roadmap).

## The idea

Network and access-policy configurations can be modelled as directed graphs whose edges carry labels, the sets of packets (or request classes) they admit. A packet reaches the target if one packet is admitted by every edge of some source-target path. Instead of trusting an analyzer's yes/no answer, ask for a certificate that a short checker can validate:

- **Reachable:** a path and a packet admitted by every edge on it.
- **Unreachable:** a list of cuts. Each cut is a vertex set containing the source but not the target, such that every edge leaving it has a label disjoint from the cut's group of packets. The groups together cover the queried packets.

One subtlety drives the design: for a *set* of packets, a single cut does not always exist (one edge may admit only port 22 and the next only port 80). The minimum number of cuts needed for a query is an optimization problem studied in this project.

## Quick start

Requires Python 3.9 or later. There are no dependencies.

```bash
cd src
python tutorial_example.py      # worked example, see docs/tutorial.md
python exhaustive_tests.py quick
python maintain_tests.py quick
```

## Repository layout

| File | Purpose |
| --- | --- |
| `src/certreach.py` | Definitions, checkers, certificate generators, and certificate-size analysis |
| `src/maintain.py` | Insertion-only maintenance of cut certificates, with work counters |
| `src/exhaustive_tests.py` | Exhaustive and randomized tests of soundness, completeness, certificate size, and local rechecking |
| `src/maintain_tests.py` | Correctness and cost tests for the maintenance algorithm |
| `src/prop3_check.py` | Brute-force check of the single-cut characterization |
| `src/hypergraph_check.py` | Check of the link between minimum certificates and hypergraph coloring |
| `src/hardness_check.py`, `src/hardness_check2.py` | Consistency checks (not proofs) of the construction behind the planned hardness reduction from 2-coloring 3-uniform hypergraphs; the second script includes non-2-colorable cases such as the Fano plane |
| `src/llm_experiment.py` | Pilot: untrusted solvers (LLM-written and bug-injected) checked by the certificate checker |
| `src/tutorial_example.py` | The worked example used in the tutorial |
| `results/` | Recorded outputs of the longer runs (`hardness_results.txt` holds the output of the two hardness checks) |
| `docs/tutorial.md` | Step-by-step tutorial |
| `lean/` | Draft Lean 4 formalization of the definitions and soundness theorems (not yet compiled), with setup instructions |

## Pilot results (small random graphs, pure Python)

- **Soundness:** across 450,000 runs of 15 solver configurations, about 19,000 runs gave a wrong answer; the checker rejected all of them and accepted none.
- **Exhaustive checks:** soundness and completeness hold on every labelled graph with 3 nodes and up to 3 packets, and on random larger instances.
- **Maintenance:** the insertion-only algorithm matched a from-scratch recomputation and passed the checker after every insertion (1.5 million checks), with total work about 0.5 times m(n + M + I).

See `results/` for the raw outputs. These are small, synthetic experiments. The pilot was developed with LLM assistance (Claude Sonnet 5.5, high effort), so it is a consistency check, not an independent evaluation.

## Limitations

- The model is deliberately simple (finite packet sets on directed edges). Real networks involve address translation, stateful rules, and routing; extending the model is future work.
- The checker is validated by testing, not by a machine-checked proof.
- Maintenance is implemented for label insertions only. Deletions and mixed streams are open.

## Roadmap

1. Complete and independently check the paper proofs, including the hardness reduction for the minimum-certificate problem, which is so far supported only by the consistency checks above.
2. Formalize the definitions and soundness theorem in Lean 4, in stages (a first draft is in `lean/`), then an executable verified checker.
3. Repair algorithms for deletions and mixed streams, with amortized bounds in chosen graph classes.
4. Scaled benchmark on synthetic fat-tree and public topologies.

## Contributing

Issues and pull requests are welcome. Please run the quick tests before submitting changes. See `CONTRIBUTING.md`.

## License

The code (`src/` and `lean/`) is under the MIT License; see `LICENSE`. The tutorial (`docs/`) and the recorded outputs (`results/`) are under CC BY 4.0; see `LICENSE-DATA`.

## Acknowledgements

Parts of the code and documentation were drafted with assistance from Claude (Anthropic; Claude Sonnet 5.5, high effort) and reviewed by the maintainer.
