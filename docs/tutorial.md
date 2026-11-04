# Tutorial: certificates for packet-labelled reachability

This tutorial walks through the model, the two kinds of certificate, the reason a set of packets can need several cuts, and the maintenance algorithm. All code runs from the `src/` directory with Python 3.9 or later and no dependencies. The complete example is in `src/tutorial_example.py`.

## 1. The model

A graph has nodes `0 .. n-1`. Every ordered pair `(u, v)` with `u != v` carries a **label**: the set of packets that edge admits. An empty label means the edge is absent. A packet `p` **reaches** `t` from `s` if some walk from `s` to `t` has `p` in every edge label.

A **query** is `(s, t, P)` with `P` a nonempty set of packets. It is *reachable* if some packet in `P` reaches `t`, and *unreachable* if none does.

In code, a graph is a dictionary from `(u, v)` to a `frozenset` of packets:

```python
labels = {
    (0, 1): frozenset({22, 80, 443}),
    (1, 2): frozenset({80, 443}),
    (2, 4): frozenset({443}),
    (1, 3): frozenset({22}),
    (3, 4): frozenset({5432}),
}
s, t = 0, 4
```

Here node 0 is the source, node 4 the target, and packets are port numbers.

## 2. A positive certificate

A positive certificate is a pair `(p, path)`: a packet in `P` and a path from `s` to `t` whose every edge admits `p`.

```python
from certreach import make_positive, check_positive

P = frozenset({443})
cert = make_positive(labels, s, t, P)         # (443, [0, 1, 2, 4])
print(check_positive(labels, s, t, P, cert))  # True
```

`make_positive` is an untrusted generator. `check_positive` is the small checker: it only confirms that the path starts at `s`, ends at `t`, and that `p` is in every edge label.

## 3. A negative certificate

For packet 22 there is no path to `t`. A negative certificate is a list of **cuts**. A cut for a group `G` of packets is a vertex set `S` that contains `s` but not `t`, such that every edge leaving `S` has a label disjoint from `G`.

```python
from certreach import make_negative_per_packet, check_negative

P = frozenset({22})
cuts = make_negative_per_packet(labels, s, P)  # [({22}, {0, 1, 3})]
print(check_negative(labels, s, t, P, cuts))   # True
```

Here `S = {0, 1, 3}`. The edges leaving it are `(1, 2)`, which admits ports 80 and 443, and `(3, 4)`, which admits port 5432. Neither admits port 22, so port 22 can never leave `S`.

## 4. Why one cut is not always enough

Consider two edges, the first admitting only port 22 and the second only port 80, and ask about the packet set `{22, 80}`:

```python
from certreach import check_cut, reach_set, min_cuts

labels2 = {(0, 1): frozenset({22}), (1, 2): frozenset({80})}
s2, t2, P2 = 0, 2, frozenset({22, 80})

union_cut = (P2, frozenset(reach_set(labels2, s2, P2)))
print(check_cut(labels2, s2, t2, *union_cut))   # False
print(min_cuts(labels2, s2, t2, P2))            # 2
```

Neither packet can get through both edges, so the query is unreachable. But each edge individually admits some packet in `P`, so a single set `S` cannot separate `s` from `t` for the whole group. Two cuts, one per packet, work. The minimum number of cuts for a query is studied as an optimization problem in this project.

## 5. Letting the checker catch bugs

The checker is meant to be the only trusted component. To see this, write a solver that returns an answer plus a certificate, and run it through the checker. A solver that treats the packet set as one union graph returns a wrong "reachable" answer on the example above, and no certificate it could produce would pass `check_positive`. See `src/llm_experiment.py` for fifteen solver variants and the harness that classifies each run.

## 6. Maintaining cuts as labels are inserted

`maintain.py` keeps, for each fixed group of packets, the set of nodes reachable from `s`, updating it as labels are inserted. Packets are bit positions here.

```python
from maintain import CutMaintainer

M = CutMaintainer(n=4, s=0, t=3, groups=[1 << 0, 1 << 1])
M.insert(0, 1, 0)   # packet 0 can go 0 -> 1
M.insert(1, 2, 1)   # packet 1 can go 1 -> 2, but is not reachable from s
M.insert(1, 2, 0)   # packet 0 can go 1 -> 2
M.insert(2, 3, 0)   # packet 0 reaches the target
print(M.dead)       # [True, False]
```

After the last insertion the group for packet 0 is *dead*: `t` entered its reachable set, so its cut is no longer valid. For a single-packet group, the parent pointers give a positive certificate: `M.parent[0]` leads back from `t` to `s`, giving the path `[0, 1, 2, 3]`. For a group with several packets, the group must be split, and bounding the cost of that is an open question.

## 7. Running the tests

```bash
cd src
python exhaustive_tests.py quick   # soundness, completeness, size, local rechecking
python maintain_tests.py quick     # maintenance correctness and cost
python hypergraph_check.py         # minimum cuts versus hypergraph coloring
```

Drop the `quick` argument to run the longer versions, which take a few minutes. Recorded outputs are in `results/`.
