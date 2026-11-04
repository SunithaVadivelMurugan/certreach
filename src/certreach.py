"""
certreach: certificates for reachability in packet-labelled directed graphs.

Model
-----
A graph has nodes 0..n-1.  Each ordered pair (u, v) with u != v is a potential
edge carrying a label: a finite set of packets (the traffic the edge admits).
An empty label means the edge is absent.  A packet p *reaches* t from s if some
walk s = v0 -> v1 -> ... -> vk = t exists in which p belongs to every edge label.

A query is (s, t, P) with P a nonempty set of packets.  It is "reachable" if some
p in P reaches t, and "unreachable" if no p in P reaches t.

Certificates
------------
Positive: (p, path) with p in P and path a node sequence from s to t, every
          consecutive edge admitting p.
Negative: a list of cuts (group, S).  A cut is valid for a group of packets if
          s in S, t not in S, and every edge leaving S has a label disjoint from
          the group.  The negative certificate is valid if the valid cuts' groups
          together cover P.

Everything here is deliberately small: the checkers are the part intended to be
formally verified later.
"""

from itertools import combinations


# --------------------------------------------------------------------------
# Ground truth (used for testing, not part of the trusted checker)
# --------------------------------------------------------------------------

def reach_set(labels, s, group):
    """Nodes reachable from s using edges whose label meets `group`."""
    seen = {s}
    stack = [s]
    while stack:
        u = stack.pop()
        for (a, b), lab in labels.items():
            if a == u and b not in seen and lab & group:
                seen.add(b)
                stack.append(b)
    return seen


def reaches(labels, s, t, p):
    return t in reach_set(labels, s, frozenset([p]))


def bfs_path(labels, s, t, p):
    """A shortest s-t path for packet p, or None."""
    prev = {s: None}
    queue = [s]
    for u in queue:
        if u == t:
            break
        for (a, b), lab in labels.items():
            if a == u and b not in prev and p in lab:
                prev[b] = u
                queue.append(b)
    if t not in prev:
        return None
    path = []
    cur = t
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    return path[::-1]


# --------------------------------------------------------------------------
# Checkers (the small trusted core)
# --------------------------------------------------------------------------

def check_positive(labels, s, t, P, cert):
    p, path = cert
    if p not in P or not path or path[0] != s or path[-1] != t:
        return False
    for a, b in zip(path, path[1:]):
        if a == b or p not in labels.get((a, b), frozenset()):
            return False
    return True


def check_cut(labels, s, t, group, S):
    if s not in S or t in S:
        return False
    for (u, v), lab in labels.items():
        if u in S and v not in S and lab & group:
            return False
    return True


def check_negative(labels, s, t, P, cuts):
    covered = set()
    for group, S in cuts:
        if check_cut(labels, s, t, group, S):
            covered |= set(group)
    return set(P) <= covered


# --------------------------------------------------------------------------
# Certificate generation (untrusted; the checker validates its output)
# --------------------------------------------------------------------------

def make_positive(labels, s, t, P):
    for p in sorted(P):
        path = bfs_path(labels, s, t, p)
        if path is not None:
            return (p, path)
    return None


def make_negative_per_packet(labels, s, P):
    """One cut per packet: the set reachable for that packet."""
    return [(frozenset([p]), frozenset(reach_set(labels, s, frozenset([p]))))
            for p in sorted(P)]


# --------------------------------------------------------------------------
# Certificate-size analysis
# --------------------------------------------------------------------------

def atoms(labels, P):
    """Number of classes of packets in P that no edge label can tell apart."""
    sigs = {}
    for p in P:
        sigs[p] = frozenset(e for e, lab in labels.items() if p in lab)
    return len(set(sigs.values()))


def min_cuts(labels, s, t, P):
    """
    Minimum number of cuts in a negative certificate for P (P must be unreachable).
    A group G is certifiable by one cut iff t is unreachable from s in the graph of
    edges whose label meets G.  Minimum partition of P into certifiable groups,
    by dynamic programming over subsets (fine for |P| <= ~10).
    """
    plist = sorted(P)
    k = len(plist)
    ok = {}
    for mask in range(1, 1 << k):
        group = frozenset(plist[i] for i in range(k) if mask >> i & 1)
        ok[mask] = t not in reach_set(labels, s, group)
    full = (1 << k) - 1
    INF = 10 ** 9
    best = [INF] * (1 << k)
    best[0] = 0
    for mask in range(1, 1 << k):
        low = mask & -mask
        sub = mask
        while sub:
            if sub & low and ok[sub] and best[mask ^ sub] + 1 < best[mask]:
                best[mask] = best[mask ^ sub] + 1
            sub = (sub - 1) & mask
    return best[full] if best[full] < INF else None
