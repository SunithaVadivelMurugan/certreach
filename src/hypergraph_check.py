"""
Single-label special case: every present edge carries exactly one packet ("color").
Claim: m*(P) with P = all packets equals the chromatic number of the hypergraph whose
vertices are the packets and whose edges are the label sets L(pi) of s-t paths pi
(a coloring is proper if no hyperedge is monochromatic).  Also: label cuts are exactly
the transversals of that hypergraph.
"""
import random
from itertools import product
from certreach import min_cuts, reach_set, reaches
from exhaustive_tests import simple_paths, edges_of

def chromatic(num_packets, hyperedges):
    """Min colors so that no hyperedge is monochromatic (None if impossible)."""
    if any(len(h) == 1 for h in hyperedges):
        return None
    for m in range(1, num_packets + 1):
        for col in product(range(m), repeat=num_packets):
            if all(len({col[p] for p in h}) > 1 for h in hyperedges):
                return m
    return None

def is_label_cut(n, labels, s, t, removed):
    kept = {e: lab for e, lab in labels.items() if lab and not (lab <= removed)}
    return t not in reach_set(kept, s, frozenset().union(*kept.values()) if kept else frozenset())

rng = random.Random(3)
checked = bad = 0
for n, k, trials in [(4, 3, 4000), (5, 4, 4000), (6, 4, 2000)]:
    Pi = frozenset(range(k))
    es = edges_of(n)
    for _ in range(trials):
        labels = {}
        for e in es:
            labels[e] = frozenset([rng.randrange(k)]) if rng.random() < 0.55 else frozenset()
        s, t = 0, n - 1
        if any(reaches(labels, s, t, p) for p in Pi):
            continue                                   # P reachable: no negative certificate
        paths = simple_paths(n, labels, s, t)
        hyper = {frozenset(next(iter(labels[(a, b)])) for a, b in zip(pth, pth[1:])) for pth in paths}
        m1 = min_cuts(labels, s, t, Pi)
        m2 = chromatic(k, hyper) if hyper else 1
        checked += 1
        if m1 != m2:
            bad += 1; print("MISMATCH", labels, m1, m2)
print(f"hypergraph-coloring equivalence (single-label case): {checked} unreachable instances checked, {bad} mismatches")
