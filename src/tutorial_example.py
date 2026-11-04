"""
Worked example for docs/tutorial.md: build a labelled graph, produce certificates,
and check them.  Run from the src/ directory:  python tutorial_example.py
"""
from certreach import (make_positive, make_negative_per_packet, check_positive,
                       check_negative, check_cut, reach_set, min_cuts)

# Nodes: 0 = s, 1 = a, 2 = c, 3 = b, 4 = t.  Packets are port numbers.
labels = {
    (0, 1): frozenset({22, 80, 443}),
    (1, 2): frozenset({80, 443}),
    (2, 4): frozenset({443}),
    (1, 3): frozenset({22}),
    (3, 4): frozenset({5432}),
}
s, t = 0, 4

# 1. A positive certificate for port 443.
P = frozenset({443})
cert = make_positive(labels, s, t, P)
print("positive certificate:", cert)
print("checker accepts:", check_positive(labels, s, t, P, cert))

# 2. A negative certificate for port 22: one cut, the set reachable from s.
P = frozenset({22})
cuts = make_negative_per_packet(labels, s, P)
print("negative certificate:", [(sorted(g), sorted(S)) for g, S in cuts])
print("checker accepts:", check_negative(labels, s, t, P, cuts))

# 3. The subtlety: a packet set can be unreachable even though no single cut works.
labels2 = {(0, 1): frozenset({22}), (1, 2): frozenset({80})}
s2, t2, P2 = 0, 2, frozenset({22, 80})
union_cut = (P2, frozenset(reach_set(labels2, s2, P2)))
print("one cut for the whole set valid:", check_cut(labels2, s2, t2, *union_cut))
print("cuts per packet valid:",
      check_negative(labels2, s2, t2, P2, make_negative_per_packet(labels2, s2, P2)))
print("minimum number of cuts:", min_cuts(labels2, s2, t2, P2))
