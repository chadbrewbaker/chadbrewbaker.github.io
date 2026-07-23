# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
# https://chadbrewbaker.github.io/ — companion to the 2026-07-22 union-find post
# Species formula for union-by-rank reachable trees ("union trees"):
#   Ladder characterization  =>  T_r = X * PROD_{j<r} SET_{>=1}(T_j)
#   Labeled EGF:   T_r(x) = x * prod_{j<r} (e^{T_j(x)} - 1)
#   Unlabeled OGF: t_r(x) = x * prod_{j<r} MSET_{>=1}(t_j)(x)  (Euler transform)
# Exact rational power-series arithmetic on coefficient lists.

from fractions import Fraction as F
from math import factorial

N = 21          # compute [x^1..x^20]; rank r needs >= 2^r nodes => ranks <= 4

def mul(a, b):
    c = [F(0)] * N
    for i, ai in enumerate(a):
        if ai:
            for j in range(N - i):
                if b[j]:
                    c[i + j] += ai * b[j]
    return c

def exp_series(a):                      # a[0] must be 0
    assert a[0] == 0
    out = [F(0)] * N; out[0] = F(1)     # exp via E' = a'E
    ap = [F(k + 1) * a[k + 1] for k in range(N - 1)] + [F(0)]
    for n in range(1, N):
        s = F(0)
        for k in range(n):
            s += ap[k] * out[n - 1 - k]
        out[n] = s / n
    return out

def sub_xk(a, k):                       # a(x^k)
    c = [F(0)] * N
    for i, ai in enumerate(a):
        if ai and i * k < N:
            c[i * k] = ai
    return c

def euler_mset(a):                      # MSET(A) = exp(sum_k A(x^k)/k)
    s = [F(0)] * N
    for k in range(1, N):
        axk = sub_xk(a, k)
        for i in range(N):
            s[i] += axk[i] / k
    return exp_series(s)

X = [F(0)] * N; X[1] = F(1)
ONE = [F(0)] * N; ONE[0] = F(1)
def minus1(a): b = a[:]; b[0] -= 1; return b

RANKS = 5
# labeled
T = [X]
for r in range(1, RANKS):
    p = ONE
    for j in range(r):
        p = mul(p, minus1(exp_series(T[j])))
    T.append(mul(X, p))
tot = [sum(Tr[i] for Tr in T) for i in range(N)]
labeled = [factorial(n) * tot[n] for n in range(1, N)]
assert all(c.denominator == 1 for c in labeled)
print("labeled  :", [int(c) for c in labeled])

# unlabeled
t = [X]
for r in range(1, RANKS):
    p = ONE
    for j in range(r):
        p = mul(p, minus1(euler_mset(t[j])))
    t.append(mul(X, p))
utot = [sum(tr[i] for tr in t) for i in range(N)]
unlabeled = [utot[n] for n in range(1, N)]
assert all(c.denominator == 1 for c in unlabeled)
print("unlabeled:", [int(c) for c in unlabeled])

bf_lab = [1, 2, 3, 28, 125, 786, 5047, 75720]
bf_unl = [1, 1, 1, 2, 3, 5, 7, 12]
assert [int(c) for c in labeled[:8]] == bf_lab, "labeled mismatch!"
assert [int(c) for c in unlabeled[:8]] == bf_unl, "unlabeled mismatch!"
print("MATCH brute force n=1..8  (rank-4 terms start at n=16, included)")
