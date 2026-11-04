"""
Tests for Proposition 7 (insertion-only maintenance of cut certificates).

T6  correctness : after EVERY insertion, each live group's S_i equals the reachable set
                  in H_{G_i}, the pair (G_i, S_i) passes the repository checker, a group
                  is dead exactly when t is reachable, and for dead singleton groups the
                  parent-pointer path is a valid positive certificate.
T7  cost        : total work against the O(m (n + M + I)) bound, and against rebuilding
                  from scratch after each insertion (estimated by sampling).
"""

import random
import sys

from certreach import check_cut, check_positive
from maintain import CutMaintainer


def to_frozensets(labels, k):
    return {e: frozenset(i for i in range(k) if mask >> i & 1) for e, mask in labels.items()}


def mask_to_set(mask, k):
    return frozenset(i for i in range(k) if mask >> i & 1)


def test_correctness(trials, seed):
    rng = random.Random(seed)
    checks = 0
    for _ in range(trials):
        n = rng.randint(3, 9)
        k = rng.randint(2, 6)
        s, t = 0, n - 1
        # random partition of a random subset of packets into groups
        packets = list(range(k))
        rng.shuffle(packets)
        groups, i = [], 0
        while i < k:
            size = rng.randint(1, 3)
            chunk = packets[i:i + size]
            groups.append(sum(1 << p for p in chunk))
            i += size
        M = CutMaintainer(n, s, t, groups)
        for _ in range(rng.randint(5, 60)):
            u, v = rng.sample(range(n), 2)
            M.insert(u, v, rng.randrange(k))
            fs = to_frozensets(M.labels, k)
            for gi, g in enumerate(groups):
                reach, _ = M.reach_from_scratch(gi)
                t_reachable = t in reach
                assert M.dead[gi] == t_reachable, ("dead flag wrong", gi)
                if not M.dead[gi]:
                    assert M.S[gi] == reach, ("S != reachable set", gi)
                    assert check_cut(fs, s, t, mask_to_set(g, k), frozenset(M.S[gi])), \
                        ("checker rejects maintained cut", gi)
                else:
                    G = mask_to_set(g, k)
                    if len(G) == 1:
                        par = M.parent[gi]
                        path, cur = [], t
                        while cur is not None:
                            path.append(cur)
                            cur = par[cur]
                        path.reverse()
                        p = next(iter(G))
                        assert check_positive(fs, s, t, G, (p, path)), "bad path for dead singleton"
                checks += 1
    return checks


def scale_run(n, I, k, m, seed, sample_every):
    rng = random.Random(seed)
    s, t = 0, n - 1
    per = k // m
    groups = [sum(1 << p for p in range(j * per, (j + 1) * per)) for j in range(m)]
    M = CutMaintainer(n, s, t, groups)
    samples = []
    processed = 0
    death = [None] * m
    for step in range(I):
        u, v = rng.sample(range(n), 2)
        M.insert(u, v, rng.randrange(k))
        processed += 1
        for gi in range(m):
            if M.dead[gi] and death[gi] is None:
                death[gi] = step + 1
        if step % sample_every == 0:
            live = sum(1 for d in M.dead if not d)
            if live:
                samples.append((live, M.recompute_cost()))
        if all(M.dead):
            break
    edges = len(M.labels)
    bound = m * (n + edges + processed)
    # naive: rebuild every live group from scratch after each insertion
    avg_naive = sum(c for _, c in samples) / max(len(samples), 1)
    naive_total = avg_naive * processed
    return dict(n=n, groups=m, insertions=processed, edges=edges,
                maintained_ops=M.ops, searches=M.searches,
                ops_over_bound=M.ops / bound,
                est_naive_ops=naive_total,
                est_speedup=naive_total / max(M.ops, 1),
                deaths=death)


if __name__ == "__main__":
    quick = len(sys.argv) > 1 and sys.argv[1] == "quick"
    c = test_correctness(2000 if quick else 20000, seed=21)
    print(f"T6 correctness: {c} (stream step, group) checks passed.")
    configs = [(500, 5000, 16, 8, 3, 50), (2000, 20000, 16, 8, 4, 200)]
    if not quick:
        configs.append((5000, 50000, 16, 8, 5, 500))
    print("\nT7 cost (random insertion streams, 16 packets in 8 groups of 2):")
    for cfg in configs:
        r = scale_run(*cfg)
        died = sum(1 for d in r["deaths"] if d is not None)
        print(f"  n={r['n']}: {r['insertions']} insertions, {r['edges']} edges, "
              f"{died}/{r['groups']} groups reached t; "
              f"maintained ops {r['maintained_ops']:,} "
              f"(= {r['ops_over_bound']:.2f} x m(n+M+I)); "
              f"{r['searches']} searches; "
              f"estimated rebuild-each-time ops {r['est_naive_ops']:,.0f} "
              f"(~{r['est_speedup']:.0f}x more)")
    print("\nAll assertions passed.")
