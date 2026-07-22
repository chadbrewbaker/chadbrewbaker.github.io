---
layout: post
title: "Sequence Triple: recurrence ⇄ generating function ⇄ closed form, in one HTML file"
date: 2026-07-21
---

I've been mining OEIS for missing closed forms — factoring the terms of a few
thousand entries that record only a recurrence or a generating function, and
mechanically filling in the form they're missing. A side product of that
session is a small self-contained web tool, in the spirit of
[simonw/tools](https://github.com/simonw/tools): one HTML file, no
dependencies, exact arithmetic.

**[→ Sequence Triple](/tools/sequence-triple.html)**

Enter any one of a constant-coefficient recurrence, a rational generating
function, or a closed form, and the other two are derived exactly — BigInt
rationals throughout, no floating point except to display the roots of
irreducible characteristic polynomials. A verification strip at the bottom
recomputes the first terms *independently* from each representation and checks
they agree; nothing renders unverified.

A few things it does that I haven't seen in one place:

* **Exact Binet forms.** A quadratic characteristic factor is solved in
  ℚ(√D), so Fibonacci comes out as √5/5·φⁿ − √5/5·ψⁿ with exact surds, and the
  verification strip evaluates the surd expression exactly (checking the √D
  component cancels term by term).
* **Quasi-polynomials.** Characteristic factors dividing zᵐ − 1 trigger a
  residue-class split, printing per-class formulas like
  `n ≡ 0 (mod 3): a(n) = 10n/3 + 1`. This turned out to be the dominant
  missing-form class in the OEIS mining run — coordination sequences of
  tilings and zeolite nets, mostly.
* **Honest refusal.** An irreducible cubic or worse gets numeric roots and the
  general Binet shape, clearly marked approximate, rather than a fake formula.
* **Poly-Bernoulli rows.** Pick k and it generates the closed form of
  B_n^(−k) from the surjection sum in my
  [lonesum matrix paper](https://www.emis.de/journals/INTEGERS/papers/i2/i2.pdf)
  (*INTEGERS* 8 (2008), #A02), then derives the recurrence and g.f. — k = 2
  gives a(n) = 5a(n−1) − 6a(n−2), i.e. 2·3ⁿ − 2ⁿ.
* **The Stirling lens.** The part I like most. For six triangular kernels —
  S(n,m), m!·S(n,m), S(n+1,m+1), m!·S(n+1,m+1), C(n,m), (−1)^(n−m)·C(n,m) —
  the coefficients λ in a(n) = Σₘ λ(m)·K(n,m) are *forced*, uniquely, by exact
  forward substitution. The lens inverts, then asks whether λ is recognizable
  (finitely supported, polynomial, exponential-polynomial, or a hypergeometric
  term). Because the inversion is exact, a recognized λ certifies the sum
  identity on every term with nothing left to check. Run it on 2ⁿ and you get
  2ⁿ = S(n,0) + 2S(n,1) + 2S(n,2); run it on a poly-Bernoulli row and it
  inverts the full array in *both* variables, finds the coefficient matrix is
  diagonal, recognizes the diagonal as (m!)², and prints

  B_n^(−k) = Σₘ (m!)² S(n+1,m+1) S(k+1,m+1)

  — the lonesum product formula, re-derived live from the values alone rather
  than quoted from the paper. Watching a machine reconstruct that identity
  from a 16×16 grid of integers is a small but real pleasure.

The page ends with a "how it works" section tracing the algorithms to their
sources — de Moivre's *Miscellanea Analytica* (1730) for solving linear
recurrences by generating functions, Stirling's *Methodus Differentialis*
(same year!) for the numbers in the lens, Riordan's inverse relations,
Ehrhart quasi-polynomials, the Grosse-Kunstleve–Brunner–Sloane zeolite paper,
Kaneko's polylog definition of poly-Bernoulli numbers, Ryser's 1957
forbidden-pattern theorem behind lonesum matrices, and the
Gosper–Zeilberger–Petkovšek world of *A = B* that marks the tool's deliberate
boundary: everything here is C-finite, and the page says so when a sequence
isn't.

The mining session itself — 268 verified closed-form candidates for entries
currently recording none, plus the transform-inversion machinery behind the
lens — is a story for another post.
