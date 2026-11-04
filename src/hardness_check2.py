"""Discriminating version: include hypergraphs that are NOT 2-colorable (Fano plane, dense random)."""
import random
from itertools import combinations
from hardness_check import build, chromatic   # reuses the construction (re-runs its small test on import)
from certreach import min_cuts, reaches

fano = [(0,1,2),(0,3,4),(0,5,6),(1,3,5),(1,4,6),(2,3,6),(2,4,5)]
n, labels = build(7, fano)
P = frozenset(range(7))
assert not any(reaches(labels, 0, 1, p) for p in P)
m, c = min_cuts(labels, 0, 1, P), chromatic(7, fano)
print(f"Fano plane (not 2-colorable): m*(P) = {m}, chromatic number = {c}")
assert m == c == 3

rng = random.Random(4)
stats = {}
for _ in range(300):
    k = rng.randint(5, 7)
    triples = list(combinations(range(k), 3))
    r = rng.randint(len(triples) // 2, len(triples))
    H = rng.sample(triples, r)
    n, labels = build(k, H)
    P = frozenset(range(k))
    m, c = min_cuts(labels, 0, 1, P), chromatic(k, H)
    assert m == c, ("mismatch", H, m, c)
    stats[c] = stats.get(c, 0) + 1
print("dense random hypergraphs, m*(P) == chromatic number in all; counts by value:", dict(sorted(stats.items())))
