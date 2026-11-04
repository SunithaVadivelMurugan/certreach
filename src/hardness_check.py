"""
Check of the reduction from SET SPLITTING (3-uniform hypergraph 2-coloring) to deciding m*(P) <= 2.

Given a 3-uniform hypergraph H on packets 0..k-1 with hyperedges e_1..e_r, build a graph with
source 0, target 1, and for each hyperedge e_j = {a, b, c} a private path
    0 -> x_j -> y_j -> 1
whose three edges carry the single packets a, b, c.  Then:
  * the s-t paths are exactly the r private paths, with packet sets e_j;
  * every packet in P = {0..k-1} is individually unreachable (each path has 3 distinct packets);
  * m*(P) equals the chromatic number of H (no monochromatic hyperedge); in particular
    m*(P) <= 2  iff  H is 2-colorable.
"""
import random
from itertools import combinations, product
from certreach import min_cuts, reaches

def build(k, hyperedges):
    labels = {}
    n = 2 + 2 * len(hyperedges)
    for u in range(n):
        for v in range(n):
            if u != v:
                labels[(u, v)] = frozenset()
    for j, (a, b, c) in enumerate(hyperedges):
        x, y = 2 + 2 * j, 3 + 2 * j
        labels[(0, x)] = frozenset([a])
        labels[(x, y)] = frozenset([b])
        labels[(y, 1)] = frozenset([c])
    return n, labels

def chromatic(k, hyperedges):
    for m in range(1, k + 1):
        for col in product(range(m), repeat=k):
            if all(len({col[p] for p in h}) > 1 for h in hyperedges):
                return m
    return None

rng = random.Random(9)
checked = two_col = not_two_col = 0
for _ in range(3000):
    k = rng.randint(3, 7)
    triples = list(combinations(range(k), 3))
    r = rng.randint(1, min(len(triples), 9))
    H = rng.sample(triples, r)
    n, labels = build(k, H)
    P = frozenset(range(k))
    assert not any(reaches(labels, 0, 1, p) for p in P)          # unreachable, as claimed
    m = min_cuts(labels, 0, 1, P)
    c = chromatic(k, H)
    assert m == c, ("mismatch", H, m, c)
    checked += 1
    if c <= 2: two_col += 1
    else: not_two_col += 1
print(f"reduction check: {checked} random 3-uniform hypergraphs; m*(P) equals the chromatic number in all; "
      f"{two_col} are 2-colorable, {not_two_col} need 3 or more colors.")
