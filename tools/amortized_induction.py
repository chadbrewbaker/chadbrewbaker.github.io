# /// script
# requires-python = ">=3.11"
# dependencies = ["z3-solver"]
# ///
# https://chadbrewbaker.github.io/ — companion to the 2026-07-22 union-find post
#
# Run with:  uv run amortized_induction.py
#
# CLAIM (Curry-Howard reading of Tarjan's potential method):
#   A potential function is a STRENGTHENED INDUCTION HYPOTHESIS.
#
#   The naive statement "total cost of n operations <= 3n" is not inductive:
#   a single operation can cost n+1 (a resize), so P(k) does not imply P(k+1)
#   locally. Tarjan's fix is the classic proof-theoretic move: strengthen the
#   invariant to  P*(state, C) :=  C + Phi(state) <= 3 * (ops so far)
#   which IS closed under every step. Phi is exactly the strengthening.
#
#   Part 1 below CHECKS the induction step for the known Phi (what a human
#   does on paper; here z3 plays proof checker over the step relation).
#   Part 2 SYNTHESIZES Phi from a linear template — the Hofmann-Jost /
#   AARA observation that because potentials are drawn from a linear family,
#   *finding the induction hypothesis is constraint solving*, not eureka.

from z3 import (Int, Ints, Solver, Optimize, ForAll, Implies, And, Or,
                unsat, sat)

# ----- the transition system: dynamic array with doubling ------------------
# state = (n, cap), 0 <= n <= cap, invariant cap <= 2n+1 (holds from (0,1))
# append: if n < cap: cost 1,   (n,cap) -> (n+1, cap)
#         if n = cap: cost n+1, (n,cap) -> (n+1, 2*cap)   (copy n, insert 1)

n, cap = Ints("n cap")
INV = And(n >= 0, cap >= 1, n <= cap, cap <= 2 * n + 1)

def phi(a, b, c):           # linear potential template  Phi = a*n + b*cap + c
    return lambda N, CAP: a * N + b * CAP + c

def step_obligations(P, k):
    """The two branches of the induction step + Phi >= 0 (needed so the
    telescoped sum lower-bounds true cost)."""
    no_resize = Implies(And(INV, n < cap),
                        1 + P(n + 1, cap) - P(n, cap) <= k)
    resize    = Implies(And(INV, n == cap),
                        (n + 1) + P(n + 1, 2 * cap) - P(n, cap) <= k)
    nonneg    = Implies(INV, P(n, cap) >= 0)
    return [no_resize, resize, nonneg]

# ----- Part 1: CHECK the induction step for the textbook potential ---------
print("Part 1: checking the induction step for Phi = 2n - cap + 1, bound 3")
P = phi(2, -1, 1)
s = Solver()
# validity of ForAll <=> unsat of the negation
s.add(Or(*[Implies(True, ob) == False for ob in []]))  # (no-op, clarity)
s.add(Or(*[ob == False for ob in step_obligations(P, 3)]))
verdict = s.check()
print("  negation of step obligations:", verdict,
      "=> induction step", "VERIFIED" if verdict == unsat else "FAILS", "\n")

# ----- Part 2: SYNTHESIZE the strengthening ---------------------------------
print("Part 2: synthesizing (Phi, amortized bound k) by constraint solving")
# Symbolic coefficients times state variables = nonlinear arithmetic, which
# z3 won't decide under quantifiers. So we do what AARA/LP actually does:
# CEGIS. Guess coefficients grounded on finitely many states (linear!),
# verify the guess with coefficients FIXED (linear again!), feed back
# counterexample states. Induction-hypothesis search as a guess-check loop.
a, b, c = Ints("a b c")

def verify(av, bv, cv, k_val):
    """Coefficients fixed -> obligations are linear; check validity."""
    P = phi(av, bv, cv)
    s2 = Solver()
    s2.add(Or(*[ob == False for ob in step_obligations(P, k_val)]))
    if s2.check() == unsat:
        return None
    md = s2.model()
    return (md[n].as_long(), md[cap].as_long())          # counterexample

found = None
for k_val in range(0, 8):                                # smallest feasible k
    samples = [(0, 1), (1, 1), (1, 2), (3, 4)]
    for _ in range(40):                                  # CEGIS iterations
        guess = Solver()
        guess.add(a >= -4, a <= 4, b >= -4, b <= 4, c >= 0, c <= 4)
        for (nv, cv_) in samples:                        # grounded obligations
            P = phi(a, b, c)
            if nv < cv_:
                guess.add(1 + P(nv + 1, cv_) - P(nv, cv_) <= k_val)
            if nv == cv_:
                guess.add((nv + 1) + P(nv + 1, 2 * cv_) - P(nv, cv_) <= k_val)
            guess.add(P(nv, cv_) >= 0)
        if guess.check() != sat:
            break                                        # no Phi at this k
        gm = guess.model()
        av, bv, cv = gm[a].as_long(), gm[b].as_long(), gm[c].as_long()
        cex = verify(av, bv, cv, k_val)
        if cex is None:
            found = (av, bv, cv, k_val)
            break
        samples.append(cex)                              # learn from failure
    if found:
        break
av, bv, cv, k_min = found
print(f"  CEGIS found  Phi = {av}*n + ({bv})*cap + {cv},  amortized cost k = {k_min}")
print("  i.e. the solver rediscovered the induction hypothesis a human")
print("  'guesses' — hypothesis search collapsed to optimization.\n")

# ----- Part 3: same story, bit-level: the binary counter --------------------
# increment cost = (trailing ones) + 1;  Phi = popcount. Claim: amortized <= 2.
# Here the invariant is Sigma^b_1-ish over bitvectors: a bounded, feasible
# strengthening — the kind of induction S^1_2 witnesses in polytime.
from z3 import BitVec, BitVecVal, Extract, If, Sum, Not, BV2Int

W = 12
x = BitVec("x", W)
bit = lambda v, i: BV2Int(Extract(i, i, v))
popcount = lambda v: Sum([bit(v, i) for i in range(W)])

# trailing ones of x = position of lowest zero
tr = Int("tr")
lowest_zero = []
acc = None
cost = Int("cost")
# cost = 1 + (# of trailing ones): flip them to 0, set the next bit to 1
trailing = Sum([If(And(*[Extract(j, j, x) == 1 for j in range(i + 1)]), 1, 0)
                for i in range(W)])
s = Solver()
s.add(x != BitVecVal(2**W - 1, W))                  # exclude overflow
claim = (trailing + 1) + popcount(x + 1) - popcount(x) <= 2
s.add(Not(claim))
verdict = s.check()
print("Part 3: binary counter, Phi = popcount, all", 2**W - 1, "states:")
print("  negation:", verdict, "=> amortized increment <= 2",
      "VERIFIED" if verdict == unsat else "FAILS")
