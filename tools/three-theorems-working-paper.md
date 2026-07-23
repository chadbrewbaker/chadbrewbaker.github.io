# Three Theorems from the Curry–Howard Reading of Amortized Analysis
### A working paper: proofs, computations, and an honest novelty audit

**Status of this document.** Everything below is proved in full or explicitly
flagged as sketch/transfer/conjecture. Computational claims are reproduced by
the companion scripts (`uf_bruteforce.py`, `uf_species.py`,
`amortized_induction.py`) in this directory. The novelty audit at the end says,
per claim, what I could and could not verify about prior art from here.

---

## Part I — Amortized analysis as an induction scheme: a calibration theorem and an oracle separation

### Setup

Work over Cook's equational theory **PV** (function symbols for exactly the
polytime functions). An **amortized system** is a tuple
𝒜 = (init, step, cost, Φ, INV, k, c₀) of PV-symbols:
states are strings; `step(s, op)` the transition; `cost(s, op) ∈ ℕ` the true
cost; `Φ : states → ℕ` the potential; `INV` a PV-predicate (the structural
invariant); `k(op)` the amortized budget; `c₀` the initial credit. For an
operation sequence σ = op₁…op_m define s₀ = init, s_i = step(s_{i−1}, op_i),
and TC(σ) = Σ cost(s_{i−1}, op_i). Note TC is PV-definable (iterating a PV
function |σ| times, with all intermediate values polynomially bounded in |σ|
plus the state-size bound supplied by INV, is polytime).

Two schemes, distinguished by whether rates are certified:

**(Φ-IND, rate-certified).** From PV-proofs of
  (i) INV(init) ∧ Φ(init) ≤ c₀,
  (ii) ∀s,op [ INV(s) → INV(step(s,op)) ∧
       cost(s,op) + Φ(step(s,op)) ≤ Φ(s) + k(op) ],
conclude ∀σ: TC(σ) ≤ c₀ + Σ_i k(op_i).
(Nonnegativity of Φ is built into the codomain ℕ.)

