"""
Experiment: can the small checker catch bugs in untrusted reachability code?

Interface of an untrusted solver:
    solve(n, labels, s, t, P) -> ("reachable", (p, path))        positive certificate
                              or ("unreachable", [(group, S)...]) negative certificate

Part A: four implementations written by an LLM (Claude) from the one-paragraph
        problem statement.  V2 and V3 are natural first-attempt mistakes that were
        NOT injected on purpose: V2 treats the packet set as one union graph, V3 shares
        a visited set across packets for speed.
Part B: bug injection (mutation analysis) into the correct per-packet BFS (V1).

For every run we classify the outcome against brute-force ground truth:
    ok            right answer, certificate accepted
    wrong_caught  wrong answer, certificate rejected          (the checker did its job)
    wrong_missed  wrong answer, certificate ACCEPTED          (must never happen: soundness)
    cert_bug      right answer, certificate rejected          (bug in certificate output)
    crash         the solver raised an exception
"""

import random
import time
from collections import Counter

from certreach import reaches, check_positive, check_negative


# ---------------------------------------------------------------- Part A -----

def solve_v1(n, labels, s, t, P):
    """Per-packet BFS with parent pointers."""
    cuts = []
    for p in sorted(P):
        seen, parent, q = {s}, {s: None}, [s]
        for u in q:
            for (a, b), lab in labels.items():
                if a == u and b not in seen and p in lab:
                    seen.add(b)
                    parent[b] = u
                    q.append(b)
        if t in seen:
            path, cur = [], t
            while cur is not None:
                path.append(cur)
                cur = parent[cur]
            return ("reachable", (p, path[::-1]))
        cuts.append((frozenset([p]), frozenset(seen)))
    return ("unreachable", cuts)


def solve_v2(n, labels, s, t, P):
    """Union graph: follow any edge whose label meets P (one BFS for all packets)."""
    seen, parent, q = {s}, {s: None}, [s]
    for u in q:
        for (a, b), lab in labels.items():
            if a == u and b not in seen and lab & P:
                seen.add(b)
                parent[b] = u
                q.append(b)
    if t in seen:
        path, cur = [], t
        while cur is not None:
            path.append(cur)
            cur = parent[cur]
        path = path[::-1]
        p = min(labels[(path[0], path[1])] & P)
        return ("reachable", (p, path))
    return ("unreachable", [(frozenset(P), frozenset(seen))])


def solve_v3(n, labels, s, t, P):
    """Per-packet BFS, but the visited set is shared across packets 'for speed'."""
    seen, parent = {s}, {s: None}
    cuts = []
    for p in sorted(P):
        q = [s]
        for u in q:
            for (a, b), lab in labels.items():
                if a == u and b not in seen and p in lab:
                    seen.add(b)
                    parent[b] = u
                    q.append(b)
        if t in seen:
            path, cur = [], t
            while cur is not None:
                path.append(cur)
                cur = parent[cur]
            return ("reachable", (p, path[::-1]))
        cuts.append((frozenset([p]), frozenset(seen)))
    return ("unreachable", cuts)


def solve_v4(n, labels, s, t, P):
    """Per-packet Floyd-Warshall transitive closure with next-hop reconstruction."""
    cuts = []
    for p in sorted(P):
        reach = [[False] * n for _ in range(n)]
        nxt = [[None] * n for _ in range(n)]
        for (a, b), lab in labels.items():
            if p in lab:
                reach[a][b] = True
                nxt[a][b] = b
        for i in range(n):
            reach[i][i] = True
            nxt[i][i] = i
        for k in range(n):
            for i in range(n):
                if reach[i][k]:
                    for j in range(n):
                        if reach[k][j] and not reach[i][j]:
                            reach[i][j] = True
                            nxt[i][j] = nxt[i][k]
        if reach[s][t]:
            path, cur = [s], s
            while cur != t:
                cur = nxt[cur][t]
                path.append(cur)
            return ("reachable", (p, path))
        cuts.append((frozenset([p]), frozenset(j for j in range(n) if reach[s][j])))
    return ("unreachable", cuts)


# ---------------------------------------------------------------- Part B -----

def solve_mutant(mut):
    """Correct per-packet BFS (V1) with one injected bug."""
    def solve(n, labels, s, t, P):
        universe = sorted({p for lab in labels.values() for p in lab} | set(P))
        packets = sorted(P)
        if mut == "ignore_P_filter":
            packets = universe
        if mut == "skip_last_packet":
            packets = packets[:-1]
        cuts = []
        for p in packets:
            seen, parent, q = {s}, {s: None}, [s]
            for u in q:
                for (a, b), lab in labels.items():
                    ends = [(a, b)] + ([(b, a)] if mut == "undirected" else [])
                    for x, y in ends:
                        ok_label = (lab & P) if mut == "union_label" else (p in lab)
                        if x == u and y not in seen and ok_label:
                            seen.add(y)
                            parent[y] = u
                            q.append(y)
            if t in seen:
                path, cur = [], t
                while cur is not None:
                    path.append(cur)
                    cur = parent[cur]
                if mut != "path_not_reversed":
                    path = path[::-1]
                else:
                    pass
                if mut == "off_by_one_path":
                    path = path[:-1]
                rp = p
                if mut == "wrong_packet":
                    rp = sorted(P)[0]
                return ("reachable", (rp, path))
            S = frozenset(seen)
            if mut == "cut_without_source":
                S = S - {s}
            if mut == "complement_of_target":
                S = frozenset(range(n)) - {t}
            cuts.append((frozenset([p]), S))
        if mut == "only_first_cut":
            cuts = cuts[:1]
        return ("unreachable", cuts)
    return solve


