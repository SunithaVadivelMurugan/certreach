"""
Insertion-only maintenance of cut certificates (Proposition 7).

State: for each fixed group G_i (a bitmask of packets), the set S_i of nodes reachable
from s in H_{G_i}, the graph of edges whose label meets G_i.  While t is not in S_i,
(G_i, S_i) is a valid cut.  Labels only grow (insertions).

insert(u, v, p):
    adds packet p to the label of edge (u, v).  For each live group i that the edge
    newly meets, if u is in S_i and v is not, search forward from v and add what is
    reached.  If t is reached the group is "dead": its cut is no longer valid and a
    positive path now exists for H_{G_i} (a re-partition is needed if |G_i| > 1).

`ops` counts elementary steps: one group test per (insertion, group) and one edge scan
per out-edge examined during a search.
"""


class CutMaintainer:
    def __init__(self, n, s, t, groups):
        self.n, self.s, self.t = n, s, t
        self.groups = list(groups)                      # bitmasks
        self.labels = {}                                # (u, v) -> bitmask
        self.out = [[] for _ in range(n)]
        self.S = [{s} for _ in self.groups]
        self.dead = [False] * len(self.groups)
        self.parent = [{s: None} for _ in self.groups]
        self.ops = 0
        self.searches = 0

    def insert(self, u, v, p):
        old = self.labels.get((u, v), 0)
        new = old | (1 << p)
        if new == old:
            return
        self.labels[(u, v)] = new
        if old == 0:
            self.out[u].append(v)
        for i, g in enumerate(self.groups):
            self.ops += 1                               # group test
            if self.dead[i] or not (new & g) or (old & g):
                continue                                # not newly meeting this group
            S = self.S[i]
            if u in S and v not in S:
                self.searches += 1
                self._extend(i, u, v)

    def _extend(self, i, u, v):
        S, g, par = self.S[i], self.groups[i], self.parent[i]
        S.add(v)
        par[v] = u
        stack = [v]
        while stack:
            x = stack.pop()
            if x == self.t:
                self.dead[i] = True
                return
            for y in self.out[x]:
                self.ops += 1                           # edge scan
                if y not in S and self.labels[(x, y)] & g:
                    S.add(y)
                    par[y] = x
                    stack.append(y)

    # -- reference computations, for tests and cost comparison ---------------

    def reach_from_scratch(self, i):
        """Reachable set in H_{G_i}, plus the number of edge scans it takes."""
        g = self.groups[i]
        seen, stack, scans = {self.s}, [self.s], 0
        while stack:
            x = stack.pop()
            for y in self.out[x]:
                scans += 1
                if y not in seen and self.labels[(x, y)] & g:
                    seen.add(y)
                    stack.append(y)
        return seen, scans

    def recompute_cost(self):
        """Edge scans to rebuild every live group from scratch."""
        return sum(self.reach_from_scratch(i)[1]
                   for i in range(len(self.groups)) if not self.dead[i])