**(Φ-DEC, decrease-only).** From PV-proofs of
  (i) INV(init), and
  (ii') ∀s,op [ INV(s) ∧ ¬Halt(s) → INV(step(s,op)) ∧ Φ(step(s,op)) < Φ(s) ],
conclude ∀ deterministic runs reach a Halt state (equivalently: the search
problem "find a halting/locally-final state" is total).

### Theorem A1 (Φ-IND is a derived rule of S¹₂; extraction is FP)

**Claim.** If PV proves (i) and (ii), then S¹₂ proves the conclusion of Φ-IND;
moreover the conclusion is ∀Πᵇ₁ with PV matrix, so no search is hidden in it,
and the *executable content* (running the m operations while maintaining the
credit certificate) is a polytime function of (σ, size bound).

**Proof.** Define the PV-predicate
  A(i) :≡ INV(s_i) ∧ TC(σ↾i) + Φ(s_i) ≤ c₀ + Σ_{j≤i} k(op_j),
with the finite data (σ, i) coded as usual; A is PV since s_i, TC(σ↾i), and
the sums are PV-computable from (σ, i). A(0) is (i). A(i) → A(i+1): from
INV(s_i) and (ii) instantiated at (s_i, op_{i+1}),
  TC(σ↾i+1) + Φ(s_{i+1})
    = TC(σ↾i) + cost(s_i, op_{i+1}) + Φ(s_{i+1})
    ≤ TC(σ↾i) + Φ(s_i) + k(op_{i+1})            [by (ii)]
    ≤ c₀ + Σ_{j≤i+1} k(op_j)                     [by A(i)],
and INV(s_{i+1}) by (ii). Now induct on i up to m = "the number of blocks of
σ" — since i ranges over positions *in* the input, this is induction up to a
length, i.e. **LIND for a PV-formula**, which S¹₂ proves (indeed this fragment
is ∀Σᵇ₁-conservative over PV, so nothing beyond PV's strength is consumed).
A(m) plus Φ ≥ 0 gives TC(σ) ≤ c₀ + Σ k(op_i). ∎

The proof *is* the algorithm: it threads the pair (state, credit ledger)
through the run — the Σ-type reading advertised in the atlas, now literal.

### Theorem A2 (Φ-DEC is the iteration principle; its strength is PLS)

**Claim.** The search problems whose totality is provable by Φ-DEC with PV
data are, up to polytime reduction, exactly **PLS**. Consequently
PV + Φ-DEC-rule proves the same ∀Σᵇ₁ statements as T¹₂ does.

**Proof (mapping; the theory-level statement is Buss–Krajíček 1994).**
A Φ-DEC certificate (state space with PV neighbor function, PV potential
strictly decreasing until Halt) *is* a PLS instance: solutions = local minima
of Φ under the neighborhood {s, step(s,·)}; strict decrease until Halt makes
Halt-states exactly the local minima. Conversely any PLS instance (N, Φ)
yields a Φ-DEC system: step = "move to the improving neighbor N(s) if
Φ(N(s)) < Φ(s), else Halt." Totality of PLS is precisely what the iteration
principle asserts, and Buss–Krajíček identifies the ∀Σᵇ₁ consequences of T¹₂
with PLS. ∎

### Theorem A3 (Oracle separation of the two styles of amortized analysis)

**Claim.** There is an oracle A such that no polytime oracle procedure
converts Φ-DEC certificates into executed guarantees: relative to A, the
class of search problems solvable given only a decrease-only certificate
strictly contains those solvable with rate-certified extraction. Informally:
**the telescoping step of Tarjan's method is not syntactic sugar — removing
the rate certificate provably (relative to an oracle) loses extraction
power, unless FP = PLS.**

**Proof.** Rate-certified systems extract in FP (Theorem A1: the extracted
runtime is Σ k(op_i) + overhead, polynomial by hypothesis). Decrease-only
systems capture PLS-complete search (Theorem A2: e.g. encode LocalMaxCut's
standard PLS structure as (step, Φ)). It is known that FP^A ⊊ PLS^A for a
generic/suitably constructed oracle A (query-complexity separation of local
search from function computation — local search on the hypercube requires
exponentially many queries in the black-box model, Aldous 1983 /
Llewellyn–Tovey–Trick, and the standard translation turns the query bound
into an oracle separation). Relative to such A: some Φ-DEC-certified problem
has no polytime solver, while every Φ-IND-certified bound executes in
polytime. Since a uniform relativizing converter Φ-DEC ⇒ Φ-IND (with
polynomial rates) would put PLS^A inside FP^A, no such converter exists. ∎

**Remarks on what A3 does and does not say.** It does not say individual
famous analyses can't be upgraded (splay trees *have* rate certificates).
It says the *rule-to-rule* transformation is impossible in general by
relativizing means: "my potential decreases" and "my potential decreases at
a certified exchange rate against cost" are different logical resources, and
the gap between them is exactly the FP-vs-PLS gap. To my knowledge the
amortized-analysis literature has never stated its two standard proof
patterns as two schemes separated by an oracle; the ingredients, however,
are all classical (hence the audit below classifies A3 as
*new-as-a-statement, assembled from known parts*).

### The 2×2 calibration table this yields

|  | Φ polytime-computable | Φ only Σᵇ₁-certified (e.g. min-cost-to-go) |
|---|---|---|
| **rate-certified (telescoping)** | FP  (Thm A1; S¹₂/PV) | conjectured: CLS-flavored; open |
| **decrease-only** | PLS  (Thm A2; T¹₂) | higher T^i₂ analogues; open |

The two open cells are, I believe, genuinely uninvestigated, and the
bottom-right one connects to the Göös–Hollender–Robere program (which proof
system captures the resulting TFNP class?).

---

## Part II — The energy-game transfer (dictionary + two imported theorems)

**Definitions.** One-player reading: a data structure behavior is a weighted
transition graph; "amortized cost ≤ k with setup c₀" means every path π from
init has cost(π) ≤ k|π| + c₀.

**Proposition B1 (completeness + canonical potential; classical/folklore).**
The bound holds iff a potential Φ ≥ 0 exists with Φ(init) ≤ c₀ and
cost(s→s′) + Φ(s′) − Φ(s) ≤ k on reachable states; moreover
Φ*(s) := sup_π { cost(π) − k|π| : π finite, from s } is the pointwise-least
valid potential. *Proof.* (⇐) telescoping. (⇒) Φ*(s) ≥ 0 (empty path);
Φ*(init) ≤ c₀ (hypothesis); the one-step optimality (Bellman) inequality
gives the step condition; minimality: any valid Φ satisfies, by telescoping
along π from s, Φ(s) ≥ cost(π) − k|π|, so Φ ≥ Φ*. ∎

**Theorem B2 (finite-state automatic amortized analysis, imported).** For a
finite behavior graph, the optimal amortized constant k* equals the maximum
mean-weight cycle (Karp 1978), computable in O(VE); and for k ≥ k*, minimal
potentials are shortest-path distances under reduced costs. Hence *automatic,
complete* amortized analysis of finite-state abstractions is strongly
polynomial, with a primal-dual certificate pair: (potential Φ) certifying the
upper bound and (a cycle of mean k*) certifying tightness.
*Proof.* π has cost ≤ k|π| + c₀ for all π and some c₀ iff every cycle has
mean ≤ k (decompose long paths into cycles plus a short remainder; conversely
pump a heavy cycle). Karp computes max mean; Bellman–Ford on weights
cost − k* yields the potentials (no positive cycles remain). ∎

**Theorem B3 (adversarial amortization, imported).** If an adversary picks
operations and the implementation picks internal resolutions, optimal
amortized cost is the value of a mean-payoff game: decidable in NP ∩ coNP
(Zwick–Paterson), pseudo-polynomial by value iteration (Brim et al.), and —
by memoryless determinacy (Ehrenfeucht–Mycielski) — **an optimal
implementation strategy exists that is history-free**. For finite-state
abstractions of self-adjusting structures: no history needs to be consulted
to be worst-case-sequence optimal. *Proof: direct instantiation.* ∎

The transfer's value is directional: verification's machinery (progress
measures, value iteration, strategy improvement) becomes a *complete*
algorithmic toolbox for a task (amortized analysis) that the algorithms
community does by hand, per-structure; and B1's minimal Φ* explains *why*
textbook potentials look the way they do (they are Bellman values). The
CEGIS synthesis in `amortized_induction.py` is the infinite-state version of
this pipeline with templates replacing state enumeration.

---

## Part III — Enumeration of union-by-rank trees (the new theorem)

**Model.** Union-by-rank linking, **no path compression** ("Union trees" in
the recognition literature: Cai 1993; Gelle–Iván 2015/2017/2019 prove that
*with* path compression recognition becomes NP-complete, and cite the
non-compressed case as the polynomially-characterizable one). Reachable
objects: rooted trees on a labeled vertex set produced by some sequence of
rank-lawful root links (ties broken either way).

### Lemma C1 (rank determinism)

Every reachable tree T determines its rank: ρ(T) is computable bottom-up as
ρ(leaf) = 0 and ρ(v) = max_{c child of v} ρ(c) + 1.

**Proof.** By induction on |T|. A merge history of T ends with root v having
absorbed children c₁,…,c_t (in some order), each c_i a reachable tree with —
by induction — a determined rank ρ(c_i). The root's rank starts at 0 and
increments exactly when it absorbs a child of *equal* current rank; absorbing
lower rank leaves it unchanged. If the final rank is r, then increments
occurred at ranks 0,1,…,r−1, each consuming a child of exactly that rank, and
all other children were absorbed at rank strictly above their own. Hence
max_i ρ(c_i) = r − 1 (a child of rank r−1 exists — the last increment — and
none of rank ≥ r can ever be absorbed: absorbing rank q requires current
rank ≥ q, and at rank q an equal merge would increment past q, so a rank-q
child forces final rank ≥ q+1). So r = max ρ(c_i) + 1, determined by the
children's shapes alone. ∎

(Machine check: `uf_bruteforce.py` asserts, for every reachable tree up to
n = 8, that all merge histories assign it the same rank. It held.)

### Theorem C2 (ladder characterization)

A rooted tree T is reachable by union-by-rank iff for every internal node v
with children ranks (per Lemma C1) ρ₁,…,ρ_t and r := max ρ_i + 1:
**{0, 1, …, r−1} ⊆ {ρ₁,…,ρ_t}** — the children's ranks form a multiset over
{0,…,r−1} containing each value at least once.

**Proof.** *Necessity:* by the increment analysis in C1, the history supplies
one child of each rank 0,…,r−1 (the increments), and every child has rank
≤ r−1. *Sufficiency:* build each child subtree first (valid by induction on
size), then schedule: absorb one child of rank 0 (rank→1), one of rank 1
(rank→2), …, one of rank r−1 (rank→r); every remaining child has rank
q ≤ r−1 < r and is absorbed afterward, lawfully, in any order. ∎

*Relation to prior art:* an equivalent characterization is presumably Cai
(IPL 1993) — the recognition papers state one exists; I could not access
Cai's statement from here to confirm identity of form. The lemma-plus-
characterization above is self-contained regardless. What follows is the
part I could find no trace of anywhere: **counting them.**

### Theorem C3 (species system and generating functions)

Let 𝒯_r be the species of reachable trees of rank r. Then
  **𝒯₀ = X,  𝒯_r = X · ∏_{j=0}^{r−1} SET_{≥1}(𝒯_j)**,
whence the labeled EGF and unlabeled OGF satisfy
  T_r(x) = x·∏_{j<r}(e^{T_j(x)} − 1),
  t_r(x) = x·∏_{j<r}( exp(Σ_{m≥1} t_j(x^m)/m) − 1 )   (Euler/MSET),
and the counting sequences are T(x) = Σ_r T_r, t(x) = Σ_r t_r. (The sum is
locally finite: rank-r trees have ≥ 2^r vertices — the classical union-find
lemma, here re-proved by the grammar: |𝒯_r| ≥ 1 + Σ_{j<r} min|𝒯_j| gives
min|𝒯_r| = 2^r by induction.)

**Proof.** Immediate from C1 + C2: a rank-r tree is a root (X) together with,
for each j < r, a nonempty *set* of rank-j child subtrees (nonempty = the
ladder; set = children are unordered and label-disjoint — species product
splits labels, which is exactly the multiplicative conjunction the atlas
promised would do real work). Rank determinism (C1) makes the ranks
well-defined so the decomposition is a bijection, and guarantees Σ_r counts
each tree once. ∎

### Corollary C4 (the numbers)

Labeled (n = 1…20), from the EGF, independently confirmed by brute-force
history enumeration for n ≤ 8:

  1, 2, 3, 28, 125, 786, 5047, 75720, 991881, 13625830, 184491131,
  2764044636, 44445422749, 771222628554, 14127768312855, 294099208035856,
  6969896869224209, 184385882602060110, 5191974274480795891,
  152831601701911502820

Unlabeled shapes (n = 1…20), same double verification:

  1, 1, 1, 2, 3, 5, 7, 12, 19, 34, 58, 103, 176, 306, 517, 881, 1480,
  2507, 4239, 7261

Observations worth developing for a paper version: (a) the labeled fraction
among all rooted labeled trees, a_n/n^{n−1}, decays (≈ 3·10⁻⁵ at n = 20) —
conjecture: → 0 superpolynomially, provable by singularity comparison of
T(x) (entire, as an iterated finite product/composition of entire functions)
against x·e^{T} growth; (b) rank ≤ ⌊log₂ n⌋ falls out of the grammar, so the
system truncates at log-many equations — the generating-function shadow of
the O(log n) find-bound; (c) the same grammar with SET replaced by weighted
sets counts trees by (size, rank, #children) jointly, giving access to the
*distribution of ranks under random unions* — which is the analytic-
combinatorics route to average-case union-find statements.

**Novelty status.** Neither sequence, as of the searches run for this
document, appears in OEIS-indexed pages or anywhere else I could find; the
recognition literature (which is exactly where such an enumeration would be
cited) does not count. Caveats: I could not query OEIS's own search endpoint
or Superseeker from this environment — that is the mandatory next step
before claiming novelty in print; and Cai 1993 must be read to attribute C2
properly. Conditional on those checks, Theorem C3 + C4 is a publishable
short paper (JIS / Séminaire Lotharingien style, or an addendum-note to the
Gelle–Iván line), and observation (c) upgrades it toward analysis-of-
algorithms venues (AofA).

---

## Part IV — Other techniques from the atlas: two further publishable seams

**IV.1 The verification-asymmetry criterion for the probabilistic method.**
Formalize: an *abundance proof* for a property P is a witness that
Pr_x[P(x)] ≥ 1/poly. Claim (easy direction, provable): if additionally P ∈ P
(polytime-verifiable), abundance yields a ZPP witness-finder. Claim (the
interesting direction, provable by standard diagonalization over oracles):
there is an oracle world with an abundant P, decidable with the oracle,
where every polytime finder fails — abundance *without verification* has no
extraction. The pair turns last turn's observation ("Ramsey resists because
Ramsey-ness isn't checkable") into a theorem-shaped criterion; the follow-up
question with real content is a *fine-grained* version: relate the
verification complexity of P to the extraction complexity, interpolating
between Moser–Tardos (local verifiability) and extractor theory (global).

**IV.2 The missing third leg.** Göös–Hollender–Robere et al. now match TFNP
classes to proof systems (PLS↔resolution, PPA↔𝔽₂-Nullstellensatz, …); the
Kohlenbach school extracts bounds from analysis proofs; nobody has computed
*which TFNP class the standard nonconstructive lemmas of analysis land in*
after monotone functional interpretation. A concrete first target:
Caristi's fixed-point theorem / Ekeland's variational principle — whose
proof is literally a Φ-DEC argument on a continuous state space — should be
the analysis-side twin of PLS, and I would conjecture its finitary miniature
is PLS-complete. That single worked example would be a genuinely new bridge
paper between three communities.

---

## Novelty audit (what I actually believe, claim by claim)

| Claim | Status |
|---|---|
| A1 (Φ-IND derived in S¹₂, FP extraction) | Correct; formalization-level novelty only — the *statement* "Tarjan's method = PV/S¹₂ LIND with Σ-type invariant" appears unpublished as such (nearest neighbors: AARA soundness proofs; Grodin–Harper's coalgebraic potentials, which do the categorical but not the proof-theoretic side) |
| A2 (Φ-DEC ≡ PLS) | Known in substance (Buss–Krajíček); the amortization framing is new packaging |
| A3 (oracle separation of the two amortization styles) | New as a statement, assembled entirely from classical parts (query lower bounds for local search + relativization); needs a referee-proof write-up of the translation, no new mathematics |
| B1 | Folklore (completeness of potential method) |
| B2, B3 | Correct transfers of Karp / mean-payoff results; novelty is the systematization; B3's "history-free optimal implementations for finite abstractions" corollary is the most quotable transferred sentence |
| C1, C2 | Proved here; C2 likely coincides with Cai 1993 (unverified from this environment) |
| **C3, C4** | **Proved and machine-verified here; no trace found in OEIS-indexed material or the literature; the strongest candidate for "new and publishable" in this document, pending an OEIS Superseeker check and a reading of Cai 1993** |
| IV.1, IV.2 | Research proposals with the easy halves provable on demand |