MUTANTS = ["undirected", "path_not_reversed", "union_label", "skip_last_packet",
           "cut_without_source", "complement_of_target", "only_first_cut",
           "off_by_one_path", "wrong_packet", "ignore_P_filter"]


# ------------------------------------------------------------- harness -------

def random_instance(rng):
    n = rng.randint(3, 7)
    k = rng.randint(2, 5)
    density = rng.choice([0.2, 0.35, 0.5])
    Pi = list(range(k))
    labels = {}
    for u in range(n):
        for v in range(n):
            if u != v:
                labels[(u, v)] = frozenset(p for p in Pi if rng.random() < density)
    P = frozenset(rng.sample(Pi, rng.randint(1, k)))
    return n, labels, 0, n - 1, P


def classify(solver, inst):
    n, labels, s, t, P = inst
    truth = any(reaches(labels, s, t, p) for p in P)
    try:
        verdict, cert = solver(n, labels, s, t, P)
    except Exception:
        return "crash"
    claimed = verdict == "reachable"
    try:
        if claimed:
            accepted = check_positive(labels, s, t, P, cert)
        else:
            accepted = check_negative(labels, s, t, P, cert)
    except Exception:
        accepted = False
    correct = claimed == truth
    if correct and accepted:
        return "ok"
    if not correct and not accepted:
        return "wrong_caught"
    if not correct and accepted:
        return "wrong_missed"
    return "cert_bug"


def run(solvers, trials, seed):
    rng = random.Random(seed)
    insts = [random_instance(rng) for _ in range(trials)]
    table = {}
    for name, solver in solvers.items():
        table[name] = Counter(classify(solver, inst) for inst in insts)
    return table


def print_table(title, table, trials):
    cols = ["ok", "wrong_caught", "cert_bug", "crash", "wrong_missed"]
    print("\n" + title)
    print(f"{'solver':<22}" + "".join(f"{c:>14}" for c in cols) + f"{'exposed %':>12}")
    for name, cnt in table.items():
        exposed = 100.0 * (trials - cnt["ok"]) / trials
        print(f"{name:<22}" + "".join(f"{cnt[c]:>14}" for c in cols) + f"{exposed:>12.1f}")


def timing(seed=2):
    """Solve time versus check time on larger graphs (pure Python, indicative only)."""
    rng = random.Random(seed)
    n, k = 25, 8
    Pi = list(range(k))
    reps = 60
    solve_t = check_pos_t = check_neg_t = 0.0
    pos = neg = 0
    for _ in range(reps):
        labels = {(u, v): frozenset(p for p in Pi if rng.random() < 0.06)
                  for u in range(n) for v in range(n) if u != v}
        P = frozenset(Pi)
        t0 = time.perf_counter()
        verdict, cert = solve_v1(n, labels, 0, n - 1, P)
        t1 = time.perf_counter()
        if verdict == "reachable":
            check_positive(labels, 0, n - 1, P, cert)
            t2 = time.perf_counter()
            check_pos_t += t2 - t1
            pos += 1
        else:
            check_negative(labels, 0, n - 1, P, cert)
            t2 = time.perf_counter()
            check_neg_t += t2 - t1
            neg += 1
        solve_t += t1 - t0
    print(f"\nTiming (n={n}, {k} packets, {reps} graphs): "
          f"mean solve {1e3 * solve_t / reps:.2f} ms; "
          f"mean check {1e3 * check_pos_t / max(pos, 1):.3f} ms (positive, {pos} cases), "
          f"{1e3 * check_neg_t / max(neg, 1):.3f} ms (negative, {neg} cases)")


if __name__ == "__main__":
    trials = 30000
    A = {"V1 per-packet BFS": solve_v1, "V2 union graph": solve_v2,
         "V3 shared visited": solve_v3, "V4 Floyd-Warshall": solve_v4}
    print_table(f"Part A: LLM-written implementations ({trials} random instances)",
                run(A, trials, seed=1), trials)
    B = {"mut:" + m: solve_mutant(m) for m in MUTANTS}
    B = {"V1 (unmutated)": solve_mutant("none"), **B}
    print_table(f"Part B: injected bugs in V1 ({trials} random instances)",
                run(B, trials, seed=2), trials)
    timing()
