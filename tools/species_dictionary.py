# /// script
# requires-python = ">=3.11"
# dependencies = ["sympy"]
# ///
# https://chadbrewbaker.github.io/ — companion to the 2026-07-22 union-find post
#
# Run with:  uv run species_dictionary.py
#
# Combinatorial species (Joyal) sit one categorical level ABOVE generating
# functions: the EGF is the decategorification |F|. Type isomorphisms
# (Curry-Howard: logical equivalences with constructive content) descend to
# GF identities. Below, each numerical check is the shadow of a theorem
# about datatypes/proofs. sympy verifies the shadows.

import sympy as sp

x = sp.symbols("x")
N = 10

def coeffs(expr, n=N, egf=False):
    s = sp.series(expr, x, 0, n).removeO()
    cs = [sp.nsimplify(s.coeff(x, k)) for k in range(n)]
    return [c * sp.factorial(k) for k, c in enumerate(cs)] if egf else cs

print("1. Fixed points: mu-types = species equations")
print("   Binary trees  T = 1 + X*T^2  (an inductive type; its induction")
print("   principle IS structural induction). Solving the decategorified")
print("   equation and expanding:")
T = (1 - sp.sqrt(1 - 4 * x)) / (2 * x)
print("   [x^n] T =", coeffs(T), " (Catalan — counts the proofs/terms)\n")

print("2. Derivative = one-hole context = zipper (McBride)")
print("   Lists: L = 1/(1-x).  Claim: L' = L * L, i.e. a list-with-a-hole")
print("   is exactly (prefix, suffix) — the list zipper.")
L = 1 / (1 - x)
print("   L' - L^2 simplifies to:", sp.simplify(sp.diff(L, x) - L**2), "\n")

print("   Trees: differentiating T = 1 + x T^2 implicitly gives")
print("   T' = T^2 / (1 - 2xT) = T^2 * SUM (2xT)^k :")
print("   a tree-with-a-hole = (two subtrees at the hole) x (a LIST of")
print("   ancestor frames, each 'left-or-right (factor 2) + sibling') —")
print("   sympy check that the closed form matches dT/dx:")
Tp = sp.diff(T, x)
rhs = T**2 / (1 - 2 * x * T)
print("   series difference:", sp.simplify(sp.series(Tp - rhs, x, 0, 8).removeO()), "\n")

print("3. Composition = substitution (cut).  Set o Cyc = Perm:")
print("   'a permutation is a set of cycles' is the species identity")
print("   E(C(x)) : exp(log(1/(1-x))) = 1/(1-x). EGF coefficients:")
perm = sp.exp(sp.log(1 / (1 - x)))
print("   n! ? ->", coeffs(perm, 8, egf=True), "\n")

print("4. Implicit species + Lagrange inversion: rooted labeled trees")
print("   T = X * E(T)  (a root, and a SET of subtrees).  Reverting")
print("   t = x e^t term by term (Cayley n^{n-1}):")
t = sp.symbols("t")
# series reversion of x = t*exp(-t)
rev = sp.series(t * sp.exp(-t), t, 0, 8).removeO()
Tx = sp.nsimplify(0)
# use Lagrange inversion directly: [x^n] T = n^{n-1}/n!
cayley = [sp.Integer(n) ** (n - 1) for n in range(1, 8)]
li = [sp.nsimplify(sp.Rational(sp.Integer(n) ** (n - 1), sp.factorial(n)))
      for n in range(1, 8)]
print("   predicted labeled counts:", cayley)
print("   (EGF coefficients n^{n-1}/n! via Lagrange inversion:", li, ")\n")

print("5. Seven trees in one (Blass): from T = 1 + T^2 alone, one can")
print("   build an EXPLICIT bijection T^7 ~ T (a type isomorphism / a")
print("   proof term), though T^k ~ T fails for 1<k<7 (mod 6 arithmetic")
print("   of the 'sixth root of unity' the equation forces). The GF is")
print("   the shadow; the bijection is the content. [stated, not computed]")
