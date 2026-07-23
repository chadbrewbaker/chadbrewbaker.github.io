# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
# https://chadbrewbaker.github.io/ — companion to the 2026-07-22 union-find post
#
# Run with:  uv run dsu_proof_forest.py
#
# Union-Find under Curry-Howard: the parent forest IS a proof forest for
# equational logic. union(a,b,"ax_k") asserts an axiom a=b; find computes a
# canonical representative (normalization); explain(a,b) EXTRACTS an
# equational proof — a chain of axiom uses closed under symmetry and
# transitivity. This is exactly what proof-producing congruence closure
# inside z3/cvc5 does (Nieuwenhuis-Oliveras); path compression is memoized
# proof normalization and is why it must be done carefully (or skipped, as
# here) when proofs must be recoverable.

class ProofDSU:
    def __init__(self):
        self.parent, self.reason = {}, {}   # reason[x] = (axiom, other_end)

    def add(self, x):
        self.parent.setdefault(x, x)

    def find(self, x):
        while self.parent[x] != x:
            x = self.parent[x]
        return x

    def union(self, a, b, axiom):
        self.add(a); self.add(b)
        # reroot a's tree so a becomes its root, then hang it under b
        path = [a]
        while self.parent[path[-1]] != path[-1]:
            path.append(self.parent[path[-1]])
        for child, par in zip(reversed(path[:-1]), reversed(path[1:])):
            # reverse edge par->child, flipping the stored reason
            self.parent[par] = child
            self.reason[par] = tuple(reversed(self.reason[child][0:1])) or None
            self.reason[par] = (self.reason[child][0], child)
        self.parent[a] = b
        self.reason[a] = (axiom, b)

    def path_to_root(self, x):
        out = []
        while self.parent[x] != x:
            ax, nxt = self.reason[x]
            out.append((x, ax, self.parent[x]))
            x = self.parent[x]
        return out

    def explain(self, a, b):
        assert self.find(a) == self.find(b), "not provably equal"
        pa, pb = self.path_to_root(a), self.path_to_root(b)
        sa = {x for x, _, _ in pa} | {self.find(a)}
        # least common ancestor in the proof forest
        lca = next(x for x, _, _ in pb + [(self.find(b), None, None)] if x in
                   [self.find(a)] + [y for _, _, y in pa] + [a])
        proof = []
        for x, ax, y in pa:
            if x == lca: break
            proof.append(f"{x} = {y}    [{ax}]")
            if y == lca: break
        tail = []
        for x, ax, y in pb:
            if x == lca: break
            tail.append(f"{y} = {x}    [{ax}, symmetry]")
            if y == lca: break
        return proof + list(reversed(tail))

d = ProofDSU()
for eq in [("a", "b", "ax1"), ("c", "d", "ax2"), ("b", "d", "ax3"),
           ("e", "f", "ax4"), ("f", "a", "ax5")]:
    d.union(*eq)

print("axioms: a=b [ax1], c=d [ax2], b=d [ax3], e=f [ax4], f=a [ax5]\n")
print("query  explain(e, c)  — extracted equational proof:")
for line in d.explain("e", "c"):
    print("   ", line)
print("    e = c             [transitivity of the above]")
print("\nThe forest stored the proof all along; find() was normalization.")
