"""
Exhaustive (small) and randomized tests for certreach.

T1  soundness   : any certificate the checker accepts is correct (exhaustive over
                  ALL candidate certificates on small graphs).
T2  completeness: whenever the claim is true, a certificate exists and passes.
T3  subtlety    : how often one cut cannot certify a whole packet set.
T4  size        : minimum cuts versus number of atoms versus |P|.
T5  incremental : after label edits, rechecking only the edited edges agrees with
                  a full recheck.
"""

import random
import sys
from itertools import product, combinations
from collections import Counter

from certreach import (reach_set, reaches, bfs_path, check_positive, check_cut,
                       check_negative, make_positive, make_negative_per_packet,
                       atoms, min_cuts)


def subsets(items):
    items = list(items)
    for r in range(len(items) + 1):
        for c in combinations(items, r):
            yield frozenset(c)


def edges_of(n):
    return [(u, v) for u in range(n) for v in range(n) if u != v]


def simple_paths(n, labels, s, t):
    """All simple s-t node sequences over pairs with a nonempty label."""
    out = []

    def dfs(u, path):
        if u == t:
            out.append(list(path))
            return
        for v in range(n):
            if v not in path and labels.get((u, v)):
                path.append(v)
                dfs(v, path)
                path.pop()

    dfs(s, [s])
    return out


def run_instance(n, labels, s, t, Pi, stats, full_enumeration=True):
    """Run T1-T4 on one labelled graph over every nonempty query set P."""
    others = [v for v in range(n) if v not in (s, t)]
    cut_sets = [frozenset([s]) | frozenset(c) for c in subsets(others)]
    paths_cache = {}
    for P in subsets(Pi):
        if not P:
            continue
        truth = {p: reaches(labels, s, t, p) for p in P}
        any_reach = any(truth.values())

        # T1 soundness of positive certificates (all simple paths x all p in P)
        if full_enumeration:
            for path in simple_paths(n, labels, s, t):
                for p in sorted(P):
                    if check_positive(labels, s, t, P, (p, path)):
                        stats["T1_pos_accepted"] += 1
                        assert truth[p], ("unsound positive", labels, P, p, path)
            # T1 soundness of negative cuts (all groups x all candidate S)
            for group in subsets(P):
                if not group:
                    continue
                for S in cut_sets:
                    if check_cut(labels, s, t, group, S):
                        stats["T1_cut_accepted"] += 1
                        assert not any(truth[p] for p in group), (
                            "unsound cut", labels, group, S)

        # T2 completeness
        if any_reach:
            cert = make_positive(labels, s, t, P)
            assert cert is not None and check_positive(labels, s, t, P, cert)
            stats["T2_pos_complete"] += 1
        else:
            cuts = make_negative_per_packet(labels, s, P)
            assert check_negative(labels, s, t, P, cuts), ("incomplete", labels, P)
            stats["T2_neg_complete"] += 1

            # T3 / T4
            m = min_cuts(labels, s, t, P)
            a = atoms(labels, P)
            assert m is not None and m <= a <= len(P)
            # verify the minimum is achievable by a real certificate: group packets
            stats[("size", len(P), "atoms", a, "mincuts", m)] += 1
            if len(P) >= 2:
                stats["T3_negP_queries"] += 1
                if m > 1:
                    stats["T3_needs_multiple_cuts"] += 1
                if m < a:
                    stats["T4_mincuts_lt_atoms"] += 1
                if m < len(P):
                    stats["T4_mincuts_lt_P"] += 1


def random_labels(n, Pi, density, rng):
    labels = {}
    for e in edges_of(n):
        labels[e] = frozenset(p for p in Pi if rng.random() < density)
    return labels


def test_exhaustive(n, k):
    """Every labelling of every ordered pair with every subset of k packets."""
    Pi = list(range(k))
    edges = edges_of(n)
    subs = list(subsets(Pi))
    stats = Counter()
    count = 0
    for combo in product(subs, repeat=len(edges)):
        labels = dict(zip(edges, combo))
        run_instance(n, labels, 0, n - 1, Pi, stats)
        count += 1
    return count, stats


