# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
# https://chadbrewbaker.github.io/ — companion to the 2026-07-22 union-find post
# Brute-force ground truth: enumerate all trees on [n] reachable by
# union-by-rank linking (NO path compression), via "last merge" recursion:
# a tree on S is reachable iff it is the rank-lawful merge of reachable
# trees on some partition (S1, S2). Also asserts the rank-uniqueness lemma.

from functools import lru_cache
from itertools import combinations

def attach(tree, child):
    lab, ch = tree
    return (lab, tuple(sorted(ch + (child,))))

@lru_cache(maxsize=None)
def reach(S):                       # S: frozenset -> frozenset of (tree, rank)
    S = frozenset(S)
    if len(S) == 1:
        (x,) = S
        return frozenset({((x, ()), 0)})
    out = set()
    elems = sorted(S)
    fixed = elems[0]                # avoid double-counting unordered splits
    rest = elems[1:]
    for k in range(0, len(rest)):
        for comb in combinations(rest, k):
            S1 = frozenset({fixed} | set(comb))
            S2 = frozenset(S - S1)
            if not S2:
                continue
            for (t1, r1) in reach(S1):
                for (t2, r2) in reach(S2):
                    if r1 < r2:
                        out.add((attach(t2, t1), r2))
                    elif r2 < r1:
                        out.add((attach(t1, t2), r1))
                    else:
                        out.add((attach(t1, t2), r1 + 1))
                        out.add((attach(t2, t1), r1 + 1))
    return frozenset(out)

def shape(tree):
    _, ch = tree
    return ("*", tuple(sorted(shape(c) for c in ch)))

MAXN = 8
lab, unlab = [], []
for n in range(1, MAXN + 1):
    R = reach(frozenset(range(n)))
    trees = {}
    for (t, r) in R:
        assert trees.setdefault(t, r) == r, "rank NOT shape-determined!"
    lab.append(len(trees))
    unlab.append(len({shape(t) for t in trees}))
    print(f"n={n:2d}  labeled={len(trees):8d}  unlabeled={unlab[-1]:5d}")
print("\nrank-uniqueness lemma held for every reachable tree up to n =", MAXN)
print("labeled  :", lab)
print("unlabeled:", unlab)
