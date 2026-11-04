"""Check Prop. 3: a group G has a valid cut iff t is unreachable from s in the union graph H_G."""
import random
from itertools import product
from exhaustive_tests import subsets, edges_of, random_labels
from certreach import reach_set, check_cut

def check(n, labels, Pi):
    s, t = 0, n - 1
    others = [v for v in range(n) if v not in (s, t)]
    cut_sets = [frozenset([s]) | frozenset(c) for c in subsets(others)]
    for G in subsets(Pi):
        if not G:
            continue
        exists_cut = any(check_cut(labels, s, t, G, S) for S in cut_sets)
        unreachable = t not in reach_set(labels, s, G)
        assert exists_cut == unreachable, (labels, G)
        # monotone: every subset of a certifiable group is certifiable
        if exists_cut:
            for H in subsets(G):
                if H:
                    assert any(check_cut(labels, s, t, H, S) for S in cut_sets)

n, k = 3, 3
Pi = list(range(k)); edges = edges_of(n); subs = list(subsets(Pi)); c = 0
for combo in product(subs, repeat=len(edges)):
    check(n, dict(zip(edges, combo)), Pi); c += 1
print(f"Prop 3 + downward closure: exhaustive n=3, k=3 ({c} graphs): OK")
rng = random.Random(5)
for n, k, trials in [(4, 3, 20000), (5, 4, 4000)]:
    Pi = list(range(k))
    for _ in range(trials):
        check(n, random_labels(n, Pi, 0.35, rng), Pi)
    print(f"Prop 3 + downward closure: random n={n}, k={k} ({trials} graphs): OK")
