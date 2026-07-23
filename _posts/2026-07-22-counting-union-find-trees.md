---
layout: post
title: "Counting union-find trees: a species formula, two sequences OEIS doesn't have, and what Tarjan's potential method really is"
date: 2026-07-22
tags: [combinatorics, oeis, union-find, curry-howard, species, z3, sat]
---

This post writes up the results of an extended session with Claude (Anthropic's
Fable 5) walking the Curry–Howard correspondence through the standard
algorithms curriculum: every data structure is a type, every analysis is a
proof, so every analysis *technique* should be an induction scheme with a
complexity of its own. Most of that walk produces reframings. Three places it
produced theorems. The scripts backing everything are in
[`tools/`](https://github.com/chadbrewbaker/chadbrewbaker.github.io/tree/master/tools)
— uv-runnable, PEP 723 inline deps, every number below reproducible.

## 1. Two sequences that appear to be new

Ask what the *state space* of union-by-rank actually is. The recognition
question is settled: with path compression, deciding whether a given tree is a
reachable union-find tree is **NP-complete** (Gelle–Iván 2015–2019, by
reduction from Partition); without compression the literature says a
polynomial characterization exists (Cai, IPL 1993). What nobody seems to have
done is **count** them.

**Lemma (rank determinism).** Every tree reachable by union-by-rank linking
(no compression) determines its own rank, bottom-up: ρ(leaf) = 0,
ρ(v) = max ρ(children) + 1. Different merge histories cannot assign the same
tree different ranks. Machine-checked over *all* merge histories through n = 8
([`uf_bruteforce.py`](/tools/uf_bruteforce.py) asserts it).

**Theorem (ladder characterization).** A rooted tree is reachable iff at every
internal node of rank r, the multiset of children's ranks is contained in
{0, …, r−1} and **contains each value at least once**. Necessity: the root's
rank climbs 0 → r via exactly r equal-rank merges, consuming one child of each
rank 0, …, r−1. Sufficiency: climb the ladder first, attach the extras after.
(The classical "rank r ⇒ ≥ 2^r nodes" lemma falls out of the grammar for
free.)

That characterization *is* a combinatorial-species definition — a rank-r tree
is a root times, for each j < r, a **nonempty set** of rank-j trees:

    𝒯₀ = X        𝒯ᵣ = X · ∏_{j<r} SET≥1(𝒯ⱼ)

so the labeled EGF satisfies **Tᵣ(x) = x·∏_{j<r}(e^{Tⱼ(x)} − 1)** and the
unlabeled OGF is the same product under the Euler/multiset transform. The
system truncates at rank ⌊log₂ n⌋ — the generating-function shadow of the
O(log n) find bound. Exact power-series arithmetic
([`uf_species.py`](/tools/uf_species.py)) and independent brute-force history
enumeration agree on every term where both run.

**Labeled union-find trees on n nodes** (n = 1..20):

    1, 2, 3, 28, 125, 786, 5047, 75720, 991881, 13625830, 184491131,
    2764044636, 44445422749, 771222628554, 14127768312855,
    294099208035856, 6969896869224209, 184385882602060110,
    5191974274480795891, 152831601701911502820

**Unlabeled shapes** (n = 1..20):

    1, 1, 1, 2, 3, 5, 7, 12, 19, 34, 58, 103, 176, 306, 517, 881,
    1480, 2507, 4239, 7261

Neither is in OEIS. The closest hit for the labeled version is
[A098812](https://oeis.org/A098812) — it shares a prefix and then diverges,
which is exactly the kind of near-miss that makes exact term lists worth
publishing. Next steps before an OEIS submission and a short note (JIS /
AofA-adjacent): run Superseeker on both, and read Cai 1993 to attribute the
characterization correctly. One genuinely fun refinement waiting in the
grammar: mark rank with a second variable and the same system yields the
joint (size, rank) distribution — i.e., the analytic-combinatorics route to
average-case union-find, derived rather than analyzed.

The fraction of labeled rooted trees that are union-find-reachable,
aₙ/n^{n−1}, is ≈ 3·10⁻⁵ by n = 20 and falling: almost no tree can be built by
merging. Rank discipline is *restrictive*, which is presumably why it works.

## 2. What Tarjan's potential method is, logically

The potential function in amortized analysis is a **strengthened induction
hypothesis** — the oldest move in proof theory. "Total cost ≤ 3n" is true but
not inductively closed (a resize breaks the local step); Tarjan's fix is to
strengthen the invariant to `cost-so-far + Φ(state) ≤ budget`, which *is*
closed, and Φ is exactly the strengthening. Three consequences, in increasing
order of interest:

**Where it lives.** With a polytime, polynomially-bounded Φ, the whole
argument is length-induction on a PV-formula — it formalizes in Buss's S¹₂,
whose witnessing theorem then *guarantees* the extracted algorithm is
polytime. The degenerate cousin — "the potential strictly decreases, so we
terminate," no rates — is precisely the **PLS** iteration principle
(Buss–Krajíček: the ∀Σᵇ₁ consequences of T¹₂ are PLS).

**An oracle separation of two textbook proof styles.** Rate-certified
extraction is FP; decrease-only certificates capture PLS-complete search; and
local search is exponentially hard in the black-box model. So relative to a
suitable oracle, **no uniform polytime procedure converts "my potential
decreases" into "my potential decreases at a certified exchange rate."** The
telescoping step in Tarjan's method is not syntactic sugar — it is a logical
resource, and the gap between the two amortization styles is exactly the
FP-vs-PLS gap. Assembled entirely from classical parts, but I can't find the
amortization literature ever stating its two standard patterns as
oracle-separated schemes.

**Finding Φ is constraint solving.** Because potentials come from linear
templates, induction-hypothesis discovery collapses to optimization
(Hofmann–Jost's insight, industrialized in AARA).
[`amortized_induction.py`](/tools/amortized_induction.py) does it live with
z3: verifies the dynamic-array step obligation, then *synthesizes*
Φ = 2n − cap + const with the optimal amortized bound k = 3 by CEGIS — it
needs CEGIS rather than one solver call because coefficient-times-state is
nonlinear, a nice miniature of proof search sitting strictly above proof
checking. Bonus track: the binary counter's popcount potential verified over
all 4095 states.

And the finite-state case is *completely solved by transfer*: a potential
function is an energy-game progress measure, optimal amortized cost is Karp's
maximum mean cycle (strongly polynomial, with a primal-dual certificate:
potential above, tight cycle below), and memoryless determinacy of mean-payoff
games gives a quotable corollary — **finite-state self-adjusting structures
always admit history-free optimal implementations**. Verification solved our
problem in the '90s under a different name.

## 3. Watching a lower bound on a stopwatch

Haken (1985): pigeonhole needs exponential resolution proofs. CDCL solvers
are resolution engines, so the theorem predicts solver behavior. KISSAT
4.0.4 on PHP(n+1, n) ([`php_kissat.py`](/tools/php_kissat.py)):

| holes | conflicts | time |
|------:|----------:|-----:|
| 4  | 29      | 0.00s |
| 6  | 704     | 0.01s |
| 8  | 10,737  | 0.10s |
| 10 | 147,461 | 2.27s |

×4–5 per pigeon. One line of mathematics, exponentially long proofs — and
polynomial in Frege, so the cost is a property of the *reasoning system*, not
the theorem. Meanwhile [`dsu_proof_forest.py`](/tools/dsu_proof_forest.py)
shows the flip side of union-find from §1: the parent forest is literally a
proof forest, and `explain(e, c)` extracts the equational proof chain — the
mechanism inside every SMT solver's congruence closure.

## Files

In [`tools/`](https://github.com/chadbrewbaker/chadbrewbaker.github.io/tree/master/tools):
`uf_species.py` (the species formula, exact arithmetic, both sequences),
`uf_bruteforce.py` (independent ground truth + rank-determinism check),
`amortized_induction.py` (z3: verify + CEGIS-synthesize potentials),
`species_dictionary.py` (sympy: derivative = zipper, Set∘Cyc = Perm, Cayley
via Lagrange inversion), `php_kissat.py` (Haken empirically; expects `kissat`
on PATH or `KISSAT` env var), `dsu_proof_forest.py` (proof-producing
union-find, stdlib only). All carry PEP 723 headers: `uv run <script>` and
they fetch their own deps.

The longer working paper with full proofs and a claim-by-claim novelty audit
rides along as
[`tools/three-theorems-working-paper.md`](/tools/three-theorems-working-paper.md).