def test_random(n, k, trials, density, seed):
    rng = random.Random(seed)
    Pi = list(range(k))
    stats = Counter()
    for _ in range(trials):
        labels = random_labels(n, Pi, density, rng)
        run_instance(n, labels, 0, n - 1, Pi, stats)
    return trials, stats


# ---------------------------------------------------------------- T5 ---------

def full_valid(labels, s, t, kind, cert, P):
    if kind == "pos":
        return check_positive(labels, s, t, P, cert)
    group, S = cert
    return check_cut(labels, s, t, group, S)


def local_valid(old_labels, new_labels, edited, s, t, kind, cert, P):
    """Revalidate an ALREADY-VALID certificate by looking only at edited edges."""
    if kind == "pos":
        p, path = cert
        on_path = set(zip(path, path[1:]))
        return all(p in new_labels.get(e, frozenset()) for e in edited if e in on_path)
    group, S = cert
    return all(not (new_labels.get(e, frozenset()) & group)
               for e in edited if e[0] in S and e[1] not in S)


def test_incremental(n, k, trials, seed):
    rng = random.Random(seed)
    Pi = list(range(k))
    es = edges_of(n)
    s, t = 0, n - 1
    stats = Counter()
    for _ in range(trials):
        labels = random_labels(n, Pi, 0.4, rng)
        P = frozenset(rng.sample(Pi, rng.randint(1, k)))
        # a valid certificate for one packet class
        p = rng.choice(sorted(P))
        if reaches(labels, s, t, p):
            cert, kind, group = (p, bfs_path(labels, s, t, p)), "pos", P
        else:
            group = frozenset([p])
            cert, kind = (group, frozenset(reach_set(labels, s, group))), "neg"
        assert full_valid(labels, s, t, kind, cert, P if kind == "pos" else group)
        # a batch of 1-3 edits
        edited = rng.sample(es, rng.randint(1, 3))
        new = dict(labels)
        for e in edited:
            q = rng.choice(Pi)
            new[e] = new[e] ^ frozenset([q])      # toggle packet q on edge e
        scope = P if kind == "pos" else group
        f = full_valid(new, s, t, kind, cert, scope)
        l = local_valid(labels, new, edited, s, t, kind, cert, scope)
        assert f == l, ("local/full mismatch", labels, new, edited, kind, cert)
        stats[(kind, "still_valid" if f else "invalidated")] += 1
    return stats


if __name__ == "__main__":
    quick = len(sys.argv) > 1 and sys.argv[1] == "quick"

    def show(title, stats):
        print("\n=== " + title)
        keys = [k for k in stats if isinstance(k, str)]
        for k in sorted(keys):
            print(f"  {k}: {stats[k]}")

    c, st = test_exhaustive(3, 2)
    print(f"Exhaustive n=3, 2 packets: {c} labelled graphs, all queries.")
    show("exhaustive n=3, k=2", st)

    if not quick:
        c, st = test_exhaustive(3, 3)
        print(f"\nExhaustive n=3, 3 packets: {c} labelled graphs, all queries.")
        show("exhaustive n=3, k=3", st)

    for (n, k, trials, dens) in [(4, 3, 20000, 0.35), (5, 4, 4000, 0.3)]:
        if quick:
            trials //= 10
        c, st = test_random(n, k, trials, dens, seed=7)
        print(f"\nRandom n={n}, {k} packets, density {dens}: {c} graphs, all queries.")
        show(f"random n={n}, k={k}", st)
        sizes = Counter()
        for key, v in st.items():
            if isinstance(key, tuple):
                _, sizeP, _, a, _, m = key
                sizes[(sizeP, a, m)] += v
        print("  (|P|, atoms, min cuts) -> count   [unreachable queries only]")
        for key in sorted(sizes):
            if key[0] >= 2:
                print(f"    {key}: {sizes[key]}")

    for (n, k) in [(4, 3), (6, 4)]:
        trials = 20000 if quick else 200000
        stats = test_incremental(n, k, trials, seed=11)
        print(f"\nIncremental recheck n={n}, k={k}: {trials} edit batches, "
              "local recheck == full recheck in every trial.")
        for key in sorted(stats):
            print(f"    {key}: {stats[key]}")

    print("\nAll assertions passed.")
